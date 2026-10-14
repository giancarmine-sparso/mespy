/* MesPy duck mascot: pixel frames only. Shared by the homepage duck
   (homepage-duck.js) and the guide sidebar station (guide-duck-station.js). */
window.mespyDuckFrames = (() => {
  // One char per logical pixel. Every frame shares the same size and water line
  // (row WATERLINE in homepage-duck.js), so switching frames never moves the
  // duck or the line.
  const FRAMES = {
    profilo: [ // side view, facing right
      '........oooo....',
      '.......oooooo...',
      '.......ooooeoo..', // e: eye
      '.......ooooooobb', // b: beak
      '.......ooooooob.',
      '........oooo....',
      'o.......oooo....',
      'oo....ooooooo...',
      'ooooooooooooooo.',
      'ooowwwwooooooooo', // w: wing
      '.oooooowwoooooo.', // WATERLINE
      '..ooooooooooooo.',
      '....oooooooooo..',
    ],
    treQuarti: [ // three-quarter view, turning towards the viewer
      '.......ooooo....',
      '......ooooooo...',
      '......ooeooeo...',
      '......oooobbbb..',
      '......ooooobb...',
      '.......ooooo....',
      '.o......oooo....',
      'oo....oooooooo..',
      'oooooooooooooooo',
      '.ooowwwwoooooooo',
      '.ooooowwwooooooo', // WATERLINE
      '..ooooooooooooo.',
      '...oooooooooooo.',
    ],
    fronte: [ // front view, wings at the sides
      '.....oooooo.....',
      '....oooooooo....',
      '....ooeooeoo....',
      '....oobbbboo....',
      '....oooooooo....',
      '.....oooooo.....',
      '......oooo......',
      '..oooooooooooo..',
      '.wwooooooooooww.',
      '.wwooooooooooww.',
      '..woooooooooow..', // WATERLINE
      '..oooooooooooo..',
      '....oooooooo....',
    ],
    salutoMeta: [ // viewer-left wing halfway up
      '.....oooooo.....',
      '....oooooooo....',
      '....ooeooeoo....',
      '....oobbbboo....',
      '.w..oooooooo....',
      'ww...oooooo.....',
      'ww....oooo......',
      '.wwooooooooooo..',
      '...ooooooooooww.',
      '...ooooooooooww.',
      '...oooooooooow..', // WATERLINE
      '..oooooooooooo..',
      '....oooooooo....',
    ],
    salutoSu: [ // viewer-left wing tip on the forehead, above the eye
      '.....oooooo.....',
      '....wwwooooo....',
      '..wwooeooeoo....',
      '.ww.oobbbboo....',
      'ww..oooooooo....',
      'ww...oooooo.....',
      '.ww...oooo......',
      '..wooooooooooo..',
      '...ooooooooooww.',
      '...ooooooooooww.',
      '...oooooooooow..', // WATERLINE
      '..oooooooooooo..',
      '....oooooooo....',
    ],
  };
  const PALETTE = {
    o: 'var(--mh-amber)',
    b: 'var(--mh-duck-beak)',
    e: 'black', // fixed, not theme-dependent
    w: 'var(--mh-duck-wing)',
  };
  return { FRAMES, PALETTE };
})();
