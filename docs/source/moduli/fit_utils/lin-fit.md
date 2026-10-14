(lin-fit-reference)=
# `mespy.lin_fit`

Adatta una retta a osservazioni appaiate, con incertezze assolute facoltative su `y` e incertezze indipendenti su `x`. La funzione restituisce i parametri stimati, le loro incertezze tipo, i residui e le informazioni diagnostiche in un `LinearFitResult`. Per impostazione predefinita crea anche una figura Matplotlib con due pannelli; l'esportazione su file deve essere richiesta esplicitamente.

La media stimata dal fit è

$$
\hat y(x) = m x + q,
$$

dove `slope` è $m$ e `intercept` è $q$. Per impostazione predefinita, il calcolo considera `x` esatto e gli errori di misura verticali indipendenti; il parametro facoltativo `sigma_x` aggiunge soltanto barre di errore orizzontali. Seleziona esplicitamente `x_error_method="iterate"` per propagare le incertezze orizzontali indipendenti mediante l'approssimazione della varianza efficace descritta sotto. In assenza di `sigma_y`, le stime delle incertezze presuppongono un'unica varianza verticale comune. Con `sigma_y`, ogni valore fornito è un'incertezza tipo assoluta per la rispettiva osservazione.

(lin-fit-signature)=
## Firma della funzione

```python
def lin_fit(
    x: ArrayLike,
    y: ArrayLike,
    sigma_y: ArrayLike | None = None,
    *,
    sigma_x: ArrayLike | None = None,
    x_error_method: XErrorMethod = "none",
    xlabel: str = "x",
    ylabel: str = "y",
    title: str | None = None,
    style: str | None = "mespy",
    output: str | Path | None = None,
    plot: bool = True,
    normalize_residuals: bool = False,
) -> LinearFitResult:
```

Importa la funzione con `from mespy import lin_fit`. Qui `ArrayLike` proviene da `numpy.typing`, `Path` da `pathlib`, e `LinearFitResult` e `XErrorMethod` da `mespy.fit_utils`. `XErrorMethod` è `Literal["none", "iterate"]`. Solo `x`, `y` e `sigma_y` possono essere passati come argomenti posizionali; tutti gli altri argomenti devono essere passati per nome.

(lin-fit-parameters)=
## Parametri

`x` — `ArrayLike`, obbligatorio
: Coordinate indipendenti, come vettore numerico reale monodimensionale non vuoto. Almeno due valori devono essere distinti **dopo la conversione a `float64`**. Sono ammesse coordinate ripetute; i dati in ingresso non devono necessariamente essere ordinati. La distinzione è verificata mediante uguaglianza esatta, senza tolleranza assoluta.

`y` — `ArrayLike`, obbligatorio
: Ordinate misurate, come vettore numerico reale monodimensionale non vuoto della stessa lunghezza di `x`. Sono richieste almeno **tre osservazioni** quando `sigma_y=None`, oppure **due osservazioni** quando vengono fornite le incertezze.

`sigma_y` — `ArrayLike | None`, valore predefinito `None`
: Incertezze tipo assolute su `y`, nelle stesse unità di `y`. Accetta uno scalare reale finito strettamente positivo (compreso un array numerico a zero dimensioni) o un vettore monodimensionale della stessa lunghezza di `x`. Uno scalare viene espanso in un vettore costante. Un vettore di un solo elemento non viene esteso automaticamente a un campione più lungo. `None` seleziona i minimi quadrati ordinari (OLS); fornire le incertezze seleziona i minimi quadrati pesati (WLS) con incertezze assolute. Questo argomento specifica incertezze tipo, non varianze o pesi.

`sigma_x` — `ArrayLike | None`, valore predefinito `None`
: Incertezze tipo indipendenti su `x`, nelle unità di `x`. Accetta uno scalare reale finito non negativo o un vettore monodimensionale della stessa lunghezza di `x`; uno scalare viene espanso. Zero indica una coordinata esatta. Con `x_error_method="none"`, queste incertezze forniscono soltanto barre orizzontali e non modificano parametri, covarianza o informazioni diagnostiche. Con `"iterate"`, sono richiesti sia `sigma_x` sia `sigma_y`.

