import {useCurrentFrame} from 'remotion';
import {theme} from '../theme';
import {TypingAnimation} from './TypingAnimation';
export const NotebookCell = ({code, start, done, runLabel, compact = false}: {code: string; start: number; done: number; runLabel: string; compact?: boolean}) => {
  const f = useCurrentFrame();
  return <div data-box style={{display: 'flex', alignItems: 'center', border: `1px solid ${f>=done ? '#657e74' : theme.line}`, background: '#151a1b', borderRadius: 5, padding: compact ? '12px 22px' : '15px 22px', gap: 26}}>
    <div style={{width: 170, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 12, color: f>=done ? theme.blue : theme.ink}}><span style={{width: 44, height: 44, borderRadius: '50%', border: '2px solid currentColor', display: 'grid', placeItems: 'center', fontSize: 32}}>{f>=done ? '✓' : '▶'}</span>{f<done && <span style={{fontSize: 32}}>{runLabel}</span>}</div>
    <div style={{fontFamily: theme.mono, fontSize: 44, lineHeight: 1.32}}><TypingAnimation text={code} start={start} /></div>
  </div>;
};
