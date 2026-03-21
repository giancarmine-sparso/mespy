# Piano finale del progetto — Script per analisi dati di laboratorio

## Obiettivo
Costruire una piccola toolbox in **Python** per analizzare i dati delle esperienze di laboratorio del primo anno, in modo coerente con gli argomenti trattati a lezione.

L’obiettivo non è creare subito una libreria generica per ogni possibile esperimento, ma una base solida e riutilizzabile per:
- elaborazione statistica di misure;
- gestione delle incertezze;
- presentazione corretta dei risultati;
- fit ai minimi quadrati;
- calibrazione e produzione di grafici.

---

## Contenuti del corso su cui basare il progetto
Il progetto sarà costruito attorno ai nuclei effettivamente affrontati a lezione:

### 1. Misure, incertezze, cifre significative
- errori casuali e sistematici;
- precisione e accuratezza;
- cifre significative;
- deviazione standard;
- deviazione standard della media;
- compatibilità tra un valore misurato e un valore atteso;
- strumenti di misura (regolo, calibro, Palmer);
- distribuzione uniforme continua;
- inferenza gaussiana su singola misura e misure ripetute.

### 2. Adattamento di curve ai dati sperimentali
- metodo dei minimi quadrati;
- fit lineare;
- rette di calibrazione;
- estrapolazione;
- stima delle incertezze sui parametri;
- caso delle medie pesate;
- analisi dei residui.

---

## Filosofia del progetto
Il progetto deve rispettare cinque principi:

1. **Modularità** — ogni file deve svolgere un compito chiaro.
2. **Riutilizzabilità** — le stesse funzioni devono poter servire in più esperienze.
3. **Trasparenza** — i passaggi matematici devono essere leggibili e verificabili.
4. **Riproducibilità** — gli stessi dati devono produrre sempre gli stessi risultati.
5. **Crescita graduale** — prima strumenti essenziali, poi raffinamenti.

---

## Struttura consigliata del repository

```text
lab-scripts/
├─ README.md
├─ requirements.txt
├─ data/
│  ├─ raw/
│  └─ processed/
├─ notebooks/
├─ scripts/
│  ├─ __init__.py
│  ├─ io_utils.py
│  ├─ stats_utils.py
│  ├─ uncertainty_utils.py
│  ├─ fit_utils.py
│  ├─ plot_utils.py
│  └─ format_utils.py
├─ experiments/
│  ├─ exp01_calibro/
│  │  ├─ run.py
│  │  └─ README.md
│  └─ exp02_pendolo/
│     ├─ run.py
│     └─ README.md
├─ reference_data/
│  └─ test_lineare.csv      ← dataset con risultati noti per validazione manuale
└─ tests/
```

---

## Moduli da implementare

### `io_utils.py`
Funzioni per:
- lettura di file CSV o TXT;
- gestione di separatori diversi;
- rinomina delle colonne;
- controllo di valori mancanti;
- esportazione di dati processati.

### `stats_utils.py`
Funzioni per:
- media aritmetica;
- mediana;
- moda, se utile;
- deviazione standard campionaria;
- deviazione standard della media;
- numero di osservazioni;
- controllo preliminare di outlier.

### `uncertainty_utils.py`
Funzioni per:
- incertezza assoluta e relativa;
- incertezza strumentale da risoluzione;
- distribuzione uniforme e gaussiane elementari;
- combinazione in quadratura;
- propagazione per somma, differenza, prodotto, rapporto e potenze;
- compatibilità tra due misure o tra misura e valore atteso.

### `fit_utils.py`
Funzioni per:
- regressione lineare;
- fit pesato;
- stima di pendenza e intercetta;
- incertezza sui parametri del fit;
- residui;
- chi quadro ridotto, dove applicabile;
- gestione di rette di calibrazione.

### `plot_utils.py`
Funzioni per:
- scatter plot;
- grafici con error bar;
- visualizzazione della retta di fit;
- grafico dei residui;
- istogrammi di distribuzioni sperimentali;
- salvataggio automatico delle figure.

### `format_utils.py`
Funzioni per:
- arrotondamento coerente con l’incertezza;
- gestione delle cifre significative;
- formattazione di risultati del tipo `x ± σ`;
- testo pronto da inserire in una relazione.

> **Nota:** se il modulo risulta troppo piccolo in pratica, le sue funzioni possono essere assorbite in `stats_utils.py` senza perdita di coerenza.

