/* Python runs in this worker, never in a backend endpoint or the UI thread.
   Pin Python and all compiled wheels to one compatible Pyodide distribution. */
const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v0.29.4/full/';
let runtime;
let busy = false;
async function loadRuntime(id) {
  const stage = value => self.postMessage({ id, stage: value });
  stage('runtime');
  const { loadPyodide } = await import(`${PYODIDE_URL}pyodide.mjs`);
  const python = await loadPyodide({ indexURL: PYODIDE_URL });
  stage('packages');
  await python.loadPackage(['numpy', 'scipy', 'matplotlib', 'pandas', 'tomli-w']);
  const response = await fetch(new URL('./mespy-runtime.zip', import.meta.url));
  if (!response.ok) throw new Error(`MesPy archive: HTTP ${response.status}`);
  python.unpackArchive(await response.arrayBuffer(), 'zip', { extractDir: '/home/pyodide/mespy-homepage' });
  python.runPython(`
import os, sys
os.environ['MPLBACKEND'] = 'Agg'
sys.path.insert(0, '/home/pyodide/mespy-homepage')
from homepage_fit import execute_fit
`);
  return python;
}
self.onmessage = async ({ data }) => {
  if (busy) return;
  if (typeof data.code !== 'string' || data.code.length > 20000) {
    self.postMessage({id: data.id, result: {ok: false, code: 'size'}});
    return;
  }
  busy = true;
  let runner;
  try {
    runtime ??= loadRuntime(data.id);
    const python = await runtime;
    self.postMessage({ id: data.id, stage: 'execute' });
    runner = python.globals.get('execute_fit');
    const result = JSON.parse(runner(data.code));
    self.postMessage({ id: data.id, result });
  } catch (error) {
    runtime = undefined; // A retry can recover from a failed CDN/package load.
    self.postMessage({ id: data.id, error: String(error.message || error) });
  } finally {
    runner?.destroy();
    busy = false;
  }
};
