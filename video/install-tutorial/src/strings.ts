import {MESPY_VERSION, PY_VERSION} from './config';

// Every visible string lives here. Technical strings are shared verbatim.
export const commands = {
  colabInstall: '%pip install mespy',
  colabVerify: 'import mespy\nprint(mespy.__version__)',
  localCheck: 'python --version',
  localInstall: 'python -m pip install mespy',
  localVerify: 'python -c "import mespy; print(mespy.__version__)"',
} as const;
const technical = {
  badge: 'SIMULATED DEMO',
  colabName: 'Google Colab',
  address: 'colab.research.google.com',
  notebook: 'MesPy.ipynb',
  notebookMark: 'co',
  shellPrompt: '$ ',
  version: MESPY_VERSION,
  pythonVersion: `Python ${PY_VERSION}`,
  pipLines: ['Collecting mespy', 'Installing collected packages: mespy'],
  pipSuccess: `Successfully installed mespy-${MESPY_VERSION}`,
  platform: ['macOS/Linux: python3', 'Windows: py'],
  commands,
};
export const strings = {
  en: {
    ...technical,
    title: {colab: 'Install MesPy · Google Colab', local: 'Install MesPy · Local Python'},
    path: {colab: 'Google Colab', local: 'Local Python'},
    steps: {colab: ['Open', 'Install', 'Verify'], local: ['Check', 'Install', 'Verify']},
    open: 'Open colab.research.google.com and create a new notebook.',
    installColab: 'Type it in a code cell and press Run.',
    lookFor: 'Look for the line "Successfully installed mespy-…".',
    verifyColab: 'If you see a version number, MesPy is ready.',
    reset: 'Colab resets its runtime: run %pip install mespy again in every new session.',
    check: 'You need Python 3.12 or newer.',
    environment: 'Using conda or a venv? Activate it first.',
    verifyLocal: 'Version shown? MesPy is ready.',
    enter: 'Press Enter.',
    verifyAction: 'Run the version check.',
    ready: 'MesPy is ready.',
    next: 'Next: the examples below.',
    terminal: 'Terminal',
    platformTitle: 'PYTHON COMMAND',
    // Only essential menu labels are represented in this simplified mock.
    menu: ['File', 'Edit', 'View', 'Insert'],
    addCode: '+ Code', addText: '+ Text', newNotebook: '+ New notebook',
    run: 'Run',
  },
  it: {
    ...technical,
    badge: 'DEMO SIMULATA',
    commands: {
      ...commands,
      colabVerify: 'import mespy\nprint("MesPy è pronto.")',
      localVerify: 'python -c "import mespy; print(\'MesPy è pronto.\')"',
    },
    version: 'MesPy è pronto.',
    pipSuccess: 'Successfully installed mespy-2.0.0',
    title: {colab: 'Installa MesPy · Google Colab', local: 'Installa MesPy · Python in locale'},
    path: {colab: 'Google Colab', local: 'Python in locale'},
    steps: {colab: ['Apri', 'Installa', 'Verifica'], local: ['Controlla', 'Installa', 'Verifica']},
    open: 'Apri colab.research.google.com e crea un nuovo notebook.',
    installColab: 'Scrivilo in una cella di codice e premi Esegui.',
    lookFor: 'Cerca la riga "Successfully installed mespy-…".',
    verifyColab: 'Se compare il messaggio, MesPy è pronto.',
    reset: "Colab azzera l'ambiente: ripeti %pip install mespy a ogni nuova sessione.",
    check: 'Serve Python 3.12 o successivo.',
    environment: 'Usi conda o un venv? Attivalo prima.',
    verifyLocal: 'Vedi il messaggio? MesPy è pronto.',
    enter: 'Premi Invio.',
    verifyAction: 'Esegui il codice di verifica.',
    ready: 'MesPy è pronto.',
    next: 'Prossimo passo: gli esempi qui sotto.',
    terminal: 'Terminale',
    platformTitle: 'COMANDO PYTHON',
    // File is verified in Google's Italian welcome notebook; uncertain menus
    // are represented by neutral icons, not guessed Italian translations.
    menu: ['File'],
    addCode: '+ Codice', addText: '+ Testo', newNotebook: '+',
    run: 'Esegui',
  },
} as const;
export type Copy = (typeof strings)[keyof typeof strings];
