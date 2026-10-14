import type {CSSProperties, ReactNode} from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
export const ramp = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, end], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
// Text stays fully opaque. A short positional entrance replaces text fades.
export const Entrance = ({children, at = 0, style}: {children: ReactNode; at?: number; style?: CSSProperties}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: frame-at, fps, config: {damping: 200}, durationInFrames: 15});
  if (frame < at) return null;
  return <div style={{transform: `translateY(${(1-s)*12}px)`, ...style}}>{children}</div>;
};
export const SceneTransition = Entrance;
