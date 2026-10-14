# Audit scientifico e architetturale — mespy 2.0.0

Data: 11 ottobre 2026. Oggetto: working tree locale, base Git `d08002a`, incluse le modifiche già presenti all'inizio dell'analisi. Il codice esaminato di `src/mespy/fit_utils.py` ha SHA-256 `3f39af8f02f48c60eb2e596447281c98c2cb2e957d12732b352af18b9cc0bd6f`.

Questo documento propone interventi; **non implementa il redesign**. Nessun sorgente, test esistente o catalogo è stato modificato dall'audit. Durante l'analisi i metadati locali sono passati da 1.2.0 a 2.0.0 per modifiche esterne a questa attività; i riferimenti di riga riguardano il codice scientifico letto e verificato, non una release pubblicata.

## A. Executive summary

1. **P0: il ramo `sigma_x` non minimizza, in generale, il χ² efficace descritto dalla documentazione.** È una WLS iterativamente ripesata a pesi congelati, non York e non ODR. Un controesempio di tre punti dimostra una derivata non nulla al risultato dichiarato convergente.
2. **P0: grandi offset su x possono falsificare completamente χ² e p-value, anche con slope accurata.** Nel caso riprodotto, traslare x di `1e15` cambia χ² da 2.58 a 50.22 e p da 0.63 a circa `3.25e-10`.
3. **OLS e WLS con sole incertezze su y hanno formule dei parametri e della covarianza corrette in aritmetica esatta.** Non serve riscriverle con un solver generico: occorre consolidarle numericamente.
4. **La separazione attuale fra `absolute` e `residual` è statisticamente utile.** Il problema è l'API che sceglie il modello dagli input e la diagnostica `chi2=ν`, priva di potere informativo quando si stima la scala.
5. **P0/P1: covarianza e p-value del ramo x/y non hanno le garanzie suggerite dall'output.** Le incertezze sono quelle WLS con pesi trattati come fissi; la bontà del fit non è validata per quel procedimento.
6. **P0: proteggere i passaggi intermedi, non solo gli input.** Quadrati di x e σ, somme dei pesi e prodotti pesati possono andare in overflow su input finiti con risultati finali rappresentabili.
7. **P0: `variance(..., w, ddof!=0)` ha una semantica ambigua.** `sum(w)-ddof` è appropriato per pesi di frequenza, non in generale per pesi relativi o inverse varianze; normalizzare i pesi cambia il risultato.
8. **P1: separare fitting, rappresentazione del risultato e plotting.** `lin_fit` ha 37 parametri, di cui 30 di presentazione; una chiamata numerica non dovrebbe dipendere da stile e gestione delle figure.
9. **Il result object esiste già e va migliorato.** La dataclass `frozen` contiene un array modificabile; mancano matrice di covarianza, modello esplicito e previsione numericamente stabile.
10. **L'assenza di correlazioni è una limitazione accettabile solo se dichiarata.** Non esistono input per correlazione x/y, correlazioni fra punti o matrici complete; non si può chiamare questo un supporto implicito.
11. **P0/P1 fuori dal fit:** istogrammi costanti con `bin_width` possono perdere tutti i conteggi; `hist_range` può includere punti esterni. Un workflow stima impropriamente l'incertezza strumentale dalla dispersione di oggetti diversi.
12. **138 test passano**, ma non coprono i due difetti scientifici principali. Sono già presenti buoni test di validazione, cambi di unità di x, offset della slope, plotting e TOML.
13. **P1/P2: rendere sistematiche le verifiche di release.** Non c'è un workflow CI che esegua pytest sulle PR; il minimo setuptools dichiarato è incompatibile con i metadati PEP 639 usati.
14. **Target proporzionato:** OLS/WLS analitici centrati e scalati, modelli espliciti, risultato numerico autonomo, plotting separato. York come funzione distinta se il supporto x/y resta nella 2.0; GLS completo e altri modelli possono attendere.

**Valutazione:** il progetto è abbastanza piccolo da correggere senza trasformarlo in un framework, ma allo stato verificato non consiglierei di considerare la 2.0 pronta per analisi sperimentali affidabili con `sigma_x` o grandi offset.

## B. Architettura attuale e verifiche eseguite

### B1. Mappa

| Componente | Simboli/responsabilità | Dipendenze principali |
|---|---|---|
| `src/mespy/__init__.py:1–48` | Re-export di otto funzioni; `_register_styles()` eseguita all'import | Tutti i moduli pubblici, Matplotlib, importlib.resources |
| `src/mespy/stats_utils.py:1–261` | `median`, `weighted_mean`, `variance`, `covariance`, `standard_deviation`; validazione vettori/pesi | NumPy |
| `src/mespy/fit_utils.py:1–784` | `lin_fit`, `LinearFitResult`, validatori, serializzazione del risultato, grafico | stats_utils, plot_utils, _toml, NumPy, SciPy; pyplot importato nel ramo grafico |
| `src/mespy/plot_utils.py:1–513` | `histogram`, stile, validatori grafici, display IPython | stats_utils, NumPy, Matplotlib; IPython opzionale di fatto |
| `src/mespy/io_utils.py:12–97` | `load_csv`, rinomina/colonne obbligatorie/policy mancanti | pandas |
| `src/mespy/_toml.py:1–59` | Metadati, normalizzazione percorso, scrittura atomica | stdlib; tomli-w importato al bisogno |
| `src/mespy/stylelib/` | Stili `mespy`, `report`, `column` | Matplotlib |
| `tests/` | Test per ogni modulo, API, traduzioni/documentazione | pytest, stack runtime, Babel transitivo |
| `docs/source/` | Sphinx/MyST, italiano e cataloghi inglesi, quattro notebook | Sphinx, myst-nb, tema, sphinx-intl |
| `tools/release-check.sh`, `tools/smoke_imports.py` | Test locali, build, twine, import wheel | Strumenti di sviluppo |
| `trials/`, `data/`, `references/`, `figures/`, `assets/` | Esperimenti manuali, CSV, materiale didattico PDF, figure e branding | Non sono core installabile |
| `.github/workflows/` | Pubblicazione documentazione e workflow Claude | Nessuna pipeline pytest dedicata |

```text
mespy.__init__ ──► fit_utils ──► stats_utils ──► NumPy
       │              │
       │              ├──────► plot_utils ──► stats_utils
       │              │             └─────► Matplotlib / IPython
       │              ├──────► _toml ─────► tomli-w
       │              └──────► scipy.stats.chi2
       ├────────► io_utils ────────────────► pandas
       ├────────► plot_utils
       └────────► registrazione globale degli stili Matplotlib
```

Non ho rilevato un ciclo di import attuale. L'accoppiamento problematico è unidirezionale: il modulo numerico dipende dal modulo grafico e dalle funzioni statistiche pubbliche, che riconvalidano ripetutamente gli stessi dati.

I consumatori di `lin_fit` sono il re-export root, `tests/test_fit_utils.py`, `tests/test_public_api.py`, lo smoke test, le pagine `docs/source/moduli/fit_utils/`, i notebook `linear-fit.ipynb` e `plot-style.ipynb`, i due script `trials/lin_fit/` e `trials/workflows/prova1.py`. Non esiste un altro solver lineare nel package. Le formule delle pagine di funzionamento duplicano parti consistenti del sorgente.

### B2. Evidenze e limiti della verifica

- Letti tutti i moduli Python installabili, i test, metadata/build/CI, documentazione del fitting e statistica, esempi/notebook e script di prova; inventariati gli asset e consultate parti pertinenti dei PDF di riferimento. I binari generati e le immagini di branding non sono una seconda implementazione da verificare matematicamente.
- Comando: `PYTHONPATH=src MPLBACKEND=Agg .venv/bin/python -m pytest -q` → **138 passed in 3.20s**.
- Python 3.14.7, NumPy 2.4.4, SciPy 1.18.1, pandas 3.0.2, Matplotlib 3.10.8, pytest 9.1.1, setuptools 84.0.0, tomli-w 1.2.0.
- Build Sphinx italiana e inglese con `-W -D nb_execution_mode=off`, output isolato in `/tmp/mespy-v2-audit/`: entrambe riuscite. Non ho rigenerato i cataloghi `.po/.mo`.
- Eseguite separatamente le celle Python dei quattro notebook, nella directory degli esempi e con backend Agg: nessun errore. Questo verifica il codice, non il comportamento del frontend Jupyter o il rendering inline.
- `pip check`: nessun requisito installato incompatibile.
- Eseguiti controesempi numerici, incluse verifiche analitiche e una minimizzazione indipendente del criterio x/y. Script riproducibile: [audit/v2_0_0_reproductions.py](audit/v2_0_0_reproductions.py).
- Non eseguiti una matrice multipiattaforma, una nuova installazione con versioni minime, test di copertura statistica Monte Carlo o la pipeline completa di pubblicazione. Non deduco affidabilità scientifica dal solo passaggio dei test esistenti.

## C. Audit dettagliato di `lin_fit`

### C1. Modello realmente implementato

La firma è in `src/mespy/fit_utils.py:177–217`. L'intercetta è sempre libera. Non c'è fit vincolato, intercetta fissata, robust regression, rimozione automatica degli outlier o scatter intrinseco aggiuntivo.

| Input | Comportamento attuale | Assunzione necessaria |
|---|---|---|
| `sigma_y` assente, `fit_method=None` | Warning e passaggio a `residual`; pesi unitari | x esatte, dispersione verticale comune ignota |
| `fit_method='residual'`, nessuna σ | OLS; scala stimata da RSS/(N−2) | Errori verticali incorrelati, omoschedastici |
| `sigma_y` presente, metodo omesso o `absolute` | WLS con `1/sigma_y**2`; covarianza non riscalata | σ standard assolute note, errori verticali incorrelati |
| `residual` con `sigma_y` | Stessi parametri WLS; covarianza moltiplicata per χ² grezzo/(N−2) | Varianze proporzionali a σ², unico fattore globale ignoto |
| `sigma_x` e `sigma_y` presenti | Iterazione WLS con `σ_eff²=σ_y²+m²σ_x²` | Propagazione verticale senza correlazione x/y; stimatore approssimato |
| Solo `sigma_x` | `ValueError` | Caso non implementato |

La normalità non serve per ottenere le soluzioni algebriche OLS/WLS o le varianze sotto le rispettive ipotesi sui secondi momenti. Serve invece per le distribuzioni esatte di test, intervalli t e interpretazione χ² in campioni finiti. La documentazione deve distinguere questi livelli.

Sono supportate incertezze eteroschedastiche su y come vettore, e su x nel ramo approssimato. Non sono supportati σ scalari: `_as_float_vector` richiede `ndim == 1`. Liste, tuple, ndarray e Series numeriche compatibili vengono convertiti a float64. Array `(N,1)` e `(N,N)` sono rifiutati; non esiste broadcasting documentato delle incertezze.

### C2. F01 — L'iterazione con `sigma_x` non minimizza il criterio dichiarato — P0

**Posizione:** `src/mespy/fit_utils.py:501–533`, `lin_fit`; `docs/source/moduli/fit_utils/lin-fit/funzionamento.md:169–215`.

**Comportamento attuale:** ricostruisce i pesi dalla slope precedente, risolve una WLS che considera quei pesi costanti, arresta quando cambia poco la slope.

**Problema:** la derivata dei pesi rispetto alla slope non compare nelle equazioni risolte. Al punto fisso, in generale, la derivata del χ² efficace resta diversa da zero. La stabilità dell'iterazione non certifica il minimo.

**Regression test da introdurre prima della correzione:**

```python
x = np.array([0., 1., 2.])
y = np.array([0., 0., 2.])
sigma_x = sigma_y = np.ones(3)
# Per il futuro solver x/y rigoroso, caso isotropo TLS:
expected_m = (1 + np.sqrt(37)) / 6
expected_q = 2 / 3 - expected_m
expected_chi2 = (7 - np.sqrt(37)) / 3
```

Attuale: `m=1`, `q=-1/3`, `chi2=1/3`, `iterations=1`, `converged=True`.
Minimo analitico: `m=1.18046042171637`, `q=-0.5137937550497033`, `chi2=0.3057458232339269`.
Derivata rispetto a m al risultato attuale: `−1/3`, non zero.

