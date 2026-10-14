import {Composition} from 'remotion';
import {Tutorial} from './Tutorial';
import {DURATION,FPS,WIDTH,HEIGHT, type InstallPath, type Language} from './config';
export const Root = () => <>{(['colab','local'] as InstallPath[]).flatMap(path=>(['en','it'] as Language[]).map(language=><Composition key={`${path}-${language}`} id={`mespy-install-${path}-${language}`} component={Tutorial} defaultProps={{language,path}} durationInFrames={DURATION} fps={FPS} width={WIDTH} height={HEIGHT}/>))}</>;
