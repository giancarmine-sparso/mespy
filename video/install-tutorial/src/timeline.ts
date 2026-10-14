import {CHARS_PER_SECOND, FPS} from './config';

// One frame-based timeline for BOTH installation paths and BOTH languages.
// Title: 2.5 s; end card: 2 s. No completed step holds for less than 2 s.
export const timeline = {
  titleEnd: 75,
  checkType: 100,
  checkResult: 145,
  notebookClick: 165,
  notebookReady: 180,
  installStart: 270,
  installType: 295,
  installRun: 360,
  pipCollect: 367,
  pipInstalling: 379,
  installResult: 390,
  verifyStart: 495,
  verifyType: 520,
  verifyRun: 630,
  verifyResult: 660,
  resetNote: 690,
  endStart: 810,
} as const;
export const typingFrames = (text: string) => Math.ceil(text.length / CHARS_PER_SECOND * FPS);