`x_error_method` — `XErrorMethod`, valore predefinito `"none"`
: `"none"` calcola OLS o WLS con incertezze assolute considerando `x` esatto. `"iterate"` seleziona esplicitamente WLS con ripesatura iterativa e incertezze verticali efficaci. Altre stringhe sollevano `ValueError`; valori che non sono stringhe sollevano `TypeError`. Vedi [Propagazione delle incertezze orizzontali](#lin-fit-x-errors).

`xlabel` — `str`, valore predefinito `"x"`
: Etichetta dell'asse orizzontale condiviso, posta nel pannello dei residui. Usa `""` per non mostrare un'etichetta. `None` non è accettato. Viene validata anche quando `plot=False` e conservata nei metadati del grafico in TOML.

`ylabel` — `str`, valore predefinito `"y"`
: Etichetta verticale del pannello con dati e fit. Usa `""` per non mostrare un'etichetta. `None` non è accettato. Il pannello dei residui ha una propria etichetta generata automaticamente. Viene validata anche quando `plot=False` e conservata nei metadati del grafico in TOML.

`title` — `str | None`, valore predefinito `None`
: Titolo del pannello superiore. `None` lascia il titolo non impostato e lo omette dal TOML; una stringa vuota è accettata e conservata. Viene validato anche quando `plot=False`.

`style` — `str | None`, valore predefinito `"mespy"`
: Stile Matplotlib temporaneo usato per creare la figura e generare automaticamente un PDF. Accetta il nome di uno stile registrato (compresi `"report"`, `"mespy"` e `"column"` di MesPy), il nome di uno stile Matplotlib oppure un percorso, come stringa, a un file `.mplstyle`. `None` mantiene la configurazione attualmente attiva. Con `plot=False`, lo stile non viene risolto né applicato. Vedi [Integrazione dello stile](#lin-fit-style).

`output` — `str | Path | None`, valore predefinito `None`
: **Percorso base** dei file, per esempio `"results/spring"`, a cui vengono aggiunte le estensioni `.toml` e, quando `plot=True`, `.pdf`. Accetta percorsi relativi o assoluti. Le directory superiori mancanti vengono create. `None` disabilita l'esportazione automatica su file. Vedi [Esportazione su file](#lin-fit-export) per la validazione dei percorsi, il comportamento di sovrascrittura e le condizioni di errore.

`plot` — `bool`, valore predefinito `True`
: Crea la figura con due pannelli. `False` restituisce `figure=None`, non importa `matplotlib.pyplot` e salta la risoluzione dello stile e tutte le operazioni di disegno. Impedisce anche la generazione automatica del PDF, ma non l'esportazione TOML. Sono accettati soltanto valori Python `bool` o NumPy `bool_`; numeri e stringhe che risultano vere in un contesto booleano vengono rifiutati.

`normalize_residuals` — `bool`, valore predefinito `False`
: Normalizza i residui **soltanto nel pannello inferiore del grafico**, usando `sigma_y` in WLS con sole incertezze su y, le incertezze efficaci finali in WLS iterativo, oppure la dispersione stimata in OLS. Non modifica il fit, le informazioni diagnostiche o i residui restituiti. Non ha effetti grafici quando `plot=False`, ma viene comunque validato e registrato nel TOML. Accetta valori Python `bool` o NumPy `bool_`, non numeri o stringhe che risultano vere in un contesto booleano. Un fit OLS con dispersione stimata nulla non può essere rappresentato con questa opzione attiva.

### Contratto sui dati numerici in ingresso

Sono accettati liste numeriche, tuple, array NumPy e altri oggetti assimilabili ad array la cui rappresentazione NumPy ha un tipo di dati intero, intero senza segno o in virgola mobile. Anche le Series numeriche di pandas soddisfano questo contratto. I dati in ingresso vengono copiati in array `float64` indipendenti e non vengono modificati.

Tutti i valori devono rimanere finiti in `float64`. Scalari e array multidimensionali non sono validi per `x` e `y`; non vengono eseguiti appiattimento, filtraggio delle righe o rimozione dei valori mancanti. Sono rifiutati array con maschera, valori complessi (anche con parte immaginaria nulla), stringhe, array con tipo di dati oggetto e dati booleani. Sono rifiutati anche elementi booleani mescolati a valori numerici in liste o tuple Python. I generatori devono prima essere materializzati in un vettore numerico supportato.

(lin-fit-returns)=
## Valore restituito

Un [`LinearFitResult`](linear-fit-result.md), un oggetto risultato immutabile con la seguente interfaccia pubblica. I suoi campi non possono essere riassegnati; la figura Matplotlib rimane modificabile. I residui sono un array `float64` di sola lettura nell'ordine originale delle osservazioni.

| Attributo | Tipo | Significato |
| --- | --- | --- |
| `slope`, `intercept` | `float` | $m$ e $q$ stimati dal fit. |
| `slope_std`, `intercept_std` | `float` | Incertezze tipo dei parametri stimati. |
| `covariance` | `float` | Covarianza tra **pendenza e intercetta**, non una matrice di covarianza. |
| `correlation` | `float` o `None` | Correlazione dei parametri, `covariance / (slope_std * intercept_std)`, quando entrambe le incertezze tipo sono positive; altrimenti `None`. Non è una correlazione dei dati né una misura della bontà del fit. |
| `residuals` | `NDArray[np.float64]` | Residui verticali in unità fisiche, $r_i=y_i-\hat y(x_i)$, nelle unità di `y`. |
| `residual_std` | `float` o `None` | $\sqrt{\sum_i r_i^2/(N-2)}$ quando `dof > 0`; altrimenti `None`. |
| `estimated_sigma` | `float` o `None` | Proprietà di sola lettura uguale a `residual_std` per OLS; `None` per WLS. |
| `chi2`, `reduced_chi2`, `p_value` | `float` o `None` | Informazioni diagnostiche pesate, la cui disponibilità è descritta [sotto](#lin-fit-diagnostics). |
| `dof` | `int` | Gradi di libertà residui, $N-2$. |
| `fit_method` | `Literal["ols", "wls"]` | Metodo selezionato in base alla presenza o all'assenza di `sigma_y`. |
| `x_error_method` | `XErrorMethod` | `"none"` o `"iterate"`, che identifica il trattamento delle incertezze orizzontali. |
| `figure` | `Figure` o `None` | Figura Matplotlib generata; `None` quando `plot=False`. |

`result.predict(x_new)` valuta la media stimata dal fit. Uno scalare reale finito restituisce un `float` Python; un vettore monodimensionale restituisce un array `float64` indipendente. Sono accettati vettori vuoti. Si applicano le stesse restrizioni sui tipi numerici e sulla finitezza previste per i dati in ingresso del fit. La previsione usa la rappresentazione in coordinate locali conservata, che evita la perdita di accuratezza dovuta alla combinazione diretta di un grande `slope*x` con un'intercetta di segno opposto.

`result.to_toml(path)` esporta lo stesso documento numerico dell'esportazione TOML automatica e restituisce il `Path` del file scritto. Vedi [Esportazione TOML manuale](#lin-fit-manual-export). Il [riferimento dedicato al risultato](linear-fit-result.md) descrive ulteriori modalità di utilizzo dell'oggetto.

(lin-fit-behavior)=
## Comportamento del fit

### Senza incertezze: OLS

Quando `sigma_y=None`, la funzione minimizza la somma non pesata dei quadrati dei residui, $\mathrm{RSS}=\sum_i r_i^2$, e imposta `fit_method="ols"`. Emette un `UserWarning` che spiega che la dispersione viene stimata dai residui e che le informazioni diagnostiche basate sul chi quadro non sono disponibili.

La dispersione verticale comune viene stimata come

$$
s = \sqrt{\frac{\mathrm{RSS}}{N-2}}.
$$

Questo valore viene restituito sia come `residual_std` sia come `estimated_sigma`. La covarianza dei parametri corrisponde a $s^2(X^\mathsf{T}X)^{-1}$, dove la matrice del modello $X$ ha come colonne `x` e un vettore di uno; la sua diagonale fornisce i quadrati delle incertezze dei parametri. Queste stime delle incertezze presuppongono errori indipendenti con un'unica varianza comune e un modello lineare appropriato per la media. La funzione non verifica tali ipotesi.

Per stimare la dispersione sono necessarie almeno tre osservazioni. Se l'implementazione riproduce esattamente tutte le osservazioni su una retta, residui, dispersione stimata, incertezze dei parametri e covarianza sono nulli; `correlation` è `None`. Il riconoscimento di una retta esatta usa verifiche di uguaglianza anziché una tolleranza. La dispersione nulla impedisce la rappresentazione dei residui normalizzati, ma consente comunque i grafici ordinari e le chiamate con `plot=False`.

### Con incertezze: WLS con incertezze assolute

Quando viene fornito `sigma_y`, la funzione minimizza

$$
\chi^2 = \sum_i \left(\frac{r_i}{\sigma_{y,i}}\right)^2
$$

e imposta `fit_method="wls"`. I pesi sono proporzionali a $1/\sigma_{y,i}^2$. La covarianza dei parametri corrisponde a $(X^\mathsf{T}WX)^{-1}$ con $W=\operatorname{diag}(1/\sigma_{y,i}^2)$: viene mantenuta la scala **assoluta** delle incertezze fornite. La covarianza **non viene moltiplicata per il chi quadro ridotto** né per la dispersione misurata dei residui.

Un `sigma_y` costante produce la stessa retta ottimale di un fit non pesato, ma usa la scala fornita per le incertezze dei parametri. Moltiplicare ogni incertezza per un fattore positivo $a$ lascia invariati la retta e i residui in unità fisiche, moltiplica le incertezze tipo dei parametri per $a$ e la covarianza per $a^2$, e divide il chi quadro per $a^2$.

Sono sufficienti due osservazioni con coordinate distinte. Le incertezze dei parametri rimangono definite anche per una retta che riproduce esattamente i dati, perché derivano dalle incertezze di misura fornite.

(lin-fit-x-errors)=
### Propagazione delle incertezze orizzontali

Fornire soltanto `sigma_x` non modifica il calcolo. Con `x_error_method="none"`, aggiunge barre di errore orizzontali mentre OLS o WLS continua a considerare esatte le coordinate.

Con `x_error_method="iterate"`, sono richiesti entrambi gli argomenti delle incertezze. Un fit WLS con sole incertezze su y fornisce la pendenza iniziale. Ogni aggiornamento risolve WLS con

$$
\sigma_{\mathrm{eff},i}=\sqrt{\sigma_{y_i}^{2}+m^{2}\sigma_{x_i}^{2}}.
$$

L'implementazione riscala i termini prima della moltiplicazione e valuta la combinazione con `hypot`. La convergenza richiede una variazione relativa della pendenza al massimo pari a `1e-10`, normalizzata rispetto al maggiore tra i moduli della pendenza precedente e di quella aggiornata; due pendenze nulle sono considerate convergenti. Vengono tentati al massimo 100 aggiornamenti. La mancata convergenza solleva `RuntimeError` prima della creazione di grafici o dell'esportazione. Questi limiti sono impostazioni fisse dell'implementazione, non argomenti pubblici.

Al termine, i pesi efficaci vengono ricalcolati dalla pendenza restituita. L'intercetta viene ricalcolata come media pesata di `y - slope*x` in coordinate locali. Residui, covarianza e banda di incertezza usano questo stato finale.

Si tratta dell'approssimazione storica WLS con ripesatura iterativa, non del metodo York/ODR. Ogni aggiornamento mantiene fissi i pesi dipendenti dalla pendenza, quindi la convergenza non garantisce un minimo del criterio efficace. La covarianza e la banda della media usano i pesi finali mantenuti fissi. Il chi quadro e il relativo valore p storico hanno un'interpretazione statistica approssimata in questa modalità. `fit_method` rimane `"wls"` e `estimated_sigma` rimane `None`.

### Valutazione numerica

L'implementazione risolve i momenti pesati centrati e riscalati mediante potenze di due, conservando le coordinate locali per residui e previsioni. OLS e WLS con sole incertezze su y non eseguono iterazioni; la propagazione orizzontale facoltativa ripete questo risolutore WLS. Valori in ingresso finiti e distinti sono necessari, ma non garantiscono che tutte le grandezze numeriche richieste siano rappresentabili: scale estreme possono sollevare `FloatingPointError`, anche quando la normalizzazione delle incertezze ridurrebbe a zero un peso positivo.

(lin-fit-diagnostics)=
## Diagnostica statistica

| Grandezza | OLS | WLS con incertezze assolute |
| --- | --- | --- |
| `dof` | $N-2$, almeno 1 | $N-2$, eventualmente 0 |
| `residual_std` | Dispersione comune stimata $s$ | Scala descrittiva non pesata dei residui; `None` con zero gradi di libertà |
| `estimated_sigma` | Uguale a `residual_std` | Sempre `None` |
| `chi2` | `None` | Criterio pesato dei residui, anche quando `dof=0` |
| `reduced_chi2` | `None` | `chi2 / dof` se `dof > 0`; altrimenti `None` |
| `p_value` | `None` | Probabilità nella coda superiore del chi quadro se `dof > 0`; altrimenti `None` |

In WLS, `residual_std` viene comunque calcolato dai **residui non pesati in unità fisiche**. Non stima né sostituisce le incertezze di misura fornite e non entra nella covarianza dei parametri.

WLS iterativo calcola il criterio pesato usando le incertezze efficaci finali; la covarianza, la banda della media, il chi quadro e il valore p hanno l'interpretazione approssimata descritta in [Propagazione delle incertezze orizzontali](#lin-fit-x-errors).

Con gradi di libertà positivi, `p_value` viene calcolato con `scipy.stats.chi2.sf(chi2, dof)`. La sua interpretazione come misura della bontà del fit richiede errori verticali gaussiani indipendenti, incertezze tipo assolute corrette, `x` esatto e un modello lineare corretto per la media. Sotto queste ipotesi, il criterio minimizzato segue una distribuzione chi quadro con $N-2$ gradi di libertà e il chi quadro ridotto ha valore atteso 1. Un piccolo valore p nella coda superiore indica residui pesati insolitamente grandi sotto quel modello; non è la probabilità che il modello sia vero.

Con incertezze positive fornite, le informazioni diagnostiche WLS sono **definite numericamente** anche se quelle ipotesi statistiche non sono giustificate; in tal caso non ne consegue un'interpretazione come test del chi quadro. Con due osservazioni WLS, `chi2` viene calcolato, ma non ci sono gradi di libertà residui per un test di bontà del fit, quindi `reduced_chi2`, `p_value` e `residual_std` non sono disponibili. In OLS i tre campi del chi quadro sono **non disponibili (`None`)**, anziché zeri segnaposto o informazioni diagnostiche costruite dalla dispersione stimata.

(lin-fit-plotting)=
## Grafici e residui

`plot=True` è il valore predefinito. La figura generata ha due assi sovrapposti verticalmente che condividono `x`, con un rapporto tra le altezze di 3:1:

- **Pannello superiore:** osservazioni, media stimata dal fit sull'intervallo di `x` osservato e una banda che si estende di un'incertezza tipo sopra e sotto tale media. Le barre di errore verticali usano il `sigma_y` originale, se fornito; le barre orizzontali usano il `sigma_x` originale, se fornito.
- **Pannello inferiore:** residui in funzione di `x` con una linea tratteggiata di riferimento a zero. Per impostazione predefinita sono residui in unità fisiche, nelle unità di `y`. I marcatori dei residui WLS hanno barre di incertezza verticali da `sigma_y`, oppure dalle incertezze efficaci finali in WLS iterativo. Le barre orizzontali conservano il `sigma_x` originale; OLS non ha barre verticali.

La banda della media include la covarianza dei parametri. La sua semiampiezza corrisponde a

$$
\sigma_{\hat y}(x)=\sqrt{x^2\,\text{slope\_std}^2
+2x\,\text{covariance}+\text{intercept\_std}^2},
$$

valutata in coordinate locali per la stabilità numerica. È una **banda di un'incertezza tipo per la media stimata dal fit**, non un intervallo di previsione per nuove osservazioni né un intervallo a livello di confidenza fissato.

(lin-fit-normalization)=
### Normalizzazione dei residui

Imposta `normalize_residuals=True` per modificare il pannello inferiore:

| Fit | Residuo rappresentato | Barra di errore verticale rappresentata |
| --- | --- | --- |
| WLS | $r_i/\sigma_{y,i}$ | Semilunghezza unitaria |
| WLS iterativo | $r_i/\sigma_{\mathrm{eff},i}$ | Semilunghezza unitaria |
| OLS | $r_i/s$ | Nessuna |

Qui $s$ è `result.estimated_sigma`. Le etichette diventano `Residuals / σ_y` (con composizione matematica) o `Residuals / s`; altrimenti l'etichetta è `Residuals`. Sono semplici residui riscalati, non residui corretti per la leva statistica o studentizzati. Le barre WLS si riferiscono alle incertezze delle osservazioni; non sono le incertezze tipo dei residui del fit. I `residuals` restituiti e i valori dei residui esportati rimangono sempre in unità fisiche.

WLS iterativo usa l'etichetta `Residuals / σ_eff`. Le barre orizzontali rimangono nelle unità di `x` in ogni modalità e non vengono mai normalizzate.

Per OLS con `s=0`, `plot=True` insieme a `normalize_residuals=True` solleva `ValueError` prima che venga creata qualsiasi figura o directory di esportazione. Con `plot=False`, la normalizzazione non viene eseguita e questa combinazione è accettata.

(lin-fit-style)=
### Integrazione dello stile

Il valore predefinito `style="mespy"` usa lo stile per notebook registrato da MesPy. Sono supportati altri stili registrati (compresi `"report"` e `"column"`), stili Matplotlib standard e percorsi a file `.mplstyle`. `style=None` conserva le impostazioni attive. Ogni chiamata che genera un grafico usa un contesto di stile temporaneo e ripristina la configurazione Matplotlib precedente all'uscita.

Lo stile controlla dimensioni della figura, DPI, caratteri, griglia, spessori delle linee, dimensioni dei marcatori, estremità delle barre di errore, disposizione e impostazioni `savefig.*`. I dati usano il primo colore del ciclo di colori attivo; la retta del fit, la banda della media e la linea a zero dei residui usano il secondo colore, ripiegando sul primo se ne è disponibile soltanto uno. La composizione a due pannelli, l'opacità della banda (0.20) e la linea tratteggiata a zero sono stabilite dall'implementazione del grafico.

In un kernel IPython/Jupyter, le figure create dal contesto grafico vengono visualizzate esplicitamente e chiuse nel registro di pyplot per evitare duplicazioni della visualizzazione nel notebook. L'oggetto figura restituito rimane utilizzabile. In uno script ordinario, usa `matplotlib.pyplot.show()` quando desideri una visualizzazione interattiva.

(lin-fit-figure)=
### Accesso alla figura e personalizzazione

Accedi all'interfaccia Matplotlib supportata tramite `result.figure`; `result.figure.axes[0]` è l'asse del fit e `result.figure.axes[1]` è l'asse dei residui. Puoi modificarne etichette, limiti, legenda e oggetti grafici, oppure salvare la figura con `result.figure.savefig(...)`. Gestisci il caso `figure=None` se la creazione del grafico può essere disabilitata.

Personalizza l'aspetto al momento della creazione tramite un file di stile o un contesto Matplotlib attivo con `style=None`. Le modifiche successive al fit non aggiornano un PDF già esportato da `output`; salva separatamente la figura modificata. Le modifiche alla figura non cambiano neppure le opzioni originali del grafico conservate nel TOML.

(lin-fit-export)=
## Esportazione su file

L'esportazione automatica usa un **percorso base**, non un nome di file con un'estensione di formato:

| Argomenti | File generati automaticamente |
| --- | --- |
| `output=None`, qualunque valore di `plot` | Nessuno |
| `output="results/spring"`, `plot=True` | `results/spring.pdf` e `results/spring.toml` |
| `output="results/spring"`, `plot=False` | Solo `results/spring.toml` |

I percorsi relativi vengono risolti dalla directory di lavoro corrente. Le directory superiori mancanti vengono create automaticamente. I punti che fanno parte del nome base vengono conservati: `"results/run.v2"` produce `run.v2.toml` e, se viene generato il grafico, `run.v2.pdf`.

### Validazione dei percorsi e sostituzione

`output` deve essere uno `str` o un `pathlib.Path`. Non sono validi stringhe vuote, percorsi di directory, stringhe che terminano con il separatore di directory della piattaforma, componenti finali `.` o `..`, caratteri NUL incorporati e nomi base che terminano con un punto.

Il suffisso finale viene rifiutato, senza distinzione tra maiuscole e minuscole, se è una delle estensioni di file riconosciute elencate sotto. Fornisci un percorso base invece, per esempio, di `"spring.pdf"` o `"spring.toml"`.

`.pdf`, `.toml`, `.png`, `.svg`, `.svgz`, `.eps`, `.ps`, `.pgf`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.webp`, `.raw`, `.rgba`, `.csv`, `.tsv`, `.txt`, `.dat`, `.json`, `.xlsx`, `.ods`, `.gz`, `.bz2`, `.xz`, `.zip`, `.tar`.

Entrambi i file richiesti vengono preparati in una directory temporanea sul file system di destinazione prima di qualsiasi sostituzione finale. I file esistenti vengono sovrascritti automaticamente. Ogni sostituzione è atomica, ma **la coppia PDF/TOML non è una transazione**: il PDF viene sostituito per primo e un errore nella sostituzione del TOML può lasciare un nuovo PDF accanto al TOML precedente. Quando `plot=False`, un eventuale PDF esistente con quel percorso base rimane intatto.

Il PDF automatico viene generato nel contesto dello stile selezionato e ne rispetta le impostazioni `savefig.*`. Gli errori di generazione o di stile si propagano al chiamante. Gli errori di I/O durante l'esportazione sollevano `OSError` (o la sottoclasse corrispondente), conservando il numero di errore e identificando la destinazione finale richiesta. I file temporanei di preparazione vengono eliminati e, in caso di errore, le directory appena create vengono rimosse se vuote; il contenuto preesistente non viene rimosso.

(lin-fit-toml)=
### Contenuto TOML

I documenti TOML automatici usano la **versione 2 dello schema** in assenza di `sigma_x`. Con `sigma_x`, la **versione 3 dello schema** memorizza anche `[data].sigma_x` dopo l'espansione degli scalari e `[fit].x_error_method`, compreso `"none"` quando sono state soltanto visualizzate barre orizzontali. Entrambi gli schemi includono:

| Tabella | Contenuto |
| --- | --- |
| `[mespy]` | `schema_version`, `mespy_version` e `result_type="linear_fit"`. |
| `[data]` | Copie originali di `x` e `y`; `sigma_y`, se fornito, dopo l'espansione degli scalari. |
| `[fit]` | Metodo, pendenza, intercetta, le loro incertezze tipo, covarianza e correlazione quando definita. |
| `[diagnostics]` | Gradi di libertà e ogni informazione diagnostica definita, compreso `estimated_sigma` in OLS. |
| `[residuals]` | Array dei residui in unità fisiche nella chiave `values`. |
| `[plot]` | Opzioni originali `enabled`, `normalize_residuals`, `xlabel` e `ylabel`; `style` e `title` quando diversi da `None`. |

I numeri in virgola mobile vengono serializzati senza arrotondamenti di presentazione. I campi non definiti vengono omessi anziché memorizzati come valori nulli. I dati conservati consentono di ripetere il fit numerico. Gli oggetti figura, le successive modifiche alla figura e la configurazione Matplotlib completa non vengono serializzati; il contenuto di un file di stile non viene incorporato.

(lin-fit-manual-export)=
### Esportazione TOML manuale

`result.to_toml(path: str | Path) -> Path` scrive separatamente lo stesso documento con schema 2. Un suffisso mancante diventa `.toml`; un suffisso esistente viene conservato. Sovrascrive atomicamente un file esistente e restituisce il `Path` di destinazione.

A differenza di `output`, questo metodo **non crea le directory superiori mancanti** e non genera un PDF. Scrive i dati del fit conservati e le opzioni originali del grafico, anche se gli array in ingresso o la figura sono stati modificati nel frattempo.

(lin-fit-errors)=
## Avvisi ed eccezioni

| Categoria | Condizione che la attiva |
| --- | --- |
| `UserWarning` | Un fit OLS calcolato correttamente emette un avviso che indica che `sigma_y` non è stato fornito, la dispersione è stimata dai residui e le informazioni diagnostiche basate sul chi quadro non sono disponibili. Questo avviene anche con `plot=False`. |
| `TypeError` | Dati numerici in ingresso con maschera, complessi, booleani, stringhe o con tipo di dati oggetto; tipi incompatibili per opzioni booleane o etichette; un valore di `output` diverso da `str`, `Path` o `None`; argomenti per nome non supportati. |
| `ValueError` | Array numerici irregolari, conversione a `float64` fallita o valori non finiti; vettori vuoti o con forma errata; lunghezze diverse; osservazioni insufficienti; `x` costante dopo la conversione; `sigma_y` non positivo o `sigma_x` negativo; `x_error_method` non valido o incertezze mancanti per l'iterazione; percorsi base di esportazione non validi; rappresentazione normalizzata dei residui OLS con dispersione nulla. |
| `RuntimeError` | L'iterazione delle incertezze orizzontali non converge entro 100 aggiornamenti; sollevata prima di qualsiasi creazione di grafici o esportazione. |
| `FloatingPointError` | Deficienza numerica di rango, un peso WLS positivo normalizzato che diventa zero, oppure grandezze calcolate, come parametri, covarianza, residui, previsioni o valori della banda grafica, non rappresentabili in `float64`. |
| `OSError` e sottoclassi | Errori nella creazione delle directory di esportazione, nella preparazione temporanea, nella scrittura o nella sostituzione; anche un nome o file di stile Matplotlib non valido o mancante viene segnalato da Matplotlib come `OSError` quando la creazione del grafico è attiva. |

Le eccezioni di disegno e generazione del sistema grafico si propagano; in caso di errore, la funzione chiude la figura appena creata e ripristina il contesto dello stile. `plot=False` evita queste condizioni di errore grafiche. Restano valide le verifiche di dati, opzioni booleane, etichette e destinazione di esportazione.

(lin-fit-example)=
## Utilizzo minimo

```python
from mespy import lin_fit

result = lin_fit(
    [0.0, 1.0, 2.0, 3.0],
    [1.1, 2.8, 5.2, 6.9],
    sigma_y=0.2,
    xlabel="Time [s]",
    ylabel="Position [m]",
    output="results/linear_fit",
)
print(result.slope, result.slope_std)
print(result.predict(1.5))
```

Questo esegue WLS con incertezze assolute, crea la figura con fit e residui e scrive `results/linear_fit.pdf` e `results/linear_fit.toml`, creando `results/` se necessario. Per una chiamata esclusivamente numerica, usa `plot=False`; lascia `output=None` per evitare di scrivere file.

(lin-fit-see-also)=
## Vedi anche

- [`LinearFitResult`](linear-fit-result.md) — riferimento dell'oggetto risultato.
- [Esempi di fit lineare](../../examples/linear-fit.ipynb) — esempi svolti di fit.
- [Stile dei grafici](../../examples/plot-style.ipynb) — stili Matplotlib e personalizzazione delle figure.
- [Flusso di lavoro di base](../../examples/basic-workflow.ipynb) — un percorso completo di analisi delle misure.
