import {theme} from '../theme';
export const StepIndicator = ({steps, active, completed}: {steps: readonly string[]; active: number; completed: number}) =>
  <div style={{display: 'flex', gap: 48, alignItems: 'center'}}>{steps.map((step,i) =>
    <div key={step} style={{display: 'flex', alignItems: 'center', gap: 15, fontSize: 36, color: theme.ink}}>
      <span style={{width: 46, height: 46, display: 'grid', placeItems: 'center', fontFamily: theme.mono, fontSize: 32, background: i <= active ? theme.orange : theme.panel, color: i <= active ? theme.bg : theme.ink, border: `1px solid ${i <= active ? theme.orange : theme.muted}`}}>{i < completed ? '✓' : i+1}</span>{step}
    </div>)}</div>;
