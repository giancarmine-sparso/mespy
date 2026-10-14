import {useCurrentFrame} from 'remotion';
import {theme} from '../theme';
import {timeline as t} from '../timeline';
import type {Copy} from '../strings';
import type {InstallPath} from '../config';
import {CodeWindow} from '../components/CodeWindow';
import {TerminalWindow} from '../components/TerminalWindow';
import {NotebookCell} from '../components/NotebookCell';
import {TypingAnimation} from '../components/TypingAnimation';
import {Mouse} from '../components/Shared';

export const PipOutput = ({copy}: {copy: Copy}) => {
  const f=useCurrentFrame();
  return <div style={{fontFamily: theme.mono, fontSize: 40, lineHeight: 1.45, marginTop: 14}}>
    {f>=t.pipCollect && <div style={{color: theme.muted}}>{copy.pipLines[0]}</div>}
    {f>=t.pipInstalling && <div style={{color: theme.muted}}>{copy.pipLines[1]}</div>}
    {f>=t.installResult && <div style={{color: theme.orange, borderLeft: `4px solid ${theme.orange}`, paddingLeft: 18, marginTop: 8}}>{copy.pipSuccess}</div>}
  </div>;
};

export const ColabWindow = ({copy, stage}: {copy: Copy; stage: number}) => {
  const f=useCurrentFrame();
  const blank=f>=t.notebookReady;
  return <div style={{position:'relative'}}>
    <CodeWindow title={blank ? copy.notebook : copy.colabName} style={{height:470}}>
      <div style={{height:58, display:'flex', alignItems:'center', padding:'0 30px', gap:34, fontSize:32, borderBottom:`1px solid ${theme.line}`}}>
        <span style={{color:theme.orange,fontWeight:700}}>{copy.notebookMark}</span>
        {copy.menu.map(item=><span key={item}>{item}</span>)}
        {copy.menu.length===1 && <span aria-hidden style={{display:'flex',gap:28,alignItems:'center'}}>{[0,1,2].map(i=><svg key={i} width="30" height="30" viewBox="0 0 30 30"><path d="M3 7h24M3 15h24M3 23h24" stroke={theme.ink} strokeWidth="2" /></svg>)}</span>}
        <span style={{marginLeft:'auto'}}>{copy.addCode}</span><span>{copy.addText}</span>
      </div>
      <div style={{padding:'22px 30px'}}>
        {!blank && <div>
          <div style={{fontFamily:theme.mono,fontSize:44,marginBottom:32}}>{copy.address}</div>
          <div style={{display:'inline-flex',alignItems:'center',justifyContent:'center',minWidth:170,height:74,padding:'0 26px',background:theme.orange,color:theme.bg,fontSize:40,borderRadius:4}}>{copy.newNotebook}</div>
        </div>}
        {blank && <>
          <NotebookCell code={copy.commands.colabInstall} start={t.installType} done={t.installResult} runLabel={copy.run} compact={stage===2}/>
          {stage===1 && <PipOutput copy={copy}/>}
          {stage===2 && <div style={{marginTop:18}}>
            <NotebookCell code={copy.commands.colabVerify} start={t.verifyType} done={t.verifyResult} runLabel={copy.run}/>
            {f>=t.verifyResult && <div style={{fontFamily:theme.mono,fontSize:48,color:theme.blue,marginLeft:220,marginTop:12}}>{copy.version}</div>}
          </div>}
        </>}
      </div>
    </CodeWindow>
    <Mouse start={t.notebookClick-25} click={t.notebookClick} from={[750,280]} to={[115,260]}/>
    <Mouse start={t.installRun-25} click={t.installRun} from={[750,270]} to={[76,188]}/>
    <Mouse start={t.verifyRun-25} click={t.verifyRun} from={[750,340]} to={[76,308]}/>
  </div>;
};
export const LocalWindow = ({copy, stage}: {copy: Copy; stage: number}) => {
  const f=useCurrentFrame();
  const command=stage===0 ? copy.commands.localCheck : stage===1 ? copy.commands.localInstall : copy.commands.localVerify;
  const start=stage===0 ? t.checkType : stage===1 ? t.installType : t.verifyType;
  return <TerminalWindow title={copy.terminal}>
    <div style={{whiteSpace:'pre'}}><span style={{color:theme.orange}}>{copy.shellPrompt}</span><TypingAnimation text={command} start={start}/></div>
    {stage===0 && f>=t.checkResult && <div style={{color:theme.blue,marginTop:26}}>{copy.pythonVersion}</div>}
    {stage===1 && <PipOutput copy={copy}/>}
    {stage===2 && f>=t.verifyResult && <div style={{color:theme.blue,marginTop:26,fontSize:48}}>{copy.version}</div>}
  </TerminalWindow>;
};
export const Workflow = ({copy,path,stage}: {copy:Copy;path:InstallPath;stage:number}) => <div style={{position:'absolute',left:90,right:90,top:435}}>{path==='colab' ? <ColabWindow copy={copy} stage={stage}/> : <LocalWindow copy={copy} stage={stage}/>}</div>;
