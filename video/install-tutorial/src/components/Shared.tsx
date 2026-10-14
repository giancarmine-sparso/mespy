import {interpolate, useCurrentFrame} from 'remotion';
import {theme} from '../theme';
import {ramp} from './SceneTransition';

export const Mouse = ({start, click, from, to}: {start: number; click: number; from: [number,number]; to: [number,number]}) => {
  const frame = useCurrentFrame();
  if (frame < start || frame > click+27) return null;
  const p = ramp(frame, start, click-5);
  const e = p*p*(3-2*p);
  const pulse = ramp(frame, click, click+20);
  return <div style={{position: 'absolute', left: interpolate(e,[0,1],[from[0],to[0]]), top: interpolate(e,[0,1],[from[1],to[1]]), opacity: 1-ramp(frame, click+15,click+27), pointerEvents: 'none'}}>
    {frame >= click && <div style={{position: 'absolute', width: 70, height: 70, left: -35, top: -35, borderRadius: '50%', border: `2px solid ${theme.orange}`, opacity: 1-pulse, transform: `scale(${0.4+pulse})`}} />}
    <svg width="31" height="39" viewBox="0 0 31 39"><path d="M2 2L3 31L10 24L17 36L23 33L16 21L27 20Z" fill={theme.ink} stroke={theme.bg} strokeWidth="2" /></svg>
  </div>;
};

export const Plot = () => {
  const frame = useCurrentFrame();
  const p = ramp(frame, 15, 65);
  return <svg width="100%" viewBox="0 0 600 320">
    {[70,130,190,250].map(y=><path key={y} d={`M50 ${y}H565`} stroke={theme.line} />)}
    {[80,180,280,380,480,565].map(x=><path key={x} d={`M${x} 35V275`} stroke={theme.line} />)}
    <path d="M50 35V275H565" fill="none" stroke="#737e81" />
    <path d="M75 251L550 58" stroke={theme.orange} strokeWidth="3" pathLength={1} strokeDasharray={1} strokeDashoffset={1-p} />
    {[[100,239],[172,220],[245,173],[320,163],[395,111],[477,94],[535,56]].map(([x,y],i)=><g key={x} opacity={ramp(frame,20+i*5,40+i*5)} stroke={theme.blue} fill={theme.blue}><path d={`M${x} ${y-18}V${y+18}M${x-5} ${y-18}h10M${x-5} ${y+18}h10`} /><rect x={x-4} y={y-4} width="8" height="8" /></g>)}
  </svg>;
};
