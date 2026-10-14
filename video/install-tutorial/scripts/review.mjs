import {execFileSync} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import {RenderInternals} from '@remotion/renderer';
const ffmpeg=RenderInternals.getExecutablePath({type:'ffmpeg',indent:false,logLevel:'error',binariesDirectory:null});
const ffprobe=RenderInternals.getExecutablePath({type:'ffprobe',indent:false,logLevel:'error',binariesDirectory:null});
const results=[];
for(const path of ['colab','local']) for(const language of ['en','it']) {
 const id=`mespy-install-${path}-${language}`;
 const dir=`out/qa/${id}`;
 await mkdir(dir,{recursive:true});
 const info=JSON.parse(execFileSync(ffprobe,['-v','error','-count_frames','-show_streams','-show_format','-of','json',`out/${id}.mp4`],{encoding:'utf8'}));
 const v=info.streams.find(s=>s.codec_type==='video');
 if(info.streams.some(s=>s.codec_type==='audio')||v.width!==1920||v.height!==1080||v.codec_name!=='h264'||v.r_frame_rate!=='30/1'||Number(info.format.duration)>30||Number(v.nb_read_frames)!==870)throw new Error(`Bad media properties: ${id}`);
 // Decode actual MP4 frames at 0,2,...,28 seconds. Remotion's minimal
 // FFmpeg includes scale but not the select/fps filters, so seek explicitly.
 for(let i=0;i<15;i++) execFileSync(ffmpeg,['-hide_banner','-v','error','-xerror','-y','-ss',String(i*2),'-i',`out/${id}.mp4`,'-vf','scale=800:450','-frames:v','1',`${dir}/${String(i+1).padStart(2,'0')}.png`]);
 execFileSync(ffmpeg,['-hide_banner','-v','error','-y','-ss',String(869/30),'-i',`out/${id}.mp4`,'-vf','scale=800:450','-frames:v','1',`${dir}/final.png`]);
 const row={file:`${id}.mp4`,duration:Number(info.format.duration),width:v.width,height:v.height,codec:v.codec_name,fps:v.r_frame_rate,frames:Number(v.nb_read_frames),bytes:Number(info.format.size),audio:false,sampledSeconds:Array.from({length:15},(_,i)=>i*2)};
 results.push(row);console.log(JSON.stringify(row));
}
await writeFile('out/qa/media-report.json',JSON.stringify(results,null,2)+'\n');
