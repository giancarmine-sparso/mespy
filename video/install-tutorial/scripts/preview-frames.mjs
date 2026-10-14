import {bundle} from '@remotion/bundler';
import {openBrowser,selectComposition,renderStill} from '@remotion/renderer';
import {mkdir} from 'node:fs/promises';
await mkdir('out/qa/layout',{recursive:true});
const serveUrl=await bundle({entryPoint:'src/index.ts'});
const browser=await openBrowser('chrome');
try {
 for(const path of ['colab','local'])for(const language of ['en','it']){
  const id=`mespy-install-${path}-${language}`;
  const inputProps={path,language};
  const composition=await selectComposition({serveUrl,id,inputProps,puppeteerInstance:browser});
  for(const frame of [60,240,420,720,869])await renderStill({serveUrl,composition,inputProps,frame,output:`out/qa/layout/${id}-${frame}.png`,puppeteerInstance:browser});
  console.log(id);
 }
}finally{await browser.close({silent:true});}