---

## Ordine corretto di sviluppo
Per massimizzare l’utilità pratica del progetto, i moduli vanno sviluppati in questo ordine:

1. `io_utils.py`
2. `stats_utils.py`
3. `uncertainty_utils.py`
4. `format_utils.py`
5. `fit_utils.py`
6. `plot_utils.py`

Questo ordine è ottimale perché riflette il workflow reale di laboratorio:
prima si leggono i dati, poi si analizzano statisticamente, poi si assegnano e combinano le incertezze, poi si presentano i risultati, infine si fa il fit e si costruiscono i grafici.

---

## Fasi del progetto

### Fase 1 — MVP statistico
Obiettivo: avere una pipeline minima funzionante.

Da implementare:
- caricamento di dati da CSV;
- media, deviazione standard, errore sulla media;
- stima di incertezza strumentale semplice;
- stampa corretta del risultato finale.

Output atteso:
- tabella pulita;
- risultati statistici base;
- stringhe formattate per la relazione.

Validazione manuale: confrontare i risultati su `reference_data/test_lineare.csv` con valori calcolati a mano o con un foglio di calcolo. Se i numeri coincidono, la fase è superata.

### Fase 2 — Incertezze complete
Obiettivo: trattare correttamente misure e propagazione errori.

Da implementare:
- combinazione di errori casuali e sistematici;
- propagazione delle incertezze;
- compatibilità tra misure;
- gestione delle distribuzioni uniformi da risoluzione.

Output atteso:
- risultati completi con incertezze ben motivate;
- funzione riutilizzabile per ogni nuova esperienza.

### Fase 3 — Fit e grafici
Obiettivo: analizzare relazioni tra grandezze sperimentali.

Da implementare:
- fit lineare ai minimi quadrati;
- fit pesato;
- grafico dati + retta di fit;
- grafico dei residui;
- estrazione di pendenza e intercetta con incertezze.

Output atteso:
- figure pronte per la relazione;
- parametri sperimentali con errore;
- analisi quantitativa della qualità del fit.

### Fase 4 — Calibrazione ed estensione
Obiettivo: rendere il progetto davvero utile per più laboratori.

Da implementare:
- rette di calibrazione;
- interpolazione/estrapolazione;
- template per nuove esperienze;
- test automatici;
- esempi documentati.

Output atteso:
- toolbox solida e riutilizzabile durante il corso;
- base buona anche per corsi successivi.

---

## Dipendenze iniziali
Le librerie da usare nella prima versione sono:

- `numpy`
- `pandas`
- `matplotlib`
- `scipy`

Eventualmente, in una fase successiva:
- `pytest` per i test;
- `jupyter` per notebook esplorativi.

---

## Workflow consigliato per ogni esperienza
Per mantenere ordine e riutilizzabilità, ogni nuova esperienza dovrebbe seguire questo schema:

1. inserire i dati grezzi in `data/raw/`;
2. creare uno script o notebook dedicato nell’area `experiments/`;
3. usare i moduli comuni in `scripts/`;
4. salvare i risultati puliti in `data/processed/`;
5. esportare grafici e parametri finali;
6. copiare nelle relazioni solo output già verificati dal codice.

---

## MVP finale: funzioni minime indispensabili
La prima versione realmente utile del progetto deve saper fare almeno queste operazioni:

- leggere una tabella sperimentale;
- calcolare media, deviazione standard ed errore sulla media;
- stimare un’incertezza strumentale da risoluzione;
- combinare incertezze;
- verificare compatibilità con un valore atteso;
- eseguire un fit lineare;
- restituire pendenza e intercetta con relative incertezze;
- produrre un grafico con error bar;
- produrre un grafico dei residui;
- formattare risultati con cifre significative corrette.

---

## Obiettivo finale del progetto
Arrivare ad avere una **toolbox per Laboratorio 1** che sia:
- abbastanza semplice da usare rapidamente;
- abbastanza rigorosa da rispettare il linguaggio e i metodi del corso;
- abbastanza modulare da poter essere estesa in futuro.

In sintesi, il progetto deve nascere come una raccolta di script per:

**statistica descrittiva + incertezze + strumenti di misura + minimi quadrati + calibrazione**.

Questo è il nucleo più coerente con le lezioni seguite e rappresenta la base migliore su cui costruire anche strumenti più avanzati in seguito.
