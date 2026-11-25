"""Lettura e conversione dei file grezzi del contatore (esadecimale -> decimale).

Formato del file grezzo
-----------------------
Ogni riga è un secondo di acquisizione e la prima riga è il secondo 0.
Ogni evento è codificato come ``t<HEX>v<HEX>``:

- ``t``: istante dell'evento in microsecondi dall'inizio di quel secondo;
- ``v``: ampiezza del segnale.

La riga termina con ``$<N>``, il numero di conteggi dichiarato dal contatore.
Esempio, riga di indice 1: ``t10F01vABtF39A0vAA$2`` -> eventi a 1.069377 s e
1.997792 s.

Precisione
----------
I tempi sono tenuti come interi in microsecondi (``tempi_us``): somme,
differenze e suddivisione in intervalli sono quindi esatte. Il passaggio ai
secondi in virgola mobile avviene solo alla fine, con un'unica divisione
correttamente arrotondata, per cui ``tempi_s`` coincide bit per bit con il
valore che si ottiene rileggendo il file ``_dec.txt``.

Il calcolo ``secondo + int(hex, 16) * 1e-6`` fa invece due arrotondamenti
(``1e-6`` non è rappresentabile esattamente in binario) e dà valori come
``6.2793849999999996``. Inoltre ``t // dt`` in virgola mobile può assegnare un
evento all'intervallo sbagliato: 127.8 s con dt = 0.1 s finisce
nell'intervallo 1277 invece che nel 1278.

Uso
---
>>> acq = leggi_contatore("Data/tufo/misura1_tufo_3min.txt")
>>> acq.tempi_s                          # tempi in secondi (float)
>>> acq.attese_us                        # tempi di attesa esatti in µs
>>> acq.conteggi_per_intervallo(0.5)     # conteggi in intervalli da 0.5 s
>>> acq.scrivi_dec("misura1_tufo_3min_dec.txt")

Da terminale: ``python converti_hex.py file1.txt [file2.txt ...] [-o cartella]``
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

US_PER_S = 1_000_000

_RIGA = re.compile(r"(?P<eventi>(?:t[0-9A-Fa-f]+v[0-9A-Fa-f]+)*)(?:\$(?P<n>\d+))?")
_EVENTO = re.compile(r"t([0-9A-Fa-f]+)v([0-9A-Fa-f]+)")


@dataclass(frozen=True)
class Anomalia:
    """Riga del file grezzo con qualcosa di inatteso."""

    secondo: int  # indice della riga (0-based), cioè il secondo di acquisizione
    descrizione: str
    riga: str

    def __str__(self) -> str:
        return f"riga {self.secondo + 1} (secondo {self.secondo}): {self.descrizione}  [{self.riga}]"


@dataclass(frozen=True, eq=False)
class Acquisizione:
    """Contenuto di un file grezzo del contatore."""

    file: Path
    tempi_us: np.ndarray  # int64, tempo assoluto di ogni evento in µs (esatto)
    ampiezze: np.ndarray  # int64, valore ``v`` di ogni evento
    conteggi_dichiarati: np.ndarray  # int64, ``$N`` di ogni secondo (-1 se assente)
    ultima_riga_troncata: bool  # l'ultima riga non ha ``$N``: secondo incompleto
    anomalie: tuple[Anomalia, ...]

    @property
    def n_eventi(self) -> int:
        return len(self.tempi_us)

    @property
    def n_secondi(self) -> int:
        """Numero di righe del file, inclusa un'eventuale ultima riga troncata."""
        return len(self.conteggi_dichiarati)

    @property
    def durata_s(self) -> int:
        """Secondi completi acquisiti (esclude l'ultima riga se troncata)."""
        return self.n_secondi - int(self.ultima_riga_troncata)

    @property
    def tempi_s(self) -> np.ndarray:
        """Tempi in secondi, correttamente arrotondati al double più vicino."""
        return self.tempi_us / US_PER_S

    @property
    def attese_us(self) -> np.ndarray:
        """Tempi di attesa tra eventi consecutivi, in µs interi (esatti)."""
        return np.diff(self.tempi_us)

    def conteggi_per_intervallo(
        self, dt_s: float, durata_s: float | None = None
    ) -> np.ndarray:
        """Numero di eventi in ciascun intervallo ``[k*dt, (k+1)*dt)``.

        Si considerano solo gli intervalli completi entro ``durata_s`` (default:
        ``self.durata_s``). Il calcolo è fatto su interi, quindi un evento che
        cade esattamente su un bordo va sempre nell'intervallo che inizia lì.
        """
        dt_us = _in_microsecondi(dt_s)
        durata_us = _in_microsecondi(self.durata_s if durata_s is None else durata_s)
        if dt_us <= 0:
            raise ValueError(f"dt deve essere almeno 1 µs, ricevuto {dt_s!r}")
        n_intervalli = durata_us // dt_us
        indici = self.tempi_us[self.tempi_us < n_intervalli * dt_us] // dt_us
        return np.bincount(indici, minlength=n_intervalli)

    def scrivi_dec(self, file_output: str | Path) -> Path:
        """Scrive ``<numero evento>\\t<tempo in s>`` con 6 decimali esatti."""
        file_output = Path(file_output)
        righe = (
            f"{i}\t{t // US_PER_S}.{t % US_PER_S:06d}\n"
            for i, t in enumerate(self.tempi_us.tolist(), start=1)
        )
        file_output.write_text("".join(righe), encoding="utf-8")
        return file_output


