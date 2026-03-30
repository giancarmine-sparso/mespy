from __future__ import annotations

import os
import sys
from pathlib import Path

EXPECTED_EXPORTS = {
    "load_csv",
    "median",
    "weighted_mean",
    "variance",
    "covariance",
    "standard_deviation",
    "histogram",
    "lin_fit",
}


def _filter_repo_paths(repo_root: Path) -> None:
    excluded_subtrees = (
        repo_root / "src",
        repo_root / "tests",
        repo_root / "tools",
    )

    filtered_path = []
    for entry in sys.path:
        if not entry:
            filtered_path.append(entry)
            continue

        try:
            resolved = Path(entry).resolve()
        except OSError:
            filtered_path.append(entry)
            continue

        if resolved == repo_root:
            continue

        if any(
            resolved == excluded_root or excluded_root in resolved.parents
            for excluded_root in excluded_subtrees
        ):
            continue

        filtered_path.append(entry)

    sys.path[:] = filtered_path


def main() -> None:
    repo_root = Path(os.environ["REPO_ROOT"]).resolve()
    _filter_repo_paths(repo_root)

    import mech_lab_tools as mlt

    module_path = Path(mlt.__file__).resolve()
    if module_path == repo_root or repo_root in module_path.parents:
        raise SystemExit(
            f"Smoke test imported editable sources instead of wheel: {module_path}"
        )

    missing_exports = EXPECTED_EXPORTS.difference(mlt.__all__)
    if missing_exports:
        raise SystemExit(f"Missing public exports: {sorted(missing_exports)}")

    if "matplotlib.pyplot" in sys.modules:
        raise SystemExit("Package import eagerly loaded matplotlib.pyplot")

    for symbol in ("load_csv", "weighted_mean", "histogram", "lin_fit"):
        if not callable(getattr(mlt, symbol)):
            raise SystemExit(f"Public symbol is not callable: {symbol}")

    print(f"Smoke imports ok from wheel: {module_path}")


if __name__ == "__main__":
    main()

"""
Smoke test per verificare che `mech_lab_tools` venga importato correttamente
dalla wheel/installazione distribuita e non dai sorgenti locali della repo.

Scopo del file
--------------
Questo script non testa nel dettaglio il comportamento numerico delle funzioni
del pacchetto. Il suo obiettivo è invece controllare la "salute" minima della
distribuzione installata, cioè verificare che il pacchetto pubblicato/buildato
sia realmente importabile, esponga la public API prevista e non introduca
effetti collaterali indesiderati già al momento dell'import.

Perché serve
------------
Quando si lavora con un pacchetto Python è facile, durante i test locali,
importare accidentalmente i file sorgente della repository invece della wheel
appena costruita e installata. In quel caso si potrebbe avere un falso positivo:
i test sembrano passare, ma in realtà non si sta verificando la distribuzione
che un utente installerebbe davvero.

Questo smoke test evita proprio quel problema:
1. rimuove da `sys.path` i percorsi che puntano alla repo locale;
2. importa `mech_lab_tools`;
3. controlla che il modulo importato non provenga dai sorgenti del progetto;
4. verifica che gli export pubblici attesi siano presenti;
5. controlla che l'import del pacchetto resti leggero, senza caricare subito
   moduli pesanti come `matplotlib.pyplot`;
6. verifica che alcuni simboli pubblici fondamentali siano effettivamente
   utilizzabili come funzioni.

Cosa controlla in pratica
-------------------------
- `REPO_ROOT`:
  viene letto dall'ambiente per individuare con precisione la root della repo.

- `_filter_repo_paths(repo_root)`:
  filtra `sys.path` rimuovendo:
    * la root della repo;
    * eventuali path sotto `src/`, `tests/` e `tools/`.
  Questo riduce il rischio che `import mech_lab_tools` risolva il package dai
  file locali anziché dalla versione installata.

- `import mech_lab_tools as mlt`:
  importa il pacchetto che dovrebbe provenire dalla wheel installata
  nell'ambiente di test.

- controllo su `mlt.__file__`:
  il path del modulo importato viene confrontato con `repo_root`.
  Se il modulo risulta provenire dalla repository locale, il test fallisce,
  perché significherebbe che non stiamo testando la distribuzione reale.

- controllo sugli export pubblici:
  il set `EXPECTED_EXPORTS` definisce i simboli che devono far parte della
  public API del pacchetto. Il test confronta questo insieme con `mlt.__all__`
  e fallisce se manca anche solo uno degli export attesi.

- controllo di import "leggero":
  se durante il semplice import del package compare `matplotlib.pyplot` in
  `sys.modules`, il test fallisce. Questo serve a garantire che il package non
  carichi eager dipendenze pesanti quando non necessario, migliorando tempi di
  startup e pulizia architetturale.

- controllo di callability:
  alcuni simboli pubblici chiave (`load_csv`, `weighted_mean`, `histogram`,
  `lin_fit`) vengono recuperati con `getattr(...)` e verificati con `callable(...)`.
  Questo è un controllo minimo per assicurarsi che l'API esposta non contenga
  nomi presenti ma mal definiti.

Perché si chiama "smoke test"
-----------------------------
Uno smoke test è un controllo rapido e superficiale che verifica che le cose
essenziali funzionino. Non prova tutta la logica interna del pacchetto, ma
risponde a una domanda fondamentale:

    "La distribuzione installata è almeno importabile e coerente nella sua API?"

Se questo test fallisce, in genere il problema è strutturale:
- packaging errato;
- export mancanti;
- import sbagliato dalla repo locale;
- side effects indesiderati all'import;
- simboli pubblici non definiti correttamente.

Cosa NON garantisce
-------------------
Questo script non sostituisce i test unitari o di integrazione. Non verifica:
- la correttezza matematica delle funzioni;
- la validità dei risultati numerici;
- il comportamento su input edge case;
- la qualità dei grafici generati;
- la compatibilità completa dell'intero pacchetto.

Garantisce però una cosa molto importante:
la wheel installata espone almeno una versione minima e coerente della public API
attesa, senza dipendere accidentalmente dai sorgenti locali.

Output finale
-------------
Se tutti i controlli passano, lo script stampa un messaggio del tipo:

    Smoke imports ok from wheel: <path_del_modulo>

Questo conferma che il pacchetto è stato importato correttamente dalla wheel
e che i controlli minimi di consistenza sono stati superati.
"""
