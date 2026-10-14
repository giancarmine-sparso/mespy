/* Guide sidebar illustration: the MesPy duck, seen from behind, at a retro
   control station (GUIDE_PAGES "station" in conf.py). Decorative only: it is
   drawn into the empty [data-guide-station] block under the guide navigator
   and hidden whenever the sticky sidebar has no room left for it. */
(() => {
  const { svgEl, frameGroup } = window.mespyPixel;
  const { FRAMES, PALETTE: DUCK_PALETTE } = window.mespyDuckFrames;

  const UNIT = 3; // CSS px per logical pixel, the same scale as the homepage duck

  // One char per logical pixel; colours are the --gd-station-* variables in
  // guide-duck-station.css. Left monitor: a histogram; centre: a 1980s green
  // Unix terminal; right: a linear fit. Cables run from the monitors' backs
  // down to the floor, the tower and the power strip.
  const SCENE = [
    '................................................................',
    '......................hhhhhhhhhhhhhhhhhhhh......................', // h: casing top edge
    '.....................cccccccccccccccccccccc.....................', // c: casing
    '.....................ccSSSSSSSSSSSSSSSSSSccn....................', // S: terminal glass
    '....................rccSggSggggSgggSSSSSSccn....................', // g: phosphor text
    '....................rccSSSSSSSSSSSSSSSSSSccn....................',
    '....................rccSGGGSGGGGGSGGGGSSSccn....................', // G: dim phosphor
    '....hhhhhhhhhhhhhhh.rccSSSSSSSSSSSSSSSSSSccn.hhhhhhhhhhhhhhh....',
    '...ccccccccccccccccc.ccSGGSGGGGGGSGGSSSSScc.ccccccccccccccccc...',
    '...ccsssssssssssssccxccSSSSSSSSSSSSSSSSSScc.ccssssssssasssscc...', // s: screen glass
    '...ccssssssssbssssccxccSggSgggSggggggSSSSccuccsssssssssssAscc...', // b, B: data blue
    '...ccssssssbsbssssccxccSSSSSSSSSSSSSSSSSSccuccssssssasssAsscc...', // a, A: fit amber
    '...ccssssssbsbsbssccxccSGGGGSGGGGGGSGSSSSccuccsssssassAAssscc...',
    '...ccssssbsbsbsbssccxccSSSSSSSSSSSSSSSSSSccuccssssssAAssssscc...',
    '...ccssssbsbsbsbsbccxccSgSgSSSSSSSSSSSSSSccuccsssssAssssssscc...', // prompt, see CURSOR
    '...ccssbsbsbsbsbsbccxccccccccccccccccccccccuccsssaAsssssssscc...',
    '...ccssbsbsbsbsbsbcbxccccccccccccccccccccccuccsaAsssssssssscc...',
    '...ccsBBBBBBBBBBBsccxcCCCCCCCCCCCCCCCCCCCCcuccssssssssssssscc...', // C: casing shade
    '...cccccccccccccccccxx..CCCCCCCCCCCCCCCC....ccccccccccccccccc...',
    '...ccccccccccccccccc.x..CCkkkkkkkkkkkkCC....ccccccccccccccccc...', // k: vents
    '...cCCCMCCCCCCCCCCCc....CCkkkkkkkkkkkkCC....cCCCCCCCCCCCCCCCc...',
    '......M.x.CCCu..........CCCCCCCCCCCCCCCC..........rCCBBBBB......', // M: steam
    '.DDDDDmmmDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDuuuuuDDDDDD.', // D: desk back edge, m: mug
    '.dddddmmdddddddddddKyKyKyKyKyKyKyKyKyKyKyKyKKdddddddddddddddddd.', // d: desk, K, y: keyboard
    '.ddddddddddddddddddKKyKyKyKyKyKyKyKyKyKyKyKyKdddddddddddddddddd.',
    '.ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff.', // f: desk front, legs
    '.ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff.',
    '..ff....x....u.X...X........X.......n.......x..x..r.........ff..', // x, X, u, r, n: cables
    '..ff....x....u.X...X.....pppppppppppppp.....x.xx..r.........ff..', // p: stool seat
    '..ff....x....u.XX..X.....pppppppppppppp.....x.x.ccccccccc...ff..',
    '..ff....x....u..XXXX......XX...PP.....nnnn..xxx.RRRRRRRRR...ff..', // R: tower, P: stool stem
    '..ff....x....uu..XX....XXXX....PP........nn...x.RRkkkkkRR...ff..',
    '..ff....xx....uu......XX.......PP.........nnnnnnRRRRRRRRR...ff..',
    '..ff.....x.....uu...XXX........PP............rrnRRkkkkkRR...ff..',
    '..ff.....xx.....uuuXXu.........PP...r.......rr..RRRRRRRRR...ff..',
    '..ff......xx......XX.uu........PP...rrrrrrrrr...RRRRRRRRR...ff..',
    '..ff.......xx....XX...uuuuuuuuuPPuuuu...........RRRRRRRRR...ff..',
    '..ff........xxxxXXxxx..........PP...uuuuuuuuuuuuRRRRRRRRR...ff..',
    '..ff......XXXXXXX...xxxxxxxxx..PP...............RRRRRRRRR...ff..',
    '.....RRRRRRR...............PPPPPPPPPP...........................',
    'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF', // F: floor
  ];
  const v = (name) => `var(--gd-station-${name})`;
  const PALETTE = {
    h: v('case-top'), c: v('case'), C: v('case-shade'), k: v('vent'),
    s: v('glass'), S: v('terminal'), g: v('phosphor'), G: v('phosphor-dim'),
    b: v('blue'), B: v('blue-dim'), a: v('amber'), A: v('amber-dim'),
    D: v('desk-edge'), d: v('desk'), f: v('desk-front'), K: v('keyboard'), y: v('keys'),
    m: v('mug'), M: v('case-shade'), p: v('case'), P: v('case-shade'), R: v('tower'), F: v('floor'),
    x: v('cable'), X: v('cable-dark'), u: v('blue-dim'), r: v('amber-dim'), n: v('cable-green'),
  };
  // Blinking details drawn over the scene: [x, y, palette char, class suffix].
  const BLINKERS = [
    [28, 14, 'g', 'cursor'], // terminal cursor after the prompt
    [50, 35, 'g', 'led-a'], // tower LEDs
    [52, 35, 'a', 'led-b'],
    [5, 38, 'g', 'led-c'], // power strip
  ];

  // The repo's duck from behind: the front view with its face hidden, the head
  // turned slightly left so the beak tip shows, wings resting on the keyboard.
  const DUCK_AT = { x: 24, y: 15 };
  function rearView(rows) {
    const grid = rows.map((row) => [...row.replace(/[eb]/g, 'o')]);
    grid[3][2] = 'b';
    grid[3][3] = 'b';
    return grid.map((row) => row.join(''));
  }
  // Typing: lift one wing (the outer wing columns) by a logical pixel. A freed
  // cell stays body colour when the body continues below it.
  function liftWing(rows, side) {
    const cols = rows[0].length;
    const isWing = (x, y) => rows[y][x] === 'w' && (side === 'left' ? x < 3 : x >= cols - 3);
    const grid = rows.map((row) => [...row]);
    const wing = [];
    rows.forEach((row, y) => [...row].forEach((_, x) => { if (isWing(x, y)) wing.push([x, y]); }));
    for (const [x, y] of wing) grid[y][x] = rows[y + 1]?.[x] === 'o' ? 'o' : '.';
    for (const [x, y] of wing) grid[y - 1][x] = 'w';
    return grid.map((row) => row.join(''));
  }

  function buildScene() {
    const rear = rearView(FRAMES.fronte);
    const cols = SCENE[0].length;
    const svg = svgEl('svg', {
      viewBox: `0 0 ${cols} ${SCENE.length}`,
      width: cols * UNIT,
      height: SCENE.length * UNIT,
      'shape-rendering': 'crispEdges',
      'aria-hidden': 'true',
      focusable: 'false',
    });
    svg.append(frameGroup('gd-station-scene', SCENE, PALETTE));
    for (const [x, y, char, name] of BLINKERS) {
      const led = frameGroup(`gd-station-${name}`, [char], PALETTE);
      led.setAttribute('transform', `translate(${x} ${y})`);
      led.setAttribute('class', `gd-station__${name}`);
      svg.append(led);
    }
    [['a', liftWing(rear, 'left')], ['b', liftWing(rear, 'right')]].forEach(([key, rows]) => {
      const duck = frameGroup(`gd-station-duck-${key}`, rows, DUCK_PALETTE);
      duck.setAttribute('transform', `translate(${DUCK_AT.x} ${DUCK_AT.y})`);
      duck.setAttribute('class', `gd-station__duck-${key}`);
      svg.append(duck);
    });
    return svg;
  }

  function init() {
    const station = document.querySelector('[data-guide-station]');
    const aside = station && station.closest('.gd-aside');
    if (!aside) return;
    station.append(buildScene());

    // Show the station only when the navigator and the station both fit in
    // the sticky sidebar, so it never adds a scrollbar to the navigation.
    // Measured from the navigator alone: toggling the station cannot loop.
    const nav = aside.querySelector('[data-guide-nav]');
    const fit = () => {
      station.hidden = false;
      const room = parseFloat(getComputedStyle(aside).maxHeight) || Infinity;
      const used = (nav ? nav.offsetHeight : 0) + station.offsetHeight + parseFloat(getComputedStyle(station).marginTop);
      station.hidden = used > room;
    };
    fit();
    if (nav) new ResizeObserver(fit).observe(nav);
    window.addEventListener('resize', fit);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
