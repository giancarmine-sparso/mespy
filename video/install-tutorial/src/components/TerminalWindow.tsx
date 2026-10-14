import type {ReactNode} from 'react';
import {CodeWindow} from './CodeWindow';
import {theme} from '../theme';
export const TerminalWindow = ({children, title}: {children: ReactNode; title: string}) =>
  <CodeWindow title={title} style={{height: 470}}><div style={{padding: '32px 34px', fontFamily: theme.mono, fontSize: 44, lineHeight: 1.5}}>{children}</div></CodeWindow>;
