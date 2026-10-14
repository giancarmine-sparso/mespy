import type {CSSProperties, ReactNode} from 'react';
import {theme} from '../theme';
export const CodeWindow = ({title, label, children, style}: {title: string; label?: string; children: ReactNode; style?: CSSProperties}) =>
  <div data-box style={{background: theme.panel, border: `1px solid ${theme.line}`, borderRadius: 10, overflow: 'hidden', boxShadow: '0 28px 60px #0004', ...style}}>
    <div style={{height: 68, borderBottom: `1px solid ${theme.line}`, padding: '0 30px', display: 'flex', alignItems: 'center', gap: 12, fontFamily: theme.mono, fontSize: 32, color: theme.ink}}>
      {[0,1,2].map(n => <span key={n} style={{width: 11, height: 11, borderRadius: 9, background: '#88908d'}} />)}
      <span style={{marginLeft: 20}}>{title}</span>{label && <span style={{marginLeft: 'auto', color: theme.blue}}>{label}</span>}
    </div>{children}
  </div>;