**Impatto:** bias della slope, risultati dipendenti dalla direzione di regressione e falsa interpretazione della convergenza, anche con σ perfettamente valide. Con σx e σy costanti per tutti i punti, ogni iterazione mantiene pesi uniformi: i parametri rimangono sempre OLS, qualunque sia l'importanza dell'incertezza orizzontale.

**Proposta:** rendere esplicito che l'attuale metodo è un'approssimazione; per la 2.0 spostare il supporto x/y in una funzione distinta con un metodo verificato, preferibilmente York per la sola retta. Se questo lavoro non entra nella release, rifiutare esplicitamente il caso x/y invece di conservarlo come fit rigoroso. Nessuna sostituzione automatica con `curve_fit`.

**Breaking change:** sì; cambiano endpoint e risultati. Motivazione scientifica, migrazione obbligatoria esplicitata.

### C3. F02 — Residui e diagnostiche instabili con grandi offset — P0

**Posizione:** `_fit_coefficients`, `fit_utils.py:173`; `lin_fit:535–543` e `665–666`.

**Comportamento:** stima bene la slope usando momenti centrati, ma calcola `q = ybar − m*xbar`, poi `residuals = y − m*x − q` e la retta grafica con `m*x+q`.

**Problema:** la cancellazione fra termini enormi distrugge le piccole deviazioni sperimentali. Migliorare la sola varianza di x non risolve questo passaggio.

**Regression test:** riusare `make_unit_change_data()` di `tests/test_fit_utils.py:602` e confrontare **residui, χ² e p-value**, oltre alla slope, dopo `x += 1e15`. Le differenze fra x sono rappresentabili esattamente.

| Quantità | x = 1,…,6 | x = 10¹⁵ + (1,…,6) |
|---|---:|---:|
| slope | 0.7994900396510877 | 0.7994900396510877 |
| residuals | circa `[.04870, −.04079, .01972, −.02977, .01074, .00125]` | `[.125, .125, .125, .125, .125, .125]` |
| χ² | 2.5798779650460455 | 50.217013888888886 |
| p-value | 0.6303917606881154 | 3.2530895751789977e−10 |

**Impatto:** un buon adattamento diventa apparentemente incompatibile con il modello; in `residual` si alterano anche tutte le incertezze stimate.

**Proposta:** conservare una parametrizzazione locale `y = a + m*(x−x_ref)`; calcolare centri e differenze tramite un'origine rappresentabile vicina ai dati, conservando la media delle differenze. Residui dalla forma centrata, `predict` e grafico dalla stessa rappresentazione. Convertire a q solo per esposizione; una q a grande distanza dai dati può essere intrinsecamente poco determinata.

**Breaking change:** nessun cambio del modello; valori precedentemente errati vengono corretti. L'aggiunta di `predict` è compatibile. Non pretendere che `slope*x+intercept` recuperi tutta la precisione della rappresentazione centrata.

### C4. F03 — Overflow intermedi e diagnostiche insufficienti — P0

**Posizione:** `fit_utils.py:493–495,505–506,535–555`; `stats_utils.py:39–40,104,162–164,212–218`.

**Regression test prima del fix:**

- `x=1e155+1e140*np.arange(6)`, `y=np.arange(6)`, `sigma_y=np.ones(6)`: varianza centrata e covarianza finale rappresentabili, ma `x**2` trabocca; messaggio attuale fuorviante: “x deve contenere solo valori finiti”, benché l'input sia finito.
- `x=[0,1,2]`, `y=[1,2,3]`, `sigma_y=[1e-154]*3`: singoli pesi finiti, somma in overflow; parametri e covarianza finale rappresentabili. Attualmente warning NumPy e `ValueError` sulla somma “strettamente positiva”.
- `weighted_mean([1e154,2e154], [1e155,1e155])`: ritorna `inf`, atteso `1.5e154`.

**Problema/Impatto:** l'invarianza rispetto alle unità si interrompe prima del limite effettivo di rappresentabilità del risultato; in altri percorsi si possono produrre inf/NaN senza un controllo finale.

**Proposta:** normalizzare i pesi, scalare coordinate e deviazioni, usare formule centrate per q/covarianza; evitare `r**2 / sigma**2` quando si può prima normalizzare r; norma scalata per somme di quadrati. `np.hypot(sigma_y, m*sigma_x)` evita alcuni overflow nel ramo efficace ma non corregge F01 e non protegge da ogni overflow del prodotto. Controllare risultati intermedi e finali, con eccezioni contestualizzate. Non silenziare i warning per restituire NaN.

**Breaking:** correttezza numerica; ampliamento del dominio accettato. Per risultati realmente non rappresentabili, errore esplicito, non clipping arbitrario.

### C5. F04 — Covarianza e p-value del ramo x/y non verificati — P0

**Posizione:** `fit_utils.py:548–579`; `tests/test_fit_utils.py:151–203` circa, test di scaling e `test_lin_fit_absolute_p_value_with_sigma_x_uses_effective_variance`.

**Comportamento:** usa la matrice WLS a pesi fissi, valutata sugli x osservati; restituisce `chi2_distribution.sf(chi2, N−2)` anche con `sigma_x`.

**Problema:** i pesi sono funzione dei parametri e x è incerta. Quelle formule non sono automaticamente la covarianza del modello errors-in-variables. Il test attuale verifica solo che il codice chiami la stessa survival function attesa; non verifica la distribuzione del criterio.

**Impatto:** incertezze e significatività possono essere interpretate come rigorose senza esserlo.

**Proposta:** per York usare le formule di incertezza associate al metodo, con punti aggiustati dove richiesto; distinguere covarianza assoluta da scaling dei residui. Per la prima API x/y proporrei `p_value=None`, documentando che la calibrazione χ² è eventualmente approssimata e richiede verifica separata. Non confondere un p-value del test sulla slope con quello di goodness-of-fit.

**Test:** benchmark pubblicati, caso Deming/TLS, limite σx→0, simulazioni di copertura con seed e tolleranze statistiche; confronto a solver indipendente sullo stesso modello. **Breaking:** sì per algoritmo, incertezze e semantica diagnostiche.

### C6. F05 — Pesi finali non sincronizzati — P1

**Posizione:** `fit_utils.py:505–524,539–550`.

**Comportamento:** la matrice di covarianza usa `weights` e `var_x` calcolati con la slope precedente; il χ² viene ricalcolato con la slope nuova.

**Regression test:** `x=arange(6)`, `y=[1,2,2,4,7,9]`, σy=1, σx=`[.1,2,.1,2,.1,2]`, `tol=1`. La varianza restituita della slope è `0.1146808651`; usando i pesi associati alla slope restituita, la stessa formula WLS dà `0.1128593495`.

**Impatto:** incoerenza interna amplificata da tolleranze lasche; al default spesso minuscola, ma distinta dall'errore scientifico F01.

**Proposta:** ogni solver restituisce un unico stato finale coerente. Se si mantiene temporaneamente l'approssimazione, aggiornare pesi e diagnostiche finali in modo coerente, chiarendo che questo non la trasforma in York.

**Breaking:** no, correzione. Test di coerenza e test di convergenza su parametri scalati, evitando un floor dimensionale fisso `1e-300` per slope prossime a zero.

### C7. F06 — χ² riscalato a uno e dimensioni di `scale_factor` — P1

**Posizione:** `fit_utils.py:545–591`; docstring `250–265,389–395`.

**Comportamento:** con scala stimata, `chi2=ν` e `reduced_chi2=1`, salvo fit esatto dove diventano zero; `p_value=nan`. `scale_factor` è una deviazione standard con unità y senza σ, un fattore adimensionale con σ.

**Classificazione:** lo scaling della **covarianza** è corretto per OLS/WLS a scala globale ignota. Il χ² auto-normalizzato è una scelta documentata ma poco utile, non una prova di buon fit. Le unità variabili dello stesso campo sono una debolezza API.

**Impatto:** per un principiante `reduced_chi2=1` sembra una validazione del modello anche quando i residui hanno una curvatura evidente. Il valore grezzo non è un campo direttamente disponibile.

**Proposta:** `rss` sempre; `weighted_rss` nei modelli pesati; `residual_scale` con unità y nei modelli a scala ignota. `chi2`, `reduced_chi2`, `p_value` disponibili solo per WLS assoluta con ipotesi appropriate; `None` negli altri casi. I pesi relativi vanno espressi con un parametro distinto, adimensionale.

**Regression test:** medesimo x, due y non lineari con diverse ampiezze dei residui: i costi devono distinguere gli adattamenti, senza inventare un goodness-of-fit dopo stima della scala. **Breaking:** sì per diagnostiche, campi e TOML.

### C8. F07 — Fit esatto e correlazione non definita — P1

**Posizione:** `fit_utils.py:553–570,582–587`.

**Comportamento:** per `x=[0,1,2]`, `y=[1,3,5]`, modalità residual, tutte le varianze stimate sono zero, ma `correlation=-0.7745966692`; residui normalizzati forzati a zero.

**Problema:** la correlazione statistica `Cov/(σm σq)` diventa 0/0. Il codice restituisce la correlazione della matrice prima dello scaling: può essere un limite geometrico utile, ma non è la correlazione della covarianza nulla restituita. Analogamente la normalizzazione 0/0 non è definita.

**Proposta/test:** ammettere scala stimata zero come caso limite esplicito, senza presentarla come certezza fisica; `correlation=None`, `normalized_residuals=None`, diagnostiche χ² assenti in OLS. Se si vuole un indicatore geometrico, dargli un nome distinto; non lo ritengo necessario. **Breaking:** sì, solo nel caso degenere e nei campi opzionali.

### C9. F08 — Output dichiarato immutabile ma modificabile — P1

**Posizione:** `LinearFitResult`, `fit_utils.py:34–54`; `_linear_fit_document:79–105`.

**Regression test:** `result.residuals[0] = 999` attualmente riesce; `chi2` rimane quello vecchio e il TOML esporta un risultato incoerente.

**Problema:** `frozen=True` protegge l'assegnazione ai campi, non i contenuti ndarray né la figura. Mancano modello x/y, dati/incertezze e rappresentazione centrata necessari per rieseguire o verificare il fit esportato. Un risultato costruito manualmente può contenere valori incoerenti: i test di serializzazione lo consentono esplicitamente.

**Proposta:** mantenere la dataclass, proprietà derivate da una singola matrice di covarianza; array copiati e read-only come contratto pratico; figura separata; costruttore validato o factory interna per risultati affidabili. Read-only NumPy non è una barriera contro manomissioni deliberate: documentare l'immutabilità logica, non una garanzia assoluta.

**Test:** input mutati dopo il fit non cambiano l'output; assegnazioni agli array pubblici rifiutate; matrice simmetrica/PSD; consistenza proprietà; export del metodo e delle assunzioni. **Breaking:** comportamento di mutazione e schema; mantenibili i nomi `slope_std`, `intercept_std`, `covariance` tramite proprietà.

### C10. F09 — Validazione incompleta o eccessivamente restrittiva — P1

**Posizione:** `fit_utils.py:108–151,458–491`; `stats_utils.py:9–22`.

Aspetti già corretti: rifiuto di vuoti, forme non 1D, lunghezze diverse, NaN/inf, σ non positive, x tutte uguali; interi convertiti prima dei quadrati; `max_iter` rifiuta bool e valori non interi.

Limiti da distinguere:

- N=2 con σ assolute: parametri e covarianza sono determinabili con x distinte. La restrizione N≥3 è una scelta conservativa, non una necessità della WLS. Il problema è solo ν=0 per χ² ridotto e test.
- σx=0: è valido per un'ascissa esatta, ma attualmente vietato; un futuro solver x/y deve definirne il limite, anche per soli alcuni punti, o rifiutare quel sottocaso in modo esplicito.
- σy scalare: utile e inequivoco; oggi vietato. Si può supportare solo broadcasting scalare→N, senza accettare implicitamente shape arbitrarie.
- `np.asarray(complex_ndarray, dtype=float)` scarta la parte immaginaria con warning: riprodotto con `[0,1,2]+1j`. Deve diventare `TypeError` prima del cast.
- Float32→float64 non recupera le differenze già perse; grandi interi oltre la precisione float64 possono diventare uguali. Dichiarare il dominio e non promettere precisione arbitraria.
- `_validate_positive_scalar('tol', True)` accetta bool; i controlli di scalari e array dovrebbero essere uniformi.
- `decimals`, `tol`, `max_iter` vengono validati anche se irrilevanti, mentre `xlim` e `ylim` no: effetto dell'accoppiamento con il plotting.

