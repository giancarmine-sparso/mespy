<!-- The HTML page is rendered by _templates/get-started.html (see conf.py).
     This file supplies the title, the search index and non-HTML builds:
     keep its commands in sync with the template. -->

# Inizia qui

Installa MesPy, verifica che funzioni e scegli da dove continuare. Tutto quello che serve per iniziare, in pochi passi. MesPy richiede Python 3.12 o successivo.

Questa documentazione segue le sorgenti del repository. Gli esempi di `histogram`, in particolare i bordi costruiti con `bin_width` e il controllo della griglia, includono modifiche successive alla versione 2.0.0 pubblicata su PyPI. Per riprodurli esattamente, usa l’installazione dalle sorgenti descritta in [Installazione per lo sviluppo](installazione.md).

## Scegli il tuo ambiente

Su Google Colab o in un notebook Jupyter, esegui in una cella di codice:

```python
%pip install mespy
```

`%pip` installa MesPy nell'ambiente del kernel attivo; se poi l'import non funziona, riavvia il kernel.

Con uv, consigliato per i progetti locali, aggiungi MesPy a un progetto creato con `uv init`:

```bash
uv add mespy
```

Per provarlo senza creare un progetto, apri una sessione Python temporanea:

```bash
uv run --with mespy python
```

Con pip, preferibilmente in un ambiente virtuale:

```bash
python -m pip install mespy
```

## Verifica che tutto funzioni

```python
import mespy

print("MesPy è pronto.")
```

## Continua a esplorare

- [Esempi](examples/index.md): flussi di analisi pratici e notebook.
- [Riferimento API](moduli/index.md): funzioni, parametri e valori restituiti.
- [Installazione per lo sviluppo](installazione.md): per chi vuole contribuire a MesPy.