def _in_microsecondi(t_s: float) -> int:
    """Secondi -> µs interi. Si arrotonda perché sotto il µs non c'è informazione."""
    return round(t_s * US_PER_S)


def leggi_contatore(file_input: str | Path) -> Acquisizione:
    """Legge un file grezzo del contatore, controllando ogni riga.

    I tempi degli eventi vengono solo dai campi ``t``. Il ``$N`` a fine riga
    è conservato in ``conteggi_dichiarati``: quando non coincide con il numero
    di tempi presenti, la riga finisce in ``anomalie``. Lo stesso vale per
    righe illeggibili, tempi >= 1 s o non crescenti e per l'ultima riga
    troncata.
    """
    path = Path(file_input)
    righe = path.read_text(encoding="utf-8").splitlines()
    while righe and not righe[-1].strip():
        righe.pop()

    tempi_us: list[int] = []
    ampiezze: list[int] = []
    dichiarati: list[int] = []
    anomalie: list[Anomalia] = []
    ultima_troncata = False

    for secondo, riga in enumerate(righe):
        riga = riga.strip()

        def segnala(descrizione: str) -> None:
            anomalie.append(Anomalia(secondo, descrizione, riga))

        m = _RIGA.fullmatch(riga)
        if m is None:
            segnala("formato non riconosciuto, estratti solo gli eventi leggibili")
            testo_eventi, n_txt = riga, None
        else:
            testo_eventi, n_txt = m["eventi"], m["n"]

        eventi = [(int(t, 16), int(v, 16)) for t, v in _EVENTO.findall(testo_eventi)]
        micro = [t for t, _ in eventi]

        if n_txt is None:
            dichiarati.append(-1)
            if secondo == len(righe) - 1:
                ultima_troncata = True
                segnala("ultima riga senza $N: acquisizione interrotta a metà secondo")
            elif m is not None:
                segnala("manca $N")
        else:
            dichiarati.append(int(n_txt))
            if int(n_txt) != len(eventi):
                segnala(f"$N = {n_txt} ma i tempi registrati sono {len(eventi)}")

        if any(t >= US_PER_S for t in micro):
            segnala("tempo >= 1 s: l'evento cade fuori dal suo secondo")
        if any(a >= b for a, b in zip(micro, micro[1:], strict=False)):
            segnala("tempi non strettamente crescenti nella riga")

        for t, v in eventi:
            tempi_us.append(secondo * US_PER_S + t)
            ampiezze.append(v)

    return Acquisizione(
        file=path,
        tempi_us=np.array(tempi_us, dtype=np.int64),
        ampiezze=np.array(ampiezze, dtype=np.int64),
        conteggi_dichiarati=np.array(dichiarati, dtype=np.int64),
        ultima_riga_troncata=ultima_troncata,
        anomalie=tuple(anomalie),
    )


def converti_hex(
    file_input: str | Path, file_output: str | Path | None = None
) -> Acquisizione:
    """Legge il file grezzo e, se ``file_output`` è dato, scrive il ``_dec.txt``."""
    acq = leggi_contatore(file_input)
    if file_output is not None:
        acq.scrivi_dec(file_output)
    return acq


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Converte i file grezzi del contatore in <nome>_dec.txt."
    )
    parser.add_argument("file", nargs="+", type=Path, help="file grezzi (esadecimali)")
    parser.add_argument(
        "-o",
        "--cartella-output",
        type=Path,
        help="cartella in cui scrivere i _dec.txt (default: accanto al file grezzo)",
    )
    args = parser.parse_args(argv)

    for ingresso in args.file:
        cartella = args.cartella_output or ingresso.parent
        cartella.mkdir(parents=True, exist_ok=True)
        uscita = cartella / f"{ingresso.stem}_dec.txt"
        acq = converti_hex(ingresso, uscita)
        print(f"{ingresso} -> {uscita}: {acq.n_eventi} eventi in {acq.durata_s} s")
        for anomalia in acq.anomalie:
            print(f"  ! {anomalia}")


if __name__ == "__main__":
    main()
