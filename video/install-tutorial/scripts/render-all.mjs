import {bundle} from '@remotion/bundler';
import {openBrowser, selectComposition, renderMedia, renderStill} from '@remotion/renderer';
import {mkdir} from 'node:fs/promises';
import './check.mjs';

await mkdir('out', {recursive:true});
const serveUrl=await bundle({entryPoint:'src/index.ts'});
const browser=await openBrowser('chrome');
try {
  for(const path of ['colab','local']) for(const language of ['en','it']) {
    const id=`mespy-install-${path}-${language}`;
    const inputProps={path,language};
    const composition=await selectComposition({serveUrl,id,inputProps,puppeteerInstance:browser});
    console.log(`Rendering ${id} (${composition.durationInFrames/composition.fps}s)`);
    let previous=-1;
    await renderMedia({serveUrl,composition,inputProps,puppeteerInstance:browser,outputLocation:`out/${id}.mp4`,codec:'h264',crf:18,pixelFormat:'yuv420p',muted:true,concurrency:2,onProgress:({progress})=>{const pct=Math.floor(progress*10)*10;if(pct!==previous){console.log(`${id}: ${pct}%`);previous=pct;}}});
    await renderStill({serveUrl,composition,inputProps,puppeteerInstance:browser,frame:composition.durationInFrames-1,output:`out/${id}.png`});
  }
} finally {await browser.close({silent:true});}
console.log('Four clips and four final-frame posters rendered. Run npm run review for decoded-frame QA.');
