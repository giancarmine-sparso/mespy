# Clip di installazione MesPy

Quattro clip Remotion/React/TypeScript, **29 s, 1920×1080, 30 fps, H.264/yuv420p, senza audio**. Una sola timeline e un solo componente, parametrizzati con `path` e `language`. Stile, logo, Inter e Liberation Mono derivano dal video originale.

## File prodotti

In `out/`, per ciascuno dei nomi seguenti:

| Nome | Video | Poster del frame finale |
| --- | --- | --- |
| `mespy-install-colab-en` | `.mp4`, 29 s | `.png`, 1920×1080 |
| `mespy-install-colab-it` | `.mp4`, 29 s | `.png`, 1920×1080 |
| `mespy-install-local-en` | `.mp4`, 29 s | `.png`, 1920×1080 |
| `mespy-install-local-it` | `.mp4`, 29 s | `.png`, 1920×1080 |

I vecchi export da 75 secondi sono conservati in `out/legacy/`. Dipendenze, export e QA sono ignorati da Git; vanno copiati esplicitamente per la consegna. Nessuna modifica al sito o al package Python.

## Anteprima e render

Da questa directory, con Node.js 22 e npm:

```sh
npm ci
npx remotion browser ensure
npm run preview
```

Scegli una delle quattro composizioni `mespy-install-{colab|local}-{en|it}`. Tutte registrano lo stesso componente `Tutorial`; cambiano solo i parametri. Per produrre tutti e quattro gli MP4 e tutti e quattro i poster con un comando:

```sh
npm run render:all
```

Chromium deve poter avviarsi e il bundler deve poter aprire una porta locale. Il render usa due worker, asset locali e font inclusi nel progetto, senza risorse esterne. Le dipendenze e Chromium si scaricano solo durante il setup. FFmpeg/ffprobe sono quelli forniti da Remotion: non serve un encoder H.264 di sistema.

## Modifiche

- `src/strings.ts`: **tutti i testi**, dizionari `en`/`it` e comandi tecnici condivisi.
- `src/config.ts`: `MESPY_VERSION = '1.2.0'`, `PY_VERSION = '3.12.8'`, FPS, risoluzione, velocità di digitazione.
- `src/timeline.ts`: unica timeline, identica per percorsi e lingue.
- `src/Tutorial.tsx`: struttura, title/end card, box laterale e istruzioni.
- `src/scenes/Workflow.tsx`: notebook Colab e terminale.
- `src/components/`: finestre, celle, digitazione, step con spunte, transizioni, logo e motivi grafici.
- `src/theme.ts`: palette originale; grigio dei log reso più chiaro per il contrasto.

Animazioni deterministiche tramite `useCurrentFrame()`, `interpolate()` e `spring()`. Nessuna dissolvenza del testo: le entrate sono solo posizionali. Dimensione minima dei testi 32 px; corpo, log e note almeno 40 px; comandi 44 px. La barra con il timecode è stata rimossa.

| Tempo | Contenuto |
| --- | --- |
| 0–2,5 s | Title card |
| 2,5–9 s | Apri Colab / controlla Python |
| 9–16,5 s | Installa; esito evidenziato da 13 s |
| 16,5–27 s | Verifica; versione visibile da 22 s |
| 23–27 s | Nota sul reset di Colab, visibile 4 s |
| 27–29 s | End card; poster al frame 869 |

Digitazione a 18 caratteri/s. Pause dopo il completamento: apertura Colab 3 s, controllo Python oltre 4 s, installazione 3,5 s, verifica 5 s. Il box macOS/Linux/Windows è presente su tutti i frame della clip locale, comprese title/end card. I comandi rimangono quelli esatti richiesti con `python`; il box indica i nomi alternativi del comando.

## Verifica riproducibile

```sh
npm run typecheck
npm run check
npm run render:all
npm run review
```

`check` verifica i comandi carattere per carattere, la configurazione, la timeline condivisa, i tempi di lettura e le dimensioni minime dei font. `review` usa ffprobe e decodifica ogni MP4, estraendo i frame 0, 60, 120, …, 840, ridotti a **800×450**, oltre all'ultimo frame. Risultati in `out/qa/mespy-install-*/` e metadati in `out/qa/media-report.json`. Le tavole di controllo raggruppano tre frame a larghezza nativa di 800 px. `node scripts/preview-frames.mjs` produce invece gli still preliminari di layout.

## Compatibilità del package e output simulato

Le versioni mostrate sono i valori dimostrativi richiesti, non una registrazione di un'installazione reale. Il badge `SIMULATED DEMO` è visibile per tutta la durata; i log pip sono una ricostruzione semplificata.

**Discrepanza verificata nel repository:** `pyproject.toml` dichiara MesPy 2.0.0 e Python >=3.12; `src/mespy/__init__.py` non espone `__version__`. Pertanto i comandi di verifica richiesti sono sintatticamente validi ma, contro il package attuale, terminano con `AttributeError` invece di stampare la versione. Nei video sono riportati esattamente come richiesto. Prima della pubblicazione occorre esporre `mespy.__version__` nel package distribuito oppure concordare un diverso comando di verifica. Il package non è stato modificato da questo lavoro.

## Etichette Colab italiane

Il mock contiene `File`, `+ Codice`, `+ Testo` ed `Esegui`. `File` è confermato dal [notebook introduttivo ufficiale in italiano](https://colab.research.google.com/notebooks/welcome.ipynb?hl=it); le altre tre diciture seguono il testo richiesto. Non è stato possibile verificare direttamente la barra menu completa o la dicitura attuale del pulsante per creare un notebook: gli altri menu sono rappresentati da icone neutre e il pulsante da `+`, senza inventare traduzioni. La didascalia italiana spiega comunque di creare un nuovo notebook. Nessun link o CTA verso gli esempi è simulato come cliccabile.

Logo: copia invariata di `../../assets/brand/mespy-logo-horizontal-dark.svg`. Inter: pacchetto locale `@fontsource/inter` con licenza OFL; Liberation Mono: `public/fonts/` con relativa licenza.
