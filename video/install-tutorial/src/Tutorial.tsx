import {AbsoluteFill, staticFile, useCurrentFrame} from 'remotion';
import {MesPyBrand} from './components/MesPyBrand';
import {SceneTransition} from './components/SceneTransition';
import {StepIndicator} from './components/StepIndicator';
import {Plot} from './components/Shared';
import {Workflow} from './scenes/Workflow';
import type {TutorialProps} from './config';
import {strings} from './strings';
import {timeline as t} from './timeline';
import {theme} from './theme';
import './style.css';

export const Tutorial = ({language,path}: TutorialProps) => {
  const frame=useCurrentFrame();
  const copy=strings[language];
  const title=frame<t.titleEnd;
  const end=frame>=t.endStart;
  const stage=frame<t.installStart ? 0 : frame<t.verifyStart ? 1 : 2;
  const completed=end ? 3 : frame>=t.verifyResult ? 3 : frame>=t.installResult ? 2 : frame>=(path==='colab' ? t.notebookReady : t.checkResult) ? 1 : 0;
  let caption: string=stage===0 ? (path==='colab' ? copy.open : copy.check) : stage===1 ? (path==='colab' ? copy.installColab : copy.environment) : copy.verifyAction;
  if(stage===2 && frame>=t.verifyResult) caption=path==='colab' ? copy.verifyColab : copy.verifyLocal;
  const footer=path==='colab' ? (stage===1 && frame>=t.installResult ? copy.lookFor : stage===2 && frame>=t.resetNote ? copy.reset : '') : (frame<t.verifyResult ? copy.enter : '');
  return <AbsoluteFill style={{background:theme.bg,color:theme.ink,fontFamily:theme.sans,fontSize:40}}>
    <style>{`@font-face {font-family:'MesPy Mono';src:url('${staticFile('fonts/LiberationMono-Regular.ttf')}') format('truetype');font-weight:400;}`}</style>
    <AbsoluteFill style={{backgroundImage:'linear-gradient(#ffffff03 1px,transparent 1px),linear-gradient(90deg,#ffffff03 1px,transparent 1px)',backgroundSize:'80px 80px'}}/>
    <div style={{position:'absolute',top:40,left:90,right:90,height:95,display:'flex',alignItems:'flex-start',justifyContent:'space-between',borderBottom:`1px solid ${theme.line}`}}>
      <MesPyBrand width={270}/><div style={{fontFamily:theme.mono,fontSize:34,color:theme.blue,border:`1px solid ${theme.line}`,padding:'12px 18px'}}>{copy.badge}</div>
    </div>
    {path==='local' && <div data-box style={{position:'absolute',right:90,top:165,width:535,border:`1px solid ${theme.line}`,background:theme.panel,padding:'20px 24px',zIndex:2}}>
      <div style={{fontFamily:theme.mono,fontSize:32,color:theme.orange,marginBottom:12}}>{copy.platformTitle}</div>
      {copy.platform.map(line=><div key={line} style={{fontSize:40,lineHeight:1.4,whiteSpace:'nowrap'}}>{line}</div>)}
    </div>}
    {title && <SceneTransition key="title"><div style={{position:'absolute',left:90,top:410,width:1220}}><h1 style={{fontSize:76,letterSpacing:-3,lineHeight:1.2,margin:0,fontWeight:600}}>{copy.title[path]}</h1><div style={{marginTop:65}}><StepIndicator steps={copy.steps[path]} active={-1} completed={0}/></div></div><div style={{position:'absolute',right:90,top:555,width:470}}><Plot/></div></SceneTransition>}
    {!title && !end && <>
      <SceneTransition key={`step-${stage}`} at={stage===0 ? t.titleEnd : stage===1 ? t.installStart : t.verifyStart}>
        <h1 style={{position:'absolute',left:90,top:170,fontSize:62,letterSpacing:-2,lineHeight:1.15,margin:0,fontWeight:600}}>{copy.path[path]}</h1>
        <div style={{position:'absolute',left:90,top:265}}><StepIndicator steps={copy.steps[path]} active={stage} completed={completed}/></div>
        <div data-box style={{position:'absolute',left:90,top:338,width:path==='local'?1120:1740,fontSize:40,lineHeight:1.2}}>{caption}</div>
        <Workflow copy={copy} path={path} stage={stage}/>
      </SceneTransition>
      {footer && <div data-box style={{position:'absolute',left:90,right:90,top:930,padding:stage===2 && path==='colab'?'13px 22px':'0',border:stage===2 && path==='colab'?`1px solid ${theme.orange}`:undefined,background:stage===2 && path==='colab'?theme.panel:undefined,fontSize:40,lineHeight:1.25,color:theme.ink}}>{footer}</div>}
    </>}
    {end && <SceneTransition key="end" at={t.endStart}><div style={{position:'absolute',left:90,top:420}}>
      <div style={{display:'flex',alignItems:'center',gap:28}}><span style={{display:'grid',placeItems:'center',width:78,height:78,borderRadius:'50%',border:`2px solid ${theme.blue}`,color:theme.blue,fontSize:54}}>✓</span><h1 style={{fontSize:82,letterSpacing:-3,lineHeight:1.1,margin:0,fontWeight:600}}>{copy.ready}</h1></div>
      <p style={{fontSize:46,margin:'36px 0 65px',lineHeight:1.3}}>{copy.next}</p>
      <StepIndicator steps={copy.steps[path]} active={2} completed={3}/>
    </div><div style={{position:'absolute',right:90,top:700,width:400}}><Plot/></div></SceneTransition>}
  </AbsoluteFill>;
};
