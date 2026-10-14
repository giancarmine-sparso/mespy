import {useCurrentFrame} from 'remotion';
import {typingFrames} from '../timeline';
import {ramp} from './SceneTransition';
import {theme} from '../theme';
export const TypingAnimation = ({text, start}: {text: string; start: number}) => {
  const frame = useCurrentFrame();
  const duration = typingFrames(text);
  const count = Math.floor(ramp(frame,start,start+duration)*text.length);
  const cursor = frame >= start && frame < start+duration+8;
  return <span style={{whiteSpace: 'pre', color: theme.ink}}><span data-command={text}>{text.slice(0,count)}</span>{cursor && <span style={{color: theme.orange}}>▎</span>}</span>;
};