**Proposta/test:** contratto completo in F4, casi parametrizzati per input reali/scalari/vettori e cardinalità dipendente dal modello. **Breaking:** soltanto nuove restrizioni sugli input concettualmente errati e riorganizzazione firma; consentire N=2 o σ scalare amplia l'API.

### C11. F10 — Presentazione e calcolo mescolati — P1

**Posizione:** firma `fit_utils.py:177–217`, plotting `593–764`; `plot_utils.py:114–179`.

**Comportamento:** il fit crea di default una figura; `save_path` richiede `show_plot=True`; il context manager di stile mostra e chiude nuove figure in IPython. Fuori da IPython non chiama `plt.show()`, nonostante la docstring dica “generates and shows”. `histogram` invece supporta `ax` e restituisce `(fig, ax)`.

**Proposta:** `lin_fit` restituisce soltanto dati numerici; `plot_linear_fit(result, ...)` restituisce `(fig, (ax_fit, ax_res))`, supporta assi del chiamante e non fa display/close impliciti. Lo studente usa due istruzioni chiare e `plt.show()` quando serve; salvataggio con `fig.savefig`.

**Test prima del cambiamento:** output numerico indipendente dal grafico e dallo stile; nessuna figura creata da `lin_fit`; plot non modifica result; grafico salvabile con backend Agg senza display; figure del chiamante non chiuse.

**Breaking:** sì per argomenti grafici, default e `result.figure`. Beneficio concreto per scripting, notebook, test, optional dependencies e riuso su subplot.

### C12. F11 — Residui grafici e banda: significati da precisare — P1/P2

**Posizione:** `fit_utils.py:582–591,680–691,718–736`.

La banda `sqrt(1/W + (x−xbar)²/Sxx)` è corretta, con scaling coerente, per l'incertezza standard della **media prevista** nel modello y-only. Non è un intervallo di previsione di una nuova misura né una banda simultanea. Con scala stimata, ±1 standard error non ha automaticamente copertura normale del 68% per campioni piccoli; un intervallo di confidenza richiede il quantile t con ν gradi di libertà.

`r_i/σ_i` sono residui normalizzati, non residui studentizzati corretti per leverage: la loro varianza sotto il modello è `1−h_ii`, non uno. Nel ramo x/y i residui fisici sono disegnati con `sigma_y`, quelli normalizzati con `sigma_eff`; non sono due visualizzazioni equivalenti delle stesse barre. Non chiamare le barre “incertezza del residuo” senza una definizione.

**Proposta/test:** documentare la banda come incertezza sulla retta; offrire nel risultato `normalized_residuals` con formula esplicita. Se si aggiungono in futuro residui studentizzati, campo distinto e controllo `h_ii=1`. Il pannello grafico deve distinguere incertezze delle osservazioni, propagazione efficace e diagnostica dei residui. Test della banda al baricentro e a punti arbitrari usando la matrice di covarianza; pendenza/intercetta correlate comprese.

## D. Verifica matematica

### D1. Formule effettive y-only

Definiamo `ν=N−2`, `r_i=y_i−mx_i−q`, e:

\[
W=\sum_i w_i,\quad \bar x_w=\frac{\sum_iw_ix_i}{W},\quad
\bar y_w=\frac{\sum_iw_iy_i}{W},
\]
\[
S_{xx}=\sum_iw_i(x_i-\bar x_w)^2,\quad
S_{xy}=\sum_iw_i(x_i-\bar x_w)(y_i-\bar y_w).
\]

`weighted_variance` e `weighted_covariance` usati da `_fit_coefficients` hanno `ddof=0`, quindi restituiscono `Sxx/W` e `Sxy/W`. Le correzioni two-pass in `stats_utils.py:149–164,213–219` sottraggono l'effetto dell'errore numerico delle medie; sono nulle in aritmetica esatta. Segue:

\[
\hat m=S_{xy}/S_{xx},\qquad \hat q=\bar y_w-\hat m\bar x_w.
\]

Questi stimatori minimizzano `Q=Σ w_i r_i²` per **pesi fissi**. Con ordine dei parametri `(m,q)`:

\[
C_0=
\begin{pmatrix}
1/S_{xx}&-\bar x_w/S_{xx}\\
-\bar x_w/S_{xx}&1/W+\bar x_w^2/S_{xx}
\end{pmatrix}.
\]

Il codice usa `E_w[x²]/Sxx` nell'elemento qq, equivalente in aritmetica esatta poiché `E_w[x²]=Sxx/W+xbar²`. La versione centrata evita di elevare al quadrato tutti gli x originali.

### D2. A — OLS, dispersione ignota

Modello: `y_i=m*x_i+q+ε_i`, x esatte, `E ε=0`, `Cov(ε)=σ²I`, σ ignota. Pesi unitari, W=N.

\[
\mathrm{RSS}=\sum r_i^2,\quad s^2=\mathrm{RSS}/(N-2),\quad \widehat C=s^2C_0.
\]
\[
\widehat{\mathrm{Var}}(m)=\frac{s^2}{\sum(x_i-\bar x)^2},\quad
\widehat{\mathrm{Var}}(q)=s^2\left(\frac1N+\frac{\bar x^2}{\sum(x_i-\bar x)^2}\right),
\]
\[
\widehat{\mathrm{Cov}}(m,q)=-\frac{s^2\bar x}{\sum(x_i-\bar x)^2}.
\]

**Esito:** `fit_method='residual'` senza σ implementa queste formule correttamente, salvo problemi numerici già descritti. `s²` è lo stimatore corretto con ν; non è lo stimatore ML che dividerebbe per N. Non esiste un goodness-of-fit χ² assoluto usando come σ la stima ottenuta dagli stessi residui: RSS/s²=ν per costruzione.

Oracle esatto: `x=[0,1,2]`, `y=[0,1,3]`. `m=3/2`, `q=−1/6`, `r=[1/6,−1/3,1/6]`, `RSS=1/6`, `ν=1`, `Cmm=1/12`, `Cqq=5/36`, `Cmq=−1/12`. Utile perché verifica contemporaneamente parametri, segno della covarianza e scaling.

### D3. B — WLS, σy assolute note

Modello: `Cov(ε)=diag(σ_y,i²)`, x esatte; pesi `w_i=1/σ_y,i²`. Si minimizza:

\[
\chi^2=\sum_i(r_i/\sigma_{y,i})^2.
\]

`C=C0`, **senza moltiplicazione per χ²/ν**. Le incertezze sono `sqrt(diag C)`; la correlazione è `Cmq/sqrt(Cmm*Cqq)`, quando definita. `reduced_chi2=chi2/ν`. Con errori gaussiani indipendenti, modello corretto e N>2, `chi2~χ²_ν`; `p_value=sf(chi2,ν)` è il test di coda superiore, non la probabilità che la retta sia vera.

**Esito:** il ramo `absolute` y-only è corretto in aritmetica esatta. Eteroschedasticità supportata. Il p-value non è esatto per il solo fatto che l'utente abbia fornito dei numeri chiamati σ: occorrono le ipotesi distributive e l'assenza di correlazioni.

Oracle: `x=[0,1,2]`, `y=[0,1,3]`, `sigma_y=[1,2,1]`. `m=3/2`, `q=−1/18`, `chi2=1/18`, `ν=1`, `Cmm=1/2`, `Cqq=17/18`, `Cmq=−1/2`. Pesi non uniformi, risultati verificabili senza invocare mespy o un algoritmo equivalente.

### D4. B — WLS, scala globale ignota

Modello distinto: `σ_i=s*v_i`, v positivi noti relativamente, s ignota. Con `w_i=1/v_i²`:

\[
Q=\sum_i(r_i/v_i)^2,\quad \hat s^2=Q/\nu,\quad \widehat C=\hat s^2C_0.
\]

**Esito:** con y-only il ramo `residual` con σ è una scelta statistica legittima di questo tipo. Non è una correzione automatica da applicare perché il χ² assoluto non è vicino a 1, e non modella uno scatter intrinseco additivo `σ_i²+τ²`.

Moltiplicare tutti i v per k>0 lascia i parametri e la covarianza finale invariati, mentre `s` cambia come `1/k`. Con σ assolute, invece, moltiplicarle per k lascia invariati i parametri, moltiplica C per k² e divide χ² per k². Questa distinzione deve essere un test e un esempio didattico.

### D5. C — Perché l'algoritmo x/y è soltanto approssimato

Per `v_i(m)=σ_y,i²+m²σ_x,i²`, il criterio descritto è:

\[
Q(m,q)=\sum_i\frac{r_i^2}{v_i(m)}.
\]
\[
\frac{\partial Q}{\partial q}=-2\sum_i\frac{r_i}{v_i},\qquad
\frac{\partial Q}{\partial m}=-2\sum_i\frac{x_ir_i}{v_i}
-2m\sum_i\frac{\sigma_{x,i}^2r_i^2}{v_i^2}.
\]

Al punto fisso WLS si annulla il primo termine della derivata in m; il secondo non si annulla in generale. Questa è una dimostrazione dal codice, indipendente da un riferimento software.

La formula di propagazione `Var(εy−m εx)=σy²+m²σx²` è esatta per una combinazione lineare a m fissata e covarianza x/y nulla. È **lo stimatore iterativo** ad essere approssimato, non necessariamente la formula di varianza.

Nel modello funzionale errors-in-variables, con ascisse vere ξ_i ignote ma fisse e errori gaussiani indipendenti, il criterio completo è:

\[
\sum_i\left[\frac{(x_i-\xi_i)^2}{\sigma_{x,i}^2}
+\frac{(y_i-m\xi_i-q)^2}{\sigma_{y,i}^2}\right].
\]

Eliminando analiticamente ξ_i si ottiene Q. Quindi il criterio efficace può avere una giustificazione rigorosa; la WLS a pesi congelati del repository non ne segue la minimizzazione. Un modello probabilistico strutturale sulle ξ, una marginalizzazione o una likelihood condizionale con varianza dipendente da m possono richiedere termini ulteriori: non aggiungere o eliminare `log(v_i)` senza dichiarare il modello.

| Alternativa | Accuratezza/assunzioni | Costo e idoneità |
|---|---|---|
| WLS con propagazione una tantum o iterativa | Approssimazione utile se il contributo x è trascurabile; non corregge in generale l'attenuazione | Semplice ma non adatta come default rigoroso x/y |
| Minimizzazione diretta di Q profilato | Coerente col modello funzionale specificato; ricerca del minimo e covarianza da trattare seriamente | Buon oracle indipendente; non basta lanciare un minimizzatore locale una volta |
| York | Metodo specializzato per una retta con σx, σy eteroschedastiche e correlazioni nello stesso punto | Raccomandato se si mantiene x/y: algoritmo limitato, senza nuova dipendenza runtime, ma richiede benchmark e formule proprie della covarianza |
| Deming/TLS | Deming per rapporto di varianze appropriato e omoschedasticità; TLS isotropo per errori uguali nelle coordinate scalate | Ottimo caso analitico di riferimento; non sostituisce il caso generale |
| ODR | Modello errors-in-variables più generale, con correzioni anche sulle x | Più complesso di quanto serva alla sola retta; backend e convenzioni da verificare |

La documentazione dell'implementazione York in isogeochem espone esplicitamente la correlazione per punto e rimanda a York et al. 2004: [documentazione primaria del pacchetto](https://search.r-project.org/CRAN/refmans/isogeochem/html/york_fit.html). Il paper da usare per implementare e verificare le equazioni è [York et al., DOI 10.1119/1.1632486](https://doi.org/10.1119/1.1632486); il testo completo dell'editore non era accessibile tramite il browser in questa sessione, quindi non dichiaro una verifica riga per riga di una futura implementazione York.

