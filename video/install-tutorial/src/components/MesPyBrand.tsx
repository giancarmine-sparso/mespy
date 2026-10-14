import {Img, staticFile} from 'remotion';
export const MesPyBrand = ({width = 205}: {width?: number}) =>
  <Img src={staticFile('mespy-logo.svg')} style={{width, height: width * 84 / 306, objectFit: 'contain'}} />;
