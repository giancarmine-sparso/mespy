import ts from 'typescript';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {createRequire} from 'node:module';
import {resolve} from 'node:path';
mkdirSync('out/qa/compiled',{recursive:true});
for(const file of ['config','strings','timeline']) {
  const source=readFileSync(`src/${file}.ts`,'utf8');
  writeFileSync(`out/qa/compiled/${file}.js`,ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText);
}
const require=createRequire(import.meta.url);
const {commands,strings}=require(resolve('out/qa/compiled/strings.js'));
const config=require(resolve('out/qa/compiled/config.js'));
const {timeline:t,typingFrames}=require(resolve('out/qa/compiled/timeline.js'));
assert.deepEqual(commands,{
 colabInstall:'%pip install mespy',
 colabVerify:'import mespy\nprint(mespy.__version__)',
 localCheck:'python --version',
 localInstall:'python -m pip install mespy',
 localVerify:'python -c "import mespy; print(mespy.__version__)"',
});
assert.match(config.MESPY_VERSION,/^\d+\.\d+\.\d+$/);assert.match(config.PY_VERSION,/^\d+\.\d+\.\d+$/);
assert.equal(config.FPS,30);assert.equal(config.WIDTH,1920);assert.equal(config.HEIGHT,1080);
assert.ok(config.DURATION/config.FPS<=30);assert.ok(t.titleEnd/config.FPS<=3);assert.ok((config.DURATION-t.endStart)/config.FPS<=2);
for(const [end,next] of [[t.notebookReady,t.installStart],[t.checkResult,t.installStart],[t.installResult,t.verifyStart],[t.verifyResult,t.endStart]]) assert.ok(next-end>=60);
assert.ok(t.endStart-t.resetNote>=90);
for(const [command,start,run] of [[commands.localCheck,t.checkType,t.checkResult],[commands.colabInstall,t.installType,t.installRun],[commands.localInstall,t.installType,t.installRun],[commands.colabVerify,t.verifyType,t.verifyRun],[commands.localVerify,t.verifyType,t.verifyRun]]) assert.ok(start+typingFrames(command)<run);
assert.deepEqual(strings.en.commands,strings.it.commands);
assert.equal(strings.en.version,config.MESPY_VERSION);assert.equal(strings.it.version,config.MESPY_VERSION);
function checkFonts(dir){for(const entry of readdirSync(dir,{withFileTypes:true})){const file=`${dir}/${entry.name}`;if(entry.isDirectory())checkFonts(file);else if(file.endsWith('.tsx')){for(const match of readFileSync(file,'utf8').matchAll(/fontSize:\s*(\d+)/g))assert.ok(Number(match[1])>=32,`${file}: font below 32 px`);}}}
checkFonts('src');
console.log('PASS: exact commands, demo config, identical language timelines, 18 chars/s, holds, duration, minimum font sizes.');