Non propongo di fondare una nuova architettura su `scipy.odr`: la documentazione corrente lo dichiara deprecato da 1.17 e previsto in rimozione in 1.19, indicando `odrpack` come alternativa. È un ulteriore costo di manutenzione da valutare, non una dipendenza da aggiungere automaticamente. [Release notes ufficiali SciPy](https://docs.scipy.org/doc/scipy/release/1.17.0-notes.html).

### D6. D — Correlazioni

**Oggi:** nessun parametro `rho_xy`, nessuna covarianza fra osservazioni, nessuna matrice completa. Passare una matrice a `sigma_y` genera errore di shape; non viene interpretata come matrice. Se l'utente passa solo le diagonali di misure correlate, le correlazioni sono assenti dal modello e l'output non può tenerne conto.

Con correlazione nello stesso punto:

\[
v_i(m)=\sigma_{y,i}^2+m^2\sigma_{x,i}^2
-2m\rho_i\sigma_{x,i}\sigma_{y,i}.
\]

Il termine misto può aumentare o diminuire la varianza efficace. `LinearFitResult.correlation` è invece la correlazione **fra parametri stimati**: non descrive correlazioni fra errori di misura.

Per y correlate e x esatte, GLS richiederebbe:

\[
Q=r^T\Sigma_y^{-1}r,\quad
\hat\beta=(X^T\Sigma_y^{-1}X)^{-1}X^T\Sigma_y^{-1}y.
\]

Queste formule sono la definizione, non un invito a implementare `inv`: usare whitening tramite Cholesky e risoluzione della least squares. La covarianza assoluta è `(XᵀΣ⁻¹X)⁻¹`; scaling separato solo se Σ è nota a meno di scala.

**Scope consigliato 2.0:** OLS/WLS con indipendenza fra punti; se incluso `lin_fit_xy`, correlazione x/y per punto esplicita. **Fuori scope dichiarato:** covarianza completa fra punti, sistematiche comuni modellate mediante nuisance parameters, covariance x/y fra punti differenti. GLS può essere una funzione futura distinta `lin_fit_gls`, senza overload ambiguo di `sigma_y`.

La scelta di rimandare GLS limita l'uso avanzato ma è onesta. La libreria non deve suggerire che una sistematica comune si riduca come un rumore indipendente facendo più misure.

### D7. Classificazione delle conclusioni

| Questione | Classificazione |
|---|---|
| Parametri e covarianza OLS/WLS y-only in aritmetica esatta | Formule corrette |
| Scaling della covarianza con scala globale ignota | Scelta statistica legittima, purché esplicita |
| Scaling della covarianza con σ assolute note | Sarebbe incoerente; il ramo absolute attuale correttamente non lo fa |
| Varianza efficace nel modello lineare a m fissata | Formula corretta per errori x/y incorrelati |
| Iterazione attuale presentata come minimizzazione del criterio efficace | Bug matematico rispetto al criterio dichiarato |
| Covarianza WLS applicata al ramo x/y | Approssimazione non giustificata come covarianza rigorosa EIV |
| χ² ridotto forzato a 1 in residual | Scelta discutibile di output, non errore nella covarianza OLS/WLS |
| Correlazione numerica con matrice di covarianza nulla | Quantità non definita come dichiarata; possibile limite geometrico da denominare separatamente |
| N≥3 anche con σ assolute | Limitazione documentabile, non bug dello stimatore |
| Nessuna matrice di covarianza degli input | Limitazione documentabile; non supporto implicito |
| Residui instabili per offset / overflow evitabile | Bug numerici |
| `sum(w)-ddof` con pesi non specificati | Formula legittima per frequenze, API statisticamente ambigua per pesi generici |

## E. Numerical robustness e performance

### E1. Strategia numerica consigliata

Preservare il metodo analitico O(N), ma svolgere il calcolo in coordinate locali scalate. Una pipeline concreta:

1. Validare una volta e convertire esplicitamente a float64. Non mutare gli input.
2. Scegliere origini vicine ai dati; calcolare differenze locali senza ricostruire troppo presto una media a grande offset. Se il range stesso rischia overflow, prescalare prima delle sottrazioni.
3. Normalizzare i pesi con un riferimento delle σ, per esempio `u_i=(sigma_ref/sigma_i)**2`, con `sigma_ref=min(sigma)`, registrando separatamente la scala assoluta. Se rapporti estremi diventano zero, rilevare la perdita di informazione e verificare il rango effettivo; non fingere che tutti i punti abbiano ancora un peso rappresentabile.
4. Centrare e scalare le differenze di x e, quando necessario, di y. Calcolare medie locali, Sxx e Sxy riutilizzando le stesse riduzioni. Mantenere la correzione two-pass ove utile.
5. Risolvere analiticamente in queste coordinate. Conservare il coefficiente locale e la covarianza locale, dove la correlazione può essere molto minore rispetto a `(m,q)`.
6. Calcolare residui dalla forma locale, χ² da residui normalizzati e somme di quadrati con scala numerica. Non elevare prima al quadrato grandezze che si normalizzeranno dopo.
7. Trasformare parametri e covarianza alle unità originali con il Jacobiano; esporre q, ma usare `predict` centrato per previsione e grafico.
8. Verificare rango, finitezza, segno delle varianze e simmetria. Saturare una correlazione oltre ±1 soltanto se lo scarto è compatibile con arrotondamento e la covarianza è altrimenti valida; non “riparare” matrici chiaramente errate.

Per esempio, con `w_i=u_i/sigma_ref²`:

\[
\mathrm{Var}(m)=\frac{\sigma_{ref}^2}{\sum u_i(x_i-\bar x_u)^2}.
\]

Anche questa espressione va ordinata e scalata per evitare che `sigma_ref²` underflowi prima di una divisione compensante. Non basta normalizzare i pesi se si continuano a formare tutti i quadrati nelle unità originali.

### E2. Scelte da confrontare

| Metodo | Accuratezza | Prestazioni | Leggibilità/didattica | Dipendenze | Scelta |
|---|---|---|---|---|---|
| Momenti analitici centrati e scalati | Ottima per retta di rango 2; richiede cura degli estremi | O(N), costante piccola | Formule verificabili direttamente | NumPy | Default OLS/WLS |
| QR sul design centrato/scalato | Buona, evita normal equations esplicite | O(N) per due colonne, overhead maggiore | Più generale, meno immediata | NumPy/SciPy già presenti | Oracle o futura estensione; non necessaria sostituzione oggi |
| SVD / `lstsq` | Ottima diagnosi del rango in coordinate appropriate | O(N) qui, overhead maggiore | Tolleranze di rango da spiegare | NumPy | Riferimento nei test e casi generali |
| Cholesky | Efficace per whitening di covarianze SPD | O(N³) per matrice densa N×N | Giustificata per GLS | NumPy/SciPy | Solo supporto correlazioni completo futuro |
| Inversa delle normal equations | Peggiora il condizionamento rispetto al design | Nessun beneficio per la retta | Apparentemente breve, meno verificabile numericamente | NumPy | Da evitare come refactoring automatico |
| `longdouble` ovunque | Precisione e disponibilità dipendono dalla piattaforma | Costi variabili | Nasconde il problema senza garantirne la soluzione | NumPy | Non come contratto pubblico |

**Quasi degenerazione:** x distinte ma vicine non vanno rifiutate usando un epsilon assoluto sulla varianza; dipenderebbe dalle unità. Le incertezze possono essere grandi e scientificamente legittime. Distinguere rango nullo, perdita numerica dovuta alla rappresentazione e semplice scarsa informazione sperimentale. Un controllo numerico si fa dopo scaling e con criteri relativi documentati. Una q enorme/fortemente correlata può essere una conseguenza reale dell'extrapolazione a x=0.

**Correlazione:** nel probe con offset `1e9`, il codice restituisce `−1.0000000000000002`. Piccolo difetto numerico, diverso da F02. Non ricostruire la banda da `Cqq + 2*x*Cmq + x²*Cmm` in coordinate globali quando i tre termini si cancellano: conservarne la forma locale.

**dtype:** la promozione di interi e float32 è giusta; non recupera informazione persa prima della chiamata. Rifiutare complessi; decidere e documentare bool, stringhe numeriche e masked arrays. Una maschera non deve essere ignorata silenziosamente dal cast: il default consigliato è errore per valori mascherati, lasciando il filtraggio esplicito al chiamante.

### E3. Profiling a livello di codice

`_fit_coefficients` richiama quattro funzioni statistiche pubbliche: varianza, covarianza e due medie. Ognuna riconverte/ricontrolla dati e pesi e ricalcola somme e medie; la covarianza valida anche y. Nel ciclo x/y questo costo si ripete a ogni iterazione. Inoltre `lin_fit:582–591` alloca residui normalizzati e barre scalate anche con `show_plot=False`.

**Ottimizzazioni utili:** un kernel privato che accetta vettori già validati e restituisce parametri locali, somme e covarianza; riuso del baricentro e di Sxx; calcolo di array grafici solo nel plotting; import pesanti al bisogno. Migliorano contemporaneamente leggibilità, robustezza e tempo.

**Micro-ottimizzazioni irrilevanti:** eliminare cast scalari, comprimere espressioni, preallocare vettori di pochi punti, ottimizzare l'indice del loop. Non prioritarie.

**Da evitare:** calcolo dei momenti con `E[x²]−E[x]²`, inversione matriciale per brevità, Numba/JIT o parallelismo per dataset di laboratorio piccoli, cache globali degli input. Non serve alcuna nuova dipendenza per ottimizzare questo core. Nessun benchmark temporale è stato usato per dichiarare speedup.

## F. API review e specifica del risultato

### F1. Firma proposta per la 2.0

Scelgo un modello **obbligatorio e keyword-only**, per eliminare la selezione statistica automatica. Il costo didattico è una parola esplicita, documentabile con tre esempi.

```python
FitMethod = Literal['ols', 'wls', 'wls_relative']

def lin_fit(
    x: ArrayLike,
    y: ArrayLike,
    *,
    method: FitMethod,
    sigma_y: ArrayLike | float | None = None,
    relative_sigma_y: ArrayLike | float | None = None,
) -> LinearFitResult:
    ...
```

| Metodo | Input consentiti | Modello | N minimo | Scaling C |
|---|---|---|---:|---|
| `ols` | x, y; nessuna σ | σ verticale comune ignota | 3 | RSS/ν |
| `wls` | σy assolute standard, scalare o N | Var(y_i)=σy_i² | 2, x distinte | Nessuno |
| `wls_relative` | `relative_sigma_y=v`, scalare o N, adimensionale | Var(y_i)=s²v_i²; s ignota in unità y | 3 | Q/ν |

`sigma_y` in OLS è errore, non ignorato. In `wls_relative` si usa un nome distinto perché v non è un'incertezza assoluta misurata. Il metodo resta identico qualunque siano gli argomenti: combinazioni incompatibili producono errore. `sigma_y` diventa keyword-only; non manterrei un terzo posizionale dal significato variabile.

Il core v2 qui specificato ha **sempre intercetta libera**. `intercept=0` non è un'opzione travestita da default; il fit vincolato è rinviato e, quando introdotto, dovrà essere esplicito e usare ν=N−1. Un'intercetta nota con incertezza non equivale a un'intercetta fissata esattamente.

Per mantenere il supporto x/y nella 2.0, endpoint distinto:

```python
def lin_fit_xy(
    x: ArrayLike,
    y: ArrayLike,
    *,
    sigma_x: ArrayLike | float,
    sigma_y: ArrayLike | float,
    rho_xy: ArrayLike | float = 0.0,
    tol: float = 1e-10,
    max_iter: int = 100,
) -> LinearFitResult:
    """York, incertezze assolute; indipendenza fra punti."""
```

Il nome separato rende esplicito il diverso modello; l'algoritmo York è parte del contratto, non selezionato in funzione delle shape. N≥3 per la prima versione x/y; σy>0, σx≥0, caso esatto sulle x gestito e verificato; `|rho_xy|<1` per punti con entrambe le incertezze positive. Se σx=0, imporre rho=0. Nessuno scaling residual implicito per x/y nella prima versione. Se questi requisiti non vengono implementati e verificati, **non esportare ancora `lin_fit_xy`**.

Una funzione GLS futura avrebbe un parametro dedicato `cov_y`, mutuamente esclusivo con σy, e una propria documentazione; non è inclusa nel contratto v2 minimo.

### F2. `LinearFitResult`: contenuto motivato

Mantenere una dataclass senza gerarchia di classi di fit, con proprietà derivate dove possibile. Rendere pubblico il tipo anche alla root migliora annotazioni e discoverability; non è indispensabile rinominare i moduli `*_utils`.

| Campo/proprietà | Significato/unità | Disponibilità |
|---|---|---|
| `method` | `ols`, `wls`, `wls_relative`, eventualmente `york` | Sempre |
| `slope`, `intercept` | m [Y/X], q [Y] | Sempre |
| `covariance_matrix` | Cov(m,q), ordine dichiarato `(slope, intercept)`; diagonale [Y²/X²], [Y²], fuori diagonale [Y²/X] | Sempre per un fit accettato; stimata nei modi a scala ignota |
| `slope_std`, `intercept_std` | Radici della diagonale; [Y/X], [Y] | Proprietà, sempre |
| `covariance` | Elemento mq [Y²/X] | Proprietà compatibile con il nome attuale |
| `correlation` | Cov/(σmσq), adimensionale | `None` se almeno una varianza è zero |
| `x`, `y` | Copie delle osservazioni [X], [Y] | Permettono plotting/verifica coerenti; niente DataFrame copiato |
| `sigma_y` / `relative_sigma_y` | Modello di incertezza realmente usato | Solo il campo pertinente; eventualmente σx/rho per York |
| `fitted_values` | Media prevista alle x osservate [Y], dalla forma centrata | Array derivato o memorizzato; per York esplicitare che sono valori alle x osservate |
| `residuals` | `y−fitted_values` [Y] | Sempre |
| `normalized_residuals` | WLS: r/σy; OLS: r/s; relativo: r/(s v); York: r/sqrt(v_eff) | `None` con scala zero; non studentizzati |
| `rss` | Σr² [Y²] | Sempre, diagnostica descrittiva |
| `weighted_rss` | WLS: Σ(r/σy)² adimensionale; relativo: Σ(r/v)² [Y²]; York: criterio profilato adimensionale | `None` per OLS; metodo documenta le unità |
| `residual_scale` | s stimata [Y] | OLS/relativo; `None` per incertezze assolute |
| `dof` | N−2 | Sempre; è nominale nel caso x/y nonlineare |
| `chi2` | Criterio assoluto y-only; per York, valore del criterio con interpretazione approssimata esplicita | `None` per OLS/relativo |
| `reduced_chi2` | chi2/ν | `None` se chi2 assente o ν=0 |
| `p_value` | Goodness-of-fit di coda superiore sotto modello gaussiano WLS | `None` per OLS/relativo, ν=0 e, nella prima versione, York |
| `iterations` | Iterazioni del solver x/y | 0 per y-only; mantenerlo è economico ma non indispensabile |

La semantica dimensionale di `weighted_rss` è dichiarata per metodo; al contrario di `scale_factor`, non implica che quantità fisicamente diverse rappresentino sempre un fattore moltiplicativo di incertezza. Si può anche limitarlo al metodo relativo e usare `chi2` per quelli assoluti per evitare duplicazione.

Conservare internamente origine x, valore locale della retta e covarianza locale per:

```python
result.predict(x_new)       # media prevista in modo numericamente stabile
result.mean_std(x_new)      # incertezza standard della media prevista
result.to_toml(path)        # sola serializzazione, nessun grafico
```

`predict` può accettare scalare o vettore, restituendo rispettivamente float o ndarray, con overload typing; deve rifiutare non finiti e shape non supportate. `mean_std` non include il rumore di una nuova misura. Intervalli di previsione e confidence level espliciti possono attendere.

Non aggiungerei R², AIC/BIC, statistiche sui parametri o prediction intervals “gratis”: hanno ipotesi e semantiche ulteriori. `converged` è oggi sempre True in ogni risultato restituito, perché il fallimento alza un'eccezione; si può deprecare senza perdere informazione. Eviterei tuple implicite e `__iter__`: oggi la dataclass non offre destructuring, quindi non c'è compatibilità da mantenere su quel comportamento.

Rimuovere `figure`; sostituire `residual_std` con il più preciso `residual_scale` solo dove è una stima di scala. Se si vuole mantenere il numero `sqrt(RSS/ν)` negli altri modelli, chiamarlo esplicitamente `residual_rse`, come riepilogo descrittivo, non “incertezza comune”. La mia proposta minima non lo aggiunge.

### F3. Cinque esempi della proposta, non API già implementate

```python
import numpy as np
from mespy import lin_fit, load_csv
from mespy.plot_utils import plot_linear_fit

# 1. Prime misure: x considerate esatte, dispersione verticale ignota.
t = np.array([0., 1., 2., 3., 4.])
s = np.array([.12, .93, 2.08, 2.94, 4.04])
fit = lin_fit(t, s, method='ols')
print(fit.slope, fit.slope_std, fit.residual_scale)
assert fit.p_value is None

# 2. Incertezza standard assoluta comune su y.
fit = lin_fit(t, s, method='wls', sigma_y=0.08)
fig, axes = plot_linear_fit(fit, xlabel='tempo [s]', ylabel='spazio [m]')
fig.savefig('moto.pdf')

# 3. Eteroschedasticità, σ determinate sperimentalmente.
df = load_csv('misure.csv', required_columns=['x', 'y', 'sigma_y'])
fit = lin_fit(df['x'], df['y'], method='wls', sigma_y=df['sigma_y'])
print(fit.chi2, fit.dof, fit.p_value)
print(fit.predict(np.array([1.5, 2.5])))
fit.to_toml('fit.toml')

# 4. Sono noti solo i rapporti delle deviazioni standard.
fit = lin_fit(t, s, method='wls_relative',
              relative_sigma_y=[1., 1., 2., 1., 1.5])
print(fit.residual_scale, fit.covariance_matrix)

# 5. Solo se l'endpoint York supera i gate di validazione.
from mespy import lin_fit_xy
fit = lin_fit_xy(t, s, sigma_x=0.03, sigma_y=0.08, rho_xy=0.0)
print(fit.slope, fit.slope_std)
```

Il terzo esempio presuppone un file dell'utente; non è uno smoke test eseguibile senza dati. Gli altri illustrano chiamate future, non cambiamenti effettuati in questo audit.

### F4. Contratto degli errori

| Input/condizione | Tipo proposto | Esempio di messaggio |
|---|---|---|
| Oggetti non numerici, complessi, bool per opzioni numeriche | `TypeError` | `x deve contenere numeri reali; ricevuti valori complessi` |
| Shape non 1D di x/y, vettori vuoti | `ValueError` | `x deve avere forma (N,) e contenere almeno un punto` |
| Lunghezze diverse | `ValueError` | `x e y devono avere la stessa lunghezza: 4 e 5` |
| N insufficiente | `ValueError` | `method='ols' richiede N >= 3 per stimare la dispersione; ricevuto N=2` |
| N=2 in WLS assoluta, x distinte | Nessun errore | ν=0; `reduced_chi2=None`, `p_value=None` |
| x tutte uguali o rango numerico nullo dopo scaling | `ValueError` | `La pendenza non è identificabile: x non ha variazione rappresentabile` |
| σy≤0, relative σ≤0; σx<0 | `ValueError` | `sigma_y deve essere finita e > 0; valore non valido all'indice 2` |
| NaN/inf | `ValueError` | `y contiene un valore non finito all'indice 3` |
| Metodo/input incompatibili | `ValueError` | `method='ols' non accetta sigma_y; usa method='wls'` |
| Range/rank perso per scale estreme | `FloatingPointError` | `Il risultato non è rappresentabile in float64; verifica scale e unità di x, y e sigma_y` |
| York non converge | `RuntimeError` o sottoclasse dedicata semplice | `York non converge dopo 100 iterazioni (variazione normalizzata=...)` |
| Matrice futura GLS non quadrata/simmetrica/finita/SPD | `ValueError` | `cov_y deve essere una matrice simmetrica definita positiva di forma (N,N)` |

Per GLS futuro: validare simmetria con tolleranza relativa dichiarata; Cholesky per SPD; non fare jitter silenzioso né pseudoinversa automatica su matrici semidefinite. I vincoli esatti richiedono un modello distinto. Messaggi stabili nei concetti, test su frammenti utili anziché sull'intera punteggiatura.

`None` rappresenta una quantità statisticamente non definita dal modello; `NaN` non deve diventare un contenitore indistinto per errori numerici e assenza di significato. TOML non supporta null: omettere i campi non applicabili e documentare metodo/schema, oppure usare una tabella di disponibilità; non serializzare la stringa `'None'` come numero.

### F5. Inventario e decisioni sull'API pubblica

| Simbolo attuale | Categoria | Decisione motivata |
|---|---|---|
| `mespy.load_csv` | IMPROVE | Conservare DataFrame e policy; validare ambiguità delle colonne e documentare che il CSV non certifica dati numerici per il fit |
| `mespy.median` | KEEP | Funzione piccola e utile; eredita validazione numerica condivisa più rigorosa |
| `mespy.weighted_mean` | IMPROVE | Conservare nome/firma; normalizzare numericamente pesi e dati, chiarire che restituisce una media, non la sua incertezza |
| `mespy.variance` | REDESIGN | Separare semantica dei pesi da ddof; mantenere il default descrittivo ddof=0 |
| `mespy.covariance` | IMPROVE | Normalizzazione descrittiva attuale legittima; allineare le opzioni di normalizzazione a variance se estese |
| `mespy.standard_deviation` | REDESIGN | Deve seguire esattamente il contratto di variance; non duplicarne logica |
| `mespy.histogram` | IMPROVE | Correggere bins/range, validare prima della creazione della figura, display esplicito, conservare `ax` |
| `mespy.lin_fit` | REDESIGN | Modello esplicito, y-only, separazione grafico, input di incertezza non ambigui |
| `mespy.fit_utils.LinearFitResult` | IMPROVE | Conservare dataclass, aggiungere matrice/predizione/stato numerico coerente; root re-export opzionale consigliato |
| `LinearFitResult.to_toml` | IMPROVE | Mantenere API; nuovo schema quando cambia la semantica |
| `FitMethod` in `fit_utils` | REDESIGN | Literal che descrive il modello, non soltanto la scelta di scaling |
| `MissingPolicy` in `io_utils` | KEEP | Alias utile nel modulo, nessuna necessità di esportarlo alla root |
| `FloatVector` nei moduli | KEEP | Alias typing interno; definire esplicitamente che non è un endpoint stabile |
| `plot_utils.STYLELIB` | DEPRECATE | Costante non usata dal core e non documentata come contratto; renderla privata o eliminarla dopo controllo consumatori |
| `_as_float_vector`, `_validate_*`, `_fit_coefficients` | KEEP privati / spostare internamente | Documentarli nelle note per sviluppatori non li rende API pubblica |
| Argomenti grafici di `lin_fit`, `result.figure` | REMOVE dal core | Trasferiti a `plot_linear_fit` e al risultato Matplotlib |
| Scelta `fit_method=None`, ramo x/y implicito | REMOVE | Eliminano ambiguità statistica; nessun alias che cambi modello silenziosamente |
| `result.scale_factor`, `result.residual_std` | RENAME/REDESIGN | `residual_scale` dove esiste una scala stimata, semantica per modello |
| `result.converged` | DEPRECATE | Ridondante se nessun risultato non convergente è restituito |

I simboli importati accidentalmente nei namespace di modulo, come `np`, `math`, `Path`, non sono API intenzionale. Aggiungere `__all__` nei moduli chiarisce il confine, senza pretendere che impedisca import espliciti. Non serve rinominare `fit_utils` in `fitting` solo per stile.

### F6. Migrazione old → new

| Prima | Proposta | Costo / motivazione |
|---|---|---|
| `lin_fit(x,y,show_plot=False)` | `lin_fit(x,y,method='ols')` | Basso; modello esplicito |
| `lin_fit(x,y,sy,show_plot=False)` | `lin_fit(x,y,method='wls',sigma_y=sy)` | Basso; σ assolute chiaramente identificate |
| `lin_fit(x,y,sy,fit_method='residual')` | `lin_fit(x,y,method='wls_relative',relative_sigma_y=sy/sy_ref)` | Medio; scegliere un riferimento positivo, v adimensionale; parametri e C restano equivalenti, `residual_scale` diventa `old.scale_factor*sy_ref` |
| `lin_fit(...,sigma_x=sx)` | `lin_fit_xy(...,sigma_x=sx,sigma_y=sy)` | Medio/alto; rivedere risultati, non solo codice, per nuovo stimatore |
| `r=lin_fit(...,xlabel=...,save_path=...)` | `r=lin_fit(...); fig,axes=plot_linear_fit(r,...); fig.savefig(...)` | Medio; separazione di calcolo e output |
| `r.reduced_chi2` in residual | `r.rss`, `r.residual_scale`, esame dei residui | Medio; cambia intenzionalmente il significato diagnostico |
| `math.isnan(r.p_value)` | `r.p_value is None` | Basso; distinguere assenza statistica da NaN numerico |
| `r.residuals[...] = ...` | Copia esplicita `residuals = r.residuals.copy()` | Basso; preservare consistenza del risultato |
| Parser TOML schema 1 | Parser schema 2 con campi opzionali e metodo | Medio; la semantica nuova deve essere versionata |

Per gli script esistenti, documentare una tabella di migrazione e mantenere fixture schema 1. Non promettere compatibilità numerica del ramo x/y né introdurre un wrapper `legacy` automatico che perpetui l'ambiguità. Non rompere i nomi dei moduli senza necessità.

## G. Test plan ordinato per priorità

### G1. Copertura esistente da preservare

`tests/test_fit_utils.py` copre: dati gaussiani a seed fisso con slope positiva, residual OLS confrontata con `np.polyfit`, scaling assoluto/relativo, controlli di p-value, assenza σ con warning, σx iterativa su dati moderati, plotting/stili/residui normalizzati/salvataggio, input invalidi, x costanti o duplicate, unità di x da 10⁻¹² a 10¹², grandi offset limitatamente alla slope, non convergenza, round-trip TOML.

`tests/test_stats_utils.py` include un oracle razionale `Fraction` per covarianza e trasformazioni di offset: ottima pratica da riutilizzare. `tests/test_public_api.py` protegge alcuni default, export e `py.typed`, ma usa un sottoinsieme anziché l'uguaglianza per `__all__`. Nessun test esistente verifica la minimizzazione del criterio x/y o la stabilità dei residui a `1e15`.

### G2. P0 — regression test bloccanti

| ID | Caso | Oracle/assert da fissare prima del fix |
|---|---|---|
| T01 | x/y isotropo di F01 | Soluzione TLS analitica; gradiente Q nullo; Q ≤ quello OLS; test fallisce oggi |
| T02 | Grande offset di F02 | Residui, χ², p, scala stimata invarianti; non soltanto slope; fallisce oggi |
| T03 | Overflow evitabile | σ=1e−154 e x circa 1e155 con dispersione 1e140; risultati rappresentabili corretti, niente warning criptici |
| T04 | OLS oracle D2 | m, q, matrice completa, RSS, ν esatti entro tolleranza float64 |
| T05 | WLS eteroschedastica oracle D3 | Pesi inverso-varianza, matrice non scalata, χ²=1/18 |
| T06 | σ assolute moltiplicate per k | Parametri invarianti, C×k², χ²/k² |
| T07 | Pesi relativi moltiplicati per k | C finale e parametri invarianti; scala inversa |
| T08 | `variance` con pesi relativi / ddof | Invarianza a normalizzazione dei pesi nel nuovo contratto o errore esplicito; non accettare vecchia formula generica |
| T09 | Input non reali/non finiti | Nessun cast complesso silenzioso; NaN/±inf rifiutati in ogni vettore e opzione scalare |
| T10 | Istogramma costante e range | Somma conteggi corretta; `[1,1,1]` non scompare; esclusione dei dati fuori range |

Il gate di correctness deve includere questi test nella stessa modifica che corregge la matematica; il fatto che la suite corrente passi non è un motivo per posticiparli a “cleanup”.

### G3. P1 — matrice sistematica del fitting

| Dimensione | Casi richiesti | Controlli |
|---|---|---|
| Geometria della retta | Esatta; m positivo, negativo, zero; q=0; x negativi e attraversamento di zero | Parametri, C, residui; C=0 solo se scala ignota e RSS=0 |
| Rumore | Gaussiano con seed; eteroschedastico noto; curva non lineare deliberata | Non confondere vicinanza al parametro vero con prova di correttezza; confronto analitico/oracle del fit sul dataset osservato |
| Pesi | Costanti, eteroschedastici, estremamente diversi, globalmente riscalati | Equivalenze appropriate; rango dopo scaling; comportamento quando un peso scompare numericamente |
| Scale | 1e−12, 1e12 e limiti float64 ragionati; offset grandi su x, y e su entrambi | Preservazione di unità e quantità rappresentabili, oracoli sui float realmente ricevuti |
| Cardinalità | Vuoto, 1 punto, 2 punti, 3 punti, duplicati parziali | OLS/relativo N≥3; WLS assoluta N=2 definita con ν=0 |
| Degenerazione | Tutti x uguali; x vicine ma distinte; differenze sotto ULP; design effettivamente dominato da un punto | Errore su rango non identificabile, nessuna soglia assoluta dipendente dalle unità |
| Tipi | List, tuple, ndarray int/float32/float64, Series, array non contigui, sola lettura | Stesso risultato sui medesimi valori rappresentati; nessuna mutazione dell'input |
| Input invalidi | Shape 0D/2D, lunghezze diverse, σ≤0, NaN/inf, complessi, ragged, maschere | Tipo/messaggio errore; broadcasting solo delle σ scalari |
| Risultato | Read-only, covarianza simmetrica/PSD, proprietà coerenti, correlazione nulla/non definita | Assenza di drift fra campi duplicati; `predict` stabile |
| Presentazione | Plot on/off separato, assi esterni, banda alla media e in extrapolazione | Nessuna modifica al fit; banda della media distinta da prediction band |
| Export | Metodi, unità semantiche, None/scala zero, versioni schema, errori di scrittura | Round-trip; file precedente intatto se serializzazione/replace falliscono |
| York se incluso | σx→0, σx=0 parziali, slope vicino a zero, segni, rho positivo/negativo, non convergenza | TLS/Deming, benchmark, gradiente del criterio e covarianza specifica |

OLS e WLS a pesi costanti hanno gli stessi parametri. Hanno la stessa covarianza **solo** se la σ assoluta comune è scelta uguale alla scala stimata OLS. Un test che pretenda sempre l'uguaglianza delle incertezze sarebbe sbagliato.

Con y costante e OLS esatto la varianza stimata è zero; non arrotondare a zero RSS “molto piccolo” con una tolleranza assoluta: dipenderebbe dalle unità.

### G4. Proprietà e unità fisiche

Per trasformazioni `x'=a*x+b`, `y'=c*y+d`, con a,c non nulli e incertezze trasformate coerentemente:

\[
m'=\frac ca m,\quad q'=cq+d-\frac{cb}{a}m,\quad
J=\begin{pmatrix}c/a&0\\-cb/a&c\end{pmatrix},\quad C'=JCJ^T.
\]

Residui `r'=c*r`; RSS moltiplicata per c². Nel modello assoluto, χ² e ν invariati, e p-value invariato dove definito. Per x→100x: m e σm divisi per 100, q e σq invariati, Cov(m,q) divisa per 100. Per y→cy+d: le incertezze cambiano con |c|, non con c; le covarianze col Jacobiano. Per inversioni di segno in York, `rho_xy` cambia con `sign(a*c)`.

Altre proprietà: permutazione dei punti; traslazione di y che non cambia la slope; aggiunta di una retta nota a y in y-only; invarianti delle equazioni normali `Σw r≈0` e `Σw(x−xbar)r≈0`; positività delle varianze; `mean_std(x)` coerente con la covarianza locale.

Iniziare con pytest parametrizzato e seed fissati. Hypothesis può diventare dipendenza **solo di test**, utile per combinare trasformazioni e scale; non necessaria per la prima correzione. Definire strategie che generino dati identificabili e riferimenti basati sui valori effettivamente rappresentati. Le tolleranze devono riflettere scala e condizionamento, non un `atol=1e-8` universale che accetta qualunque errore su valori minuscoli.

### G5. Confronti di riferimento corretti

- `np.linalg.lstsq` sul design `[x_centered_scaled, 1]` e whitening y-only: oracle indipendente per i parametri, con ricostruzione della covarianza e delle unità. Non testare grandi offset con un design globale mal condizionato e chiamarlo verità.
- `scipy.stats.linregress`: riferimento per OLS senza x uncertainty, con convenzioni di standard error verificate. Non per WLS eteroschedastica.
- `numpy.polyfit`: se usato come oracle pesato, `w=1/sigma_y`, non `1/sigma_y**2`, perché il peso moltiplica il residuo prima del quadrato; scegliere scaling della covarianza coerente. [Documentazione NumPy](https://numpy.org/doc/stable/reference/generated/numpy.polyfit.html).
- `curve_fit`: per una retta y-only, `absolute_sigma=True` per WLS assoluta; False per scala ignota. Non corregge incertezze su x. [Documentazione SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html).
- Riferimento ODR, se usato temporaneamente nei test: `cov_beta` non è scalata da `res_var`, mentre `sd_beta` lo è; confrontare le stesse quantità. [Documentazione SciPy Output](https://docs.scipy.org/doc/scipy/reference/generated/scipy.odr.Output.html). Non far dipendere a lungo termine la suite da un modulo deprecato.
- Monte Carlo: prima y-only, verificare copertura e calibrazione χ² sotto ipotesi gaussiane; poi York se incluso. Tolleranze derivate dall'errore Monte Carlo, seed fisso, suite statistica più lenta separata dai test unitari.

## H. Repository-wide issues e dependency review

### H1. Statistica descrittiva: pesi e `ddof` — P0

**File/simboli:** `src/mespy/stats_utils.py:107–165`, `variance`; `223–261`, `standard_deviation`; documentazione `docs/source/moduli/stats_utils/variance/funzionamento.md`.

Attualmente:

\[
V_w=\frac{\sum_iw_i(x_i-\bar x_w)^2}{\sum_iw_i-ddof}.
\]

- Con ddof=0 è un momento descrittivo pesato legittimo, invariante a `w→k*w`.
- Con pesi di frequenza interi, ddof=1 ha il significato di correzione campionaria sul campione replicato.
- Con pesi relativi arbitrari, ddof=1 non è invariante alla loro normalizzazione e non ha quella semantica.
- Con inverse varianze, sottrarre un numero puro alla somma di pesi con unità fisiche è anche dimensionalmente sospetto. Non esiste una sola formula universale di “varianza campionaria pesata”.

**Esempio riprodotto:** `x=[1,2,3]`, `w=[1,1,2]`, ddof=1 → `11/12 ≈ .916667`; con `10*w` → `55/78 ≈ .705128`, pur avendo identica importanza relativa.

Per pesi analitici fissi e osservazioni IID, una correzione comunemente utilizzata impiega `W−Σw²/W`, non `W−1`. Questo non la rende automaticamente la stima della dispersione di misure eteroschedastiche con inverse varianze. La distinzione `fweights/aweights` e la normalizzazione sono esplicite in [NumPy cov](https://numpy.org/doc/stable/reference/generated/numpy.cov.html).

**Proposta minima v2:** mantenere `w` per momenti descrittivi con ddof=0; per w presente e ddof diverso da zero, richiedere una semantica esplicita o rifiutare la combinazione. Non cambiare silenziosamente il denominatore. Se c'è una necessità concreta, aggiungere `weight_kind='frequency'|'relative'` con ipotesi chiare; altrimenti rimandare l'estensione e indicare NumPy per quei casi. Questo problema non altera direttamente `lin_fit` attuale, che chiama variance con ddof=0.

**Altri bug:** `ddof=np.nan` restituisce NaN; `ddof=-np.inf` restituisce 0. Validare tipo, scalarità e finitezza; decidere esplicitamente se ammettere ddof negativi o frazionari. Non occorre vietare frazioni per ragioni matematiche, ma il contratto deve essere chiaro. Test prima del fix: questi due input più le proprietà di scala dei pesi.

`covariance` normalizzata a N/W e `variance` con default 0 sono coerenti descrittivamente. Non cambiare automaticamente il default a ddof=1: una correzione di Bessel è una scelta statistica, non un miglioramento universale.

### H2. `histogram`: difetti di conteggio e validazione — P0/P1

**File:** `src/mespy/plot_utils.py:387–450`, `histogram`.

1. **Costante allineata ai bin:** `[1,1,1]`, `bin_width=1` produce `start=stop=1` e un solo bordo; il grafico ha zero barre. Regression test: somma dei conteggi=3 e almeno un intervallo valido. Garantire almeno due bordi distinti.
2. **Range violato:** `[.1,.5,1.5,1.9]`, `hist_range=(.4,1.6)`, `bin_width=1` produce bordi `[0,1,2]`, `range=None`, conteggi `[2,2]`: include .1 e 1.9 fuori range. Definire se troncare i bin o filtrare i valori prima di costruirli; il contratto attuale suggerisce esclusione fuori range. Test atteso: due dati inclusi, non quattro.
3. **Conflitto ndarray:** `bins=np.array([0,1,2,3])` con `bin_width=1` esegue `if bins != 'auto'` e produce “truth value of an array is ambiguous”. Validare il conflitto senza confronto booleano vettoriale.
4. **`bin_width=inf/nan`:** controllo solo `<=0`, poi warning o errori NumPy da `arange`. Richiedere scalare reale, finito e positivo. Larghezze troppo piccole possono richiedere un numero di bin enorme o non incrementare più i bordi: errore esplicito o limite documentato.
5. **Validazione dopo creazione figura:** vari input invalidi lasciano una figura vuota aperta. Validare range, bins, ddof e dimensioni prima di creare assi.
6. Media/deviazione standard calcolate sull'intero input anche con `hist_range`: scelta possibile, ma grafico e legenda devono dirlo oppure riferirsi allo stesso campione visualizzato. Oggi il significato non è evidente.

Correggere il conteggio cambia i risultati, ma è un bug fix, non un redesign cosmetico. La banda dell'istogramma rappresenta dispersione dei dati, non incertezza della media; mantenere chiara questa distinzione nella documentazione.

### H3. IO e interoperabilità — P1/P2

**File/simbolo:** `src/mespy/io_utils.py:12–97`, `load_csv`.

La policy dei mancanti e il controllo colonne dopo rinomina sono utili e già testati. Il ritorno DataFrame è coerente con la dipendenza pandas: sostituirlo con csv standard cambierebbe significativamente l'API.

Mancano casi da definire/testare:

- `required_columns='massa_g'` è una `Collection[str]` ma viene iterata carattere per carattere; rifiutare la stringa o trattarla esplicitamente come una sola colonna.
- `if required_columns` può essere ambiguo per un array/Index; usare controllo esplicito su None e iterazione, evitando booleani di collezioni vettoriali.
- Rinomine che producono colonne duplicate: una selezione `df['x']` può diventare un DataFrame 2D e fallire nel fitting. Rifiutare collisioni, con messaggio utile, o documentarne l'accettazione se intenzionale.
- `missing='drop'` scarta righe con mancanti in qualsiasi colonna, anche non usata nel fit: scelta documentata, da mantenere evidente. Non esegue una validazione di finitezza numerica: inf non è NaN, colonne testuali sono consentite.
- Non dedurre automaticamente incertezze o unità dai nomi delle colonne. Un tipo/protocollo “MeasurementTable” non è necessario per risolvere questi casi.

Gli ultimi punti sono limiti del contratto o casi individuati dal codice, non errori dei test già esistenti. Usare test su CSV temporanei per renderli concreti prima di correggere.

Verifica aggiuntiva eseguita su CSV temporaneo: stringa in `required_columns` interpretata come caratteri, array di due nomi con errore booleano ambiguo, rinomina duplicata accettata e selezione della colonna risultante 2D. Anche un masked array passato a `lin_fit` è stato accettato perdendo la maschera: includerlo fra i test di validazione.

### H4. Stile e side effect — P1/P2

**File/simboli:** `src/mespy/__init__.py:18–37`, `_register_styles`; `plot_utils.py:22–31`, `_resolve_style`; `136–179`, `_style_context`.

- L'import root carica Matplotlib, pandas e SciPy, anche per `median`, e registra nomi generici `report`/`column` nella libreria globale degli stili. Non modifica gli rcParams attivi, ma può sovrascrivere stili omonimi già registrati.
- Lo smoke test evita l'import eager di **pyplot**, non l'import di tutte le dipendenze pesanti. Non descriverlo come prova di un core NumPy-only.
- `_resolve_style` restituisce un percorso dopo l'uscita da `as_file`: in installazioni zip-backed quel percorso temporaneo può non esistere più quando usato. È un difetto potenziale dedotto dal lifetime, non riprodotto nell'installazione filesystem corrente. Risolvere la risorsa all'interno del context manager che la usa, oppure utilizzare lo stile già caricato come dict.
- `except Exception: pass` nella risoluzione nasconde cause inattese. Limitare le eccezioni a quelle di risorsa non disponibile, lasciando errori di lettura/parsing informativi.
- Display/chiusura automatica dentro uno style context sono responsabilità separate; avvengono anche in `finally` dopo un errore. Spostare il display al chiamante.
- `show_grid=True` può lasciare una griglia disabilitata dallo stile; usare `None` per “eredita lo stile” e True/False per override, oppure correggere la documentazione. Non imporre cambiamenti estetici non richiesti.

Si possono mantenere i tre stili; non serve riscriverli. Preferire nomi qualificati o registrazione esplicita per prevenire collisioni. Qualunque cambio della registrazione automatica va citato nella migrazione.

### H5. Produzione dei risultati e TOML — P1/P2

**File/simboli:** `_toml.py:36–59`, `_write_toml_document`; `fit_utils.py:79–105`, `_linear_fit_document`.

Punti validi: serializzazione prima di toccare il target, file temporaneo nella stessa directory, `os.replace`, pulizia su errore, figure escluse, metadati e schema, valori a precisione float64 completa. Non serve sostituirli con un framework di serializzazione. Atomicità di sostituzione non equivale a durabilità contro ogni crash: la documentazione non dovrebbe promettere più di questo.

Per v2: schema 2, ordine della matrice, metodo statistico, assenza esplicita delle diagnostiche non applicabili e rappresentazione centrata necessaria a riprodurre le previsioni. Se l'export è inteso come semplice riepilogo, dichiararlo; se vuole rendere riproducibile l'analisi, includere x/y/incertezze e opzioni scientifiche. `iterations>0` da solo non identifica il modello usato.

Test mancanti: fallimento di `tomli_w.dumps` o `os.replace` lascia intatto il file precedente e non lascia temporanei; versione/schema sbagliato rifiutato da un futuro loader. Non serve aggiungere un loader se non c'è un bisogno: fixture documentate bastano come contratto iniziale. La versione ottenuta da importlib.metadata è quella della distribuzione installata, non una certificazione del contenuto di una working tree modificata.

### H6. Esempi e documentazione — P0/P2

**P0 didattico:** `trials/workflows/prova1.py:34–38` chiama `standard_deviation` sull'intera colonna di masse e volumi per ottenere una presunta incertezza strumentale. I dati di `trials/workflows/data/misure.csv` sono oggetti con volumi diversi: la dispersione include la variazione del misurando. Servono ripetizioni dello stesso oggetto, informazioni strumentali o un modello di incertezza, non la deviazione della distribuzione dei campioni. Il commento parla di `m=ρV`, ma il fit include comunque un'intercetta libera: esplicitarlo.

**P2:** `trials/latex/tabular.py` importa `mespy.latex_utils`, modulo assente, e termina con `df =`, sintassi incompleta. Non è un modulo pubblico da resuscitare automaticamente: archiviarlo o dichiararlo scratch; non presentarlo come esempio funzionante. `tools/release-check.sh` compila solo src/tests, quindi non lo rileva.

**P2:** `docs/source/moduli/fit_utils/lin-fit/funzionamento.md:167` dice “varianza ... non troppo vicina a zero”; il codice controlla `>0` e finitezza, oltre a x tutte uguali. Correggere per non suggerire una soglia assoluta inesistente. Le parti sul criterio efficace e sulla mutabilità devono essere corrette come in C.

Le pagine replicano lunghe sezioni di codice: agevolano la lettura didattica ma aumentano il rischio di divergenza. Preferire descrizione delle assunzioni/formule, pochi estratti inclusi dal sorgente e API generata o verificata; mantenere i dettagli dei privati in una guida per contributori. `tests/test_docs.py` verifica cataloghi completi, non l'allineamento semantico delle traduzioni dopo ogni modifica della sorgente.

Il Makefile forza `nb_execution_mode=off` per la build; la riuscita Sphinx non prova che i notebook funzionino. L'audit li ha eseguiti separatamente; automatizzare questo controllo periodico senza riscrivere gli output sorgente.

### H7. Packaging, CI e typing — P1/P2

**File:** `pyproject.toml:6–7,35–71`, `.github/workflows/`, `tools/release-check.sh`, `tests/test_public_api.py`.

- PEP 639 `license='MIT'` e `license-files` richiedono setuptools compatibile; `setuptools>=68` permette versioni che non li supportano. Impostare almeno `>=77` e preferibilmente `>=77.0.3` per includere le prime correzioni, verificando la build al minimo dichiarato. Il fatto che la macchina corrente abbia 84 non valida il lower bound. [Guida ufficiale setuptools](https://setuptools.pypa.io/en/stable/userguide/license_migration.html), [changelog 77.0.3](https://setuptools.pypa.io/en/latest/history.html).
- Dipendenze runtime senza lower bound: non è automaticamente un errore, ma non esiste una matrice che giustifichi l'intero dominio dichiarato. Determinare i minimi realmente necessari; non aggiungere upper bound arbitrari.
- `optional-dependencies.dev` e `dependency-groups.dev/docs` descrivono insiemi diversi; il gruppo `docs` contiene solo sphinx-intl e il gruppo dev non replica pytest. Chiarire quale comando installa l'ambiente completo, consolidare i gruppi e allineare il lock.
- CI attuale: pubblicazione docs su main e workflow Claude, nessun pytest standard su pull request. Aggiungere suite numerica, build wheel e smoke test, Python minimo e versioni supportate, Linux più almeno controlli essenziali Windows/macOS.
- Il release-check installa la wheel in un target isolato ma riusa le dipendenze dell'interprete corrente; è un buon controllo di artefatto, non un ambiente pulito né una verifica dei requisiti minimi.
- `py.typed` è presente, ma non c'è un type-checker configurato. `save_path` è annotato `str|None` pur accettando Path; ritorni di context manager e kwargs dict sono poco precisi. Parametri grafici `Figure/Axes` importati solo sotto TYPE_CHECKING richiedono attenzione all'introspezione runtime con `get_type_hints`; non giustificano caricare pyplot nel core.
- Backend Agg scelto nei test dopo import di pyplot; impostarlo in conftest/ambiente prima degli import. Molti test di fit non chiudono la figura: fixture di cleanup evita dipendenza dall'ordine e consumo di risorse. Alcuni test istogramma usano RNG globale senza seed: renderli deterministici anche se gli assert attuali sono strutturali.
- `Makefile:121–122`, `docs-serve`: dopo `cd docs/build/html` esegue il percorso relativo `.venv/bin/python`, che non si trova più nella root. Usare l'assoluto dell'interprete. Problema dedotto direttamente dal comando, non testato avviando un server.

### H8. Dipendenze, una per una

| Dipendenza dichiarata | Uso reale | Necessità e alternativa | Costo / decisione proposta |
|---|---|---|---|
| NumPy | Array, statistiche, fit, bins | Essenziale; Python puro non porta un beneficio | Core obbligatorio |
| SciPy | Solo `scipy.stats.chi2.sf` nel runtime corrente | Serve per p-value affidabile; `scipy.special.gammaincc` è alternativa nella stessa dipendenza; NumPy/stdlib non offrono un sostituto diretto equivalente | Conservare in v2 per diagnostiche coerenti, import al bisogno; non reimplementare la coda χ² |
| pandas | `load_csv` e ritorno DataFrame | Necessaria per API attuale; `csv` standard cambierebbe il contratto | Mantenere per semplicità di installazione v2; futura extra IO possibile dopo lazy import |
| Matplotlib | Istogrammi, fit plot, registrazione stili | Necessaria per grafici, non per matematica | Separare core/import; possibile extra plotting in futuro, non obbligo per questa release |
| tomli-w≥1.0 | Scrittura TOML | `tomllib` legge soltanto; writer manuale poco desiderabile | Piccola, mantenere; opzionale tecnicamente possibile ma aumenterebbe attrito |
| build | sdist/wheel | Strumento build standard, solo sviluppo | KEEP |
| setuptools | Backend build | Necessario al backend scelto | KEEP, correggere minimo |
| wheel | Toolchain di build dichiarata | Valutarne necessità col backend minimo scelto, senza migrazione di backend | Basso, nessuna priorità di rimozione |
| twine | Verifica/publish artefatti | Utile nel release-check | KEEP, development/release |
| pytest | Suite di test | Essenziale al workflow | KEEP, gruppo test esplicito |
| ipykernel | Esempi/notebook | Non serve agli utenti del core | Gruppo notebook/docs |
| Sphinx | Documentazione | Necessario al sito attuale | Gruppo docs |
| pydata-sphinx-theme | Tema del sito | Non runtime; cambiarlo sarebbe estetico | KEEP |
| myst-nb | Markdown e notebook Sphinx | Necessario alle sorgenti attuali | KEEP, costo build/kernel separato dal runtime |
| sphinx-copybutton | UX dei blocchi codice | Facoltativo per sito | KEEP finché utile; costo basso |
| sphinx-intl | Cataloghi EN/IT | Necessario al workflow bilingue | KEEP, gruppo docs coerente |
| IPython, Babel (uso transitivo) | Display opzionale; lettura .po nei test | IPython è già gestito con ImportError; Babel usato direttamente in tests/test_docs.py | Dichiarare nel gruppo appropriato ciò su cui i test fanno affidamento, evitando dipendenze transitive accidentali |

La proposta non richiede nuove dipendenze runtime. Un type-checker e, se adottato, Hypothesis sarebbero soltanto di sviluppo. Non ho rilevato una dipendenza runtime completamente inutilizzata. Trasformare tutte le dipendenze in extra ora aumenterebbe combinazioni da testare: meglio separare le responsabilità prima e conservare un'installazione semplice per studenti.

## I. Roadmap v2.0.0

Difficoltà: B=bassa, M=media, A=alta. I rischi indicano cosa verificare, non ragioni per lasciare bug noti. Ogni attività P0 include il proprio regression test nella stessa modifica.

### P0 — correctness, gate prima della release

| Attività | Beneficio | Rischio | Difficoltà | Breaking change |
|---|---|---|---|---|
| Correggere dichiarazioni e contratto di `sigma_x`; bloccare l'uso come fit rigoroso finché non validato | Evita inferenza basata sul metodo sbagliato | Migrazione dei workflow x/y | M; A se include nuovo solver | Sì |
| Parametrizzazione centrata per residui, previsioni e diagnostiche | Elimina falsi χ²/p su offset grandi | Trasformazioni di q/C da verificare | M | No, bug fix |
| Scaling numerico di pesi e momenti, controlli intermedi/finali | Preserva risultati rappresentabili, errori utili | Estremi float64, rank effettivo | M/A | No sul modello |
| Fissare formule/convenzioni OLS, WLS e relative con oracoli analitici | Protegge la correttezza già presente | Cambiare accidentalmente scaling | M | Solo convenzioni API esplicite |
| Eliminare ambiguità weighted `ddof`; validare ddof e complessi | Statistiche coerenti con pesi/unità | Chiamate esistenti con ddof pesato | M | Sì |
| Correggere istogrammi costanti e filtro range | Nessuna perdita/inclusione indebita di conteggi | Bordo destro e costanza dei bin | B/M | Correzione risultati |
| Correggere workflow che confonde dispersione dei campioni e incertezza strumentale | Evita un errore didattico sostanziale | Richiede dati/assunzioni espliciti nell'esempio | B | No API |

### P1 — v2 architecture

| Attività | Beneficio | Rischio | Difficoltà | Breaking change |
|---|---|---|---|---|
| Metodo esplicito e parametri σ assolute/relative separati | Assunzioni visibili, IDE e messaggi chiari | Migrazione di tutte le chiamate | M | Sì |
| Separare `plot_linear_fit` dal core | Test rapidi, assi esterni, salvataggio headless | Comportamento notebook da documentare | M | Sì |
| Rafforzare `LinearFitResult`, predict locale, matrice unica, campi opzionali | Output coerente e riutilizzabile | Mutabilità/None/schema | M | Sì, mantenere proprietà compatibili |
| York dedicato, se si conserva x/y nella 2.0 | Modello x/y difendibile | Incertezze, rho, convergenza e degenerazione | A | Sì, anche numerico |
| TOML schema 2 e fixture di migrazione | Risultati interpretabili nel tempo | Parser esterni schema 1 | M | Sì per formato |
| Correggere minimo setuptools, CI pytest/build sulle PR | Release ripetibili e gate automatici | Ambiente minimo vs corrente | B/M | Solo requisiti build |
| Consolidare validazione interna senza passare da funzioni pubbliche a ogni iterazione | Meno duplicazione e controlli incoerenti | Validazione saltata nei nuovi percorsi | M | No |

### P2 — quality

| Attività | Beneficio | Rischio | Difficoltà | Breaking change |
|---|---|---|---|---|
| Matrice test G3/G4, copertura statistica periodica | Affidabilità oltre i casi singoli | Test lenti/flaky se mal progettati | M | No |
| Type-checker, overload di predict, Path coerente, __all__ moduli | IDE e contratti affidabili | Stub dipendenze, typing troppo restrittivo | M | Minimo |
| Assunzioni statistiche, tutorial σ, bande e p-value; migration guide | Usabilità per studenti e utenti avanzati | Divergenza EN/IT | M | No |
| Esecuzione automatica notebook; verifica snippet e cataloghi aggiornati | Esempi davvero eseguibili | Tempo build | M | No |
| Gestione figure/stili, risorse `as_file`, errori di plotting | Meno side effect e problemi d'installazione | Notebook già dipendenti dal display automatico | M | Sì per display se non già in P1 |
| IO: colonne duplicate, collection, test mancanti | Passaggio CSV→fit più prevedibile | Restrizioni su input prima tollerati | B | Limitato |
| Unificare gruppi sviluppo, lock e controlli wheel installata | Ambiente riproducibile | Scelta del workflow canonico | B/M | No runtime |
| Archivio trials incompleti, docs-serve, cleanup fixture | Manutenzione quotidiana | Basso | B | No |

### P3 — future, non necessari alla 2.0

| Attività | Beneficio | Rischio | Difficoltà | Breaking change |
|---|---|---|---|---|
| GLS y-only con covarianza completa | Errori sistematici/correlati fra punti | SPD/condizionamento/semantica | M/A | Endpoint additivo |
| Fit con intercetta fissata | Modelli fisici vincolati | ν diverso; vincolo esatto vs incerto | M | Additivo esplicito |
| Scatter intrinseco, robust regression, outlier model | Casi avanzati | Nuovi modelli e assunzioni | A | Nuovi endpoint |
| Intervalli di previsione/confidenza, leverage/studentizzazione | Diagnostica più ricca | Confondere bande/pull/test | M | Additivo |
| Supporto di oggetti con unità | Controllo dimensionale automatico | Dipendenza e integrazione ndarray | A | Da progettare |
| Extra IO/plotting, import root pienamente lazy | Installazione minima | Matrice degli extra, UX studenti | M | Packaging |
| ODR generale/nonlineare con backend dedicato | Fitting oltre la retta | Nuova dipendenza e manutenzione | A | Nuovo modulo |

**Ordine operativo consigliato:** prima T01/T02 e oracoli OLS/WLS; quindi fix numerici e decisione x/y; poi nuova firma/risultato/plot; infine migrazione, CI e documentazione. Le correzioni matematiche non aspettano la fine del refactoring.

## J. Proposed target architecture e specifica ideale finale

### J1. Struttura concreta, senza framework

```text
src/mespy/
    __init__.py          # API esplicita; evitare caricamento grafico non necessario
    fit_utils.py         # lin_fit, LinearFitResult; validazione del modello/orchestrazione
    _linear_fit.py       # kernel OLS/WLS centrato e scalato, covarianza/diagnostiche
    _validation.py       # vettori reali finiti, scalarità, shape; nessun plotting
    _york.py             # solo se incluso e validato: solver x/y specializzato
    stats_utils.py       # statistiche descrittive con semantica pesi dichiarata
    plot_utils.py        # histogram, plot_linear_fit, context di stile senza display
    io_utils.py          # load_csv e policy tabellari
    _toml.py             # serializzazione e scrittura atomica; schema esplicito
    stylelib/
    py.typed
```

Non serve un file per ogni classe o per ogni formula. `LinearFitResult` può restare in `fit_utils.py`; `_linear_fit.py` restituisce uno stato interno piccolo, da cui costruirlo. Se il modulo resta leggibile, anche il kernel può inizialmente rimanere privato nello stesso file: la separazione logica conta più del numero di file. Nessuna classe base `Fit`, registro di plugin o protocollo solver è necessario per una retta e un eventuale York.

**Dipendenze desiderate:** validazione→NumPy; kernel→NumPy e diagnostiche SciPy; API→validazione+kernel; plotting→risultato numerico e Matplotlib; IO→pandas; export→tipi primitivi+tomli-w. Nessun import del plotting nel kernel. Se `plot_utils` importa il tipo risultato, il percorso inverso non deve esistere a runtime.

**API root consigliata:** mantenere le otto funzioni attuali, aggiungere `LinearFitResult` e `plot_linear_fit`; aggiungere `lin_fit_xy` soltanto dopo i gate scientifici. Il resto resta privato o nei rispettivi moduli. La comodità di import root non richiede side effect di stile o display.

### J2. Specifica normativa ideale di `lin_fit` 2.0

1. Stima esclusivamente `y=m*x+q`, intercetta libera, x considerate esatte; errori verticali indipendenti con media zero. Assunzioni gaussiane dichiarate per test/intervalli, non confuse con il calcolo algebrico.
2. `method` obbligatorio: `ols`, `wls`, `wls_relative`. Nessuna inferenza automatica del modello dalla presenza, shape o assenza delle σ. **Breaking.**
3. x/y reali 1D, stessa lunghezza, finiti, con conversione float64 documentata; σ scalari o 1D di pari lunghezza. Nessun flatten implicito, nessuna eliminazione automatica di NaN, nessuna modifica degli input.
4. OLS e WLS relativa richiedono N≥3 e stimano una scala globale con ν=N−2; WLS assoluta ammette N≥2 e non riscala la covarianza in base ai residui.
5. WLS richiede `sigma_y>0`; WLS relativa richiede `relative_sigma_y>0`, adimensionale. Parametri incompatibili sono errori. Terzo argomento di incertezza keyword-only. **Breaking.**
6. Lo stimatore minimizza esattamente il criterio lineare a pesi fissi entro l'accuratezza float64, attraverso formule analitiche centrate/scalate; non usa formule dei momenti globali soggette a cancellazione.
7. Residui e previsioni derivano dallo stesso stato locale conservato. Le trasformazioni di unità devono rispettare le proprietà G4 nei limiti della rappresentabilità degli input e degli output.
8. Restituisce un `LinearFitResult` numerico, con matrice di covarianza nell'ordine `(m,q)`, proprietà delle incertezze, residui, criterio pertinente, ν e informazioni sul modello; array protetti contro mutazioni accidentali.
9. `chi2/reduced_chi2/p_value` non vengono costruiti artificialmente fissando la scala a posteriori: sono assenti dove non applicabili. Per WLS ν=0, χ² è calcolabile ma ridotto e p-value sono assenti. Correlazione assente se varianze nulle. **Breaking.**
10. `predict` usa la forma locale stabile; `mean_std` rappresenta soltanto l'incertezza standard della media prevista. Nessuna implicita prediction band o confidenza simultanea.
11. Nessuna figura, salvataggio grafico, stampa, display, chiusura di figure o variazione globale di stile dalla chiamata di fit. `plot_linear_fit` è separata. **Breaking.**
12. `sigma_x`, correlazioni e vincoli non sono interpretati approssimativamente da questa funzione. Supporto x/y esplicito via `lin_fit_xy` validata; GLS e vincoli dichiarati fuori scope della prima 2.0. **Breaking per il vecchio `sigma_x`.**
13. Input invalidi producono eccezioni utili prima del calcolo; fallimenti numerici non producono un risultato apparentemente valido con NaN/inf. Perdite di rango e limiti di rappresentazione sono distinti da una grande incertezza fisicamente legittima.
14. `to_toml` conserva metodo, semantica, ordine dei parametri e stato necessario al contratto di export scelto, con schema 2 e campi non applicabili definiti. **Breaking per i parser del formato.**
15. La release è accettabile solo dopo regression test scientifici, proprietà di scala/traslazione, oracoli analitici e test degli artefatti installati; la precisione dei risultati stampati non è prova della loro correttezza.

Questa specifica preserva ciò che è già valido: piccola API, NumPy, formule verificabili, dataclass, diagnostiche assolute y-only e scrittura TOML atomica. I breaking change proposti servono a rendere esplicite le assunzioni e impedire risultati scientificamente fuorvianti.
