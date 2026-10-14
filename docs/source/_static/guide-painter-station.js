/* Guide sidebar illustration for Plot styling: the MesPy duck on a suspended
   platform, styling the page itself. The duck stands inside the platform,
   behind its guardrail, back to the reader, rolling orange straight onto the
   page with a roller held up in front of it in both wings. The job is under
   way: two earlier passes are dry on its right, the page to its left is
   still bare. No wall or panel is drawn: the page's own background shows
   everywhere the paint has not gone. Decorative only: drawn into the empty
   [data-guide-station="painter"] block under the guide navigator and hidden
   whenever the sticky sidebar has no room for it. */
(() => {
  const { svgEl, frameGroup } = window.mespyPixel;
  const { PALETTE: DUCK_PALETTE } = window.mespyDuckFrames;

  const UNIT = 3; // CSS px per logical pixel, the same scale as the duck station
  const COLS = 64;
  const ROWS = 38;

  // Hoist motor on each stirrup of the platform; the cable enters at its top.
  const HOIST = [
    'ccccc',
    'RRRRR',
    'RRRRR',
    'RRRRR',
    'RRRRR',
    '..c..',
  ];
  const HOISTS_AT = [5, 54]; // left column of each hoist; cables in their middle
  const HOIST_Y = 27;
  const DECK = [
    'h'.repeat(54), // deck: the floor the duck stands on
    'c'.repeat(54),
    '.' + 'C'.repeat(52) + '.', // underside
  ];
  const DECK_AT = { x: 5, y: 34 };
  // Front guardrail, between the reader and the duck: a top rail level with
  // the hoist caps (y = HOIST_Y), with its shadow, crossing the duck's body
  // so it reads as standing behind it, and two posts down to the deck either
  // side of the duck, leaving its legs and feet in full view.
  const RAILS = [
    { y: 27, char: 'h' }, // top rail
    { y: 28, char: 'C' }, // its shadow
  ];
  const RAIL_TOP = RAILS[0].y;
  const POSTS_X = [22, 41];

  // Open paint bucket on the deck, full of the orange: tall enough for the
  // rim and the paint to show above the top rail.
  const BUCKET = [
    '...xxx...', // wire handle
    '..x...x..',
    '.x.....x.',
    'hhhhhhhhh', // rim, seen a little from above
    'hPPPPPPsh', // s: glint on the paint
    'hhhhhhhhh',
    '.ccccccc.',
    '.ccccccc.',
    '.ccccccc.',
    '.ccccccc.',
    '.ccccccc.',
    '.ccccccc.',
    '..CCCCC..',
  ];
  const BUCKET_AT = { x: 12, y: DECK_AT.y - BUCKET.length };

  const v = (name) => `var(--gd-paint-${name})`;
  const PALETTE = {
    h: v('steel-top'), c: v('steel'), C: v('steel-shade'), R: v('hoist'), x: v('cable'),
    M: v('metal'), P: v('orange'), p: v('orange-shade'), s: v('orange-sheen'), b: v('led'),
    D: v('dry'), d: v('dry-shade'),
  };

  function layer(id, rows, palette, x, y) {
    const group = frameGroup(id, rows, palette);
    group.setAttribute('transform', `translate(${x} ${y})`);
    return group;
  }
  const vline = (char, length) => Array.from({ length }, () => char);

  // The MesPy duck as a rubber duck seen from behind, dressed as a house
  // painter: white dungarees (W, shade V) with the straps over the shoulders
  // and paint splashes (P), round head with a glossy highlight (O), orange
  // legs on webbed feet (B: their shaded inner edge). Both wings run up the
  // sides of the head and grip the pole, centred over it, from either side.
  // Same palette as the homepage frames plus the gloss, the whites, the
  // paint and the foot shade; not in homepage-duck-frames.js, which shares
  // one size across its frames.
  //
  // One pose per frame of the painting stroke, all the same size with the
  // feet on the bottom row (the deck). The whole duck moves: it crouches,
  // rises off its heels onto its toes, leans in (head sunk into the
  // shoulders, back foreshortened by a row) and stretches its wings up to
  // roll the paint up the page, then comes back down.
  const DUCK_POSES = {
    rest: [ // relaxed, legs a little bent, feet flat
      '.............',
      '.............',
      '.............',
      '.............',
      '.....w.w.....',
      '....w...w....',
      '...wooooow...',
      '..woOooooow..',
      '..wOoooooow..',
      '..w.ooooo.w..',
      '..woWoooWow..',
      '.owoWoooWowo.',
      '.oooWoooWooo.',
      '.ooWWWWWWWoo.',
      '.oWWPWWWWWWo.',
      '.WWWWWWWWWWW.',
      '.WWWWWWWWWWW.',
      '..WWWWWWWPW..',
      '...VWPWWWV...',
      '....WW.WW....',
      '.....b.b.....',
      '...bbB.Bbb...',
    ],
    crouch: [ // gathering itself: knees in, body down a row
      '.............',
      '.............',
      '.............',
      '.............',
      '.............',
      '.....w.w.....',
      '....w...w....',
      '...wooooow...',
      '..woOooooow..',
      '..wOoooooow..',
      '..w.ooooo.w..',
      '..woWoooWow..',
      '.owoWoooWowo.',
      '.oooWoooWooo.',
      '.ooWWWWWWWoo.',
      '.oWWPWWWWWWo.',
      '.WWWWWWWWWWW.',
      '.WWWWWWWWWWW.',
      '..WWWWWWWPW..',
      '...VWPWWWV...',
      '....WW.WW....',
      '...bbB.Bbb...',
    ],
    rise: [ // up on its feet, heels lifting, wings starting up
      '.............',
      '.............',
      '.....w.w.....',
      '....w...w....',
      '....w...w....',
      '...wooooow...',
      '..woOooooow..',
      '..wOoooooow..',
      '..w.ooooo.w..',
      '..woWoooWow..',
      '.owoWoooWowo.',
      '.oooWoooWooo.',
      '.ooWWWWWWWoo.',
      '.oWWPWWWWWWo.',
      '.WWWWWWWWWWW.',
      '.WWWWWWWWWWW.',
      '..WWWWWWWPW..',
      '...VWPWWWV...',
      '....WW.WW....',
      '.....b.b.....',
      '.....b.b.....',
      '....bB.Bb....',
    ],
    stretch: [ // on tiptoe, leaning in, the back foreshortened
      '.............',
      '.....w.w.....',
      '....w...w....',
      '....w...w....',
      '....w...w....',
      '....w...w....',
      '...wooooow...',
      '..woOooooow..',
      '..wOoooooow..',
      '..woWoooWow..',
      '.owoWoooWowo.',
      '.oooWoooWooo.',
      '.ooWWWWWWWoo.',
      '.oWWPWWWWWWo.',
      '.WWWWWWWWWWW.',
      '..WWWWWWWPW..',
      '...VWPWWWV...',
      '....WW.WW....',
      '.....b.b.....',
      '.....b.b.....',
      '.....b.b.....',
      '....b...b....',
    ],
    push: [ // roller at the top of the stroke, wings at full stretch
      '.....w.w.....',
      '....w...w....',
      '....w...w....',
      '....w...w....',
      '....w...w....',
      '....w...w....',
      '...wooooow...',
      '..woOooooow..',
      '..wOoooooow..',
      '..woWoooWow..',
      '.owoWoooWowo.',
      '.oooWoooWooo.',
      '.ooWWWWWWWoo.',
      '.oWWPWWWWWWo.',
      '.WWWWWWWWWWW.',
      '..WWWWWWWPW..',
      '...VWPWWWV...',
      '....WW.WW....',
      '.....b.b.....',
      '.....b.b.....',
      '.....b.b.....',
      '....b...b....',
    ],
    lower: [ // coming down off its toes
      '.............',
      '.............',
      '.....w.w.....',
      '....w...w....',
      '....w...w....',
      '....w...w....',
      '....w...w....',
      '...wooooow...',
      '..woOooooow..',
      '..wOoooooow..',
      '..woWoooWow..',
      '.owoWoooWowo.',
      '.oooWoooWooo.',
      '.ooWWWWWWWoo.',
      '.oWWPWWWWWWo.',
      '.WWWWWWWWWWW.',
      '..WWWWWWWPW..',
      '...VWPWWWV...',
      '....WW.WW....',
      '.....b.b.....',
      '.....b.b.....',
      '....bB.Bb....',
    ],
    settle: [ // back on flat feet, wings almost home
      '.............',
      '.............',
      '.............',
      '.....w.w.....',
      '....w...w....',
      '....w...w....',
      '...wooooow...',
      '..woOooooow..',
      '..wOoooooow..',
      '..w.ooooo.w..',
      '..woWoooWow..',
      '.owoWoooWowo.',
      '.oooWoooWooo.',
      '.ooWWWWWWWoo.',
      '.oWWPWWWWWWo.',
      '.WWWWWWWWWWW.',
      '.WWWWWWWWWWW.',
      '..WWWWWWWPW..',
      '...VWPWWWV...',
      '....WW.WW....',
      '.....b.b.....',
      '...bbB.Bbb...',
    ],
  };
  // [pose, ms]: a pause at rest and at the top of the stroke.
  const TIMELINE = [
    ['rest', 900], ['crouch', 140], ['rise', 110], ['stretch', 110],
    ['push', 520], ['lower', 130], ['settle', 130],
  ];
  const DUCK_AT = { x: 25, y: DECK_AT.y - DUCK_POSES.rest.length };
  const POLE_COL = 6; // the duck's middle column, between the wing tips
  const POLE_X = DUCK_AT.x + POLE_COL;
  // The roller follows the wing tips (each pose's top wing row, relative to
  // the rest pose); the pole runs down behind the head, as far as the pose
  // with the tips highest above the head needs.
  const tipRow = (rows) => rows.findIndex((row) => row.includes('w'));
  const headRow = (rows) => rows.findIndex((row) => row[POLE_COL] === 'o');
  const REST_TIP = tipRow(DUCK_POSES.rest);
  const RIG_DY = Object.fromEntries(
    Object.entries(DUCK_POSES).map(([name, rows]) => [name, tipRow(rows) - REST_TIP]),
  );
  const TRAVEL = -Math.min(...Object.values(RIG_DY)); // rows the roller climbs
  const POLE_END = DUCK_AT.y + Math.max(
    ...Object.entries(DUCK_POSES).map(([name, rows]) => headRow(rows) + 1 - RIG_DY[name]),
  );
  // Each pose gets a dark contour in the page colour (K): invisible on the
  // bare page, it keeps the amber duck apart from the amber paint behind it.
  const outline = (rows) => rows.map((row, y) => [...row].map((char, x) => (
    char === '.' && [[y - 1, x], [y + 1, x], [y, x - 1], [y, x + 1]]
      .some(([j, i]) => rows[j] && rows[j][i] && rows[j][i] !== '.') ? 'K' : '.'
  )).join(''));
  const DUCK_COLOURS = {
    ...DUCK_PALETTE,
    O: 'var(--gd-paint-gloss)',
    W: 'var(--gd-paint-whites)', V: 'var(--gd-paint-whites-shade)',
    P: 'var(--gd-paint-orange)', B: 'var(--gd-paint-feet-shade)',
    K: 'var(--mh-bg)',
  };

  // Paint roller held up in front of the duck, centred on it: a grey nap
  // soaked with paint along the edge touching the page, end caps, and a
  // yoke from both caps into the pole.
  const ROLLER = [
    '.hhhhhhh.', // nap, h: lit, c: shaded
    'McccccccM', // M: frame
    'MPPPPPPPM', // P: the paint where nap meets page
    '.MM...MM.',
    '...MMM...',
  ];
  // Rest pose: two rows of pole show between the yoke and the wing tips.
  const ROLLER_AT = { x: POLE_X - 4, y: DUCK_AT.y + REST_TIP - 2 - ROLLER.length };
  const NAP_X = ROLLER_AT.x + 1;

  // The paint: every pass runs from the top the roller reaches down to the
  // guardrail, solid at the top and streaking out lower down (p: thinner
  // paint). The current pass is under the roller, mostly behind the duck,
  // fresh and bright; two earlier ones, already dry and duller (D, d), are
  // to its right, a column of bare page between passes. The page to the
  // duck's left is still to do.
  const PAINT_TOP = ROLLER_AT.y + 2 - TRAVEL;
  const pass = ({ drips, dry }) => {
    const rows = [...vline('PPPPPPP', RAIL_TOP - PAINT_TOP - drips.length), ...drips];
    return dry ? rows.map((row) => row.replace(/P/g, 'D').replace(/p/g, 'd')) : rows;
  };
  const PASSES = [
    { x: NAP_X, drips: ['PPpPPPp', 'PPpPPPp', 'PppPPpp', 'pp.pPp.', 'p..p.p.'] }, // under way
    { x: NAP_X + 8, dry: true, drips: ['PPPPpPP', 'pPPPpPp', '.pPp.p.', '.p.p...', '...p...'] },
    {
      x: NAP_X + 16, dry: true, // the first pass of the job
      drips: ['PPPPPpP', 'PPpPPpP', 'PpPPpPp', 'p.pPp.P', '..pPp.p', '..p.p..', '..p....'],
    },
  ];

  function buildScene() {
    const svg = svgEl('svg', {
      viewBox: `0 0 ${COLS} ${ROWS}`,
      width: COLS * UNIT,
      height: ROWS * UNIT,
      'shape-rendering': 'crispEdges',
      'aria-hidden': 'true',
      focusable: 'false',
    });
    const [left, right] = HOISTS_AT;
    const poleTop = ROLLER_AT.y + ROLLER.length;
    // Every pose, and its contour, drawn once in <defs>; the duck shows one
    // pair through two <use>s.
    const defs = svgEl('defs', {});
    for (const [name, rows] of Object.entries(DUCK_POSES)) {
      defs.append(
        frameGroup(`gd-paint-pose-${name}`, rows, DUCK_COLOURS),
        frameGroup(`gd-paint-contour-${name}`, outline(rows), DUCK_COLOURS),
      );
    }
    const at = `translate(${DUCK_AT.x} ${DUCK_AT.y})`;
    const duck = svgEl('use', { id: 'gd-paint-duck', transform: at });
    const contour = svgEl('use', { id: 'gd-paint-duck-contour', transform: at });
    // Roller, nap and pole move together, whole rows at a time, with the
    // wing tips; the pole ends behind the duck's head.
    const naps = [
      layer('gd-paint-nap-0', ['.p.p.p.'], PALETTE, NAP_X, ROLLER_AT.y + 1),
      layer('gd-paint-nap-1', ['p.p.p.p'], PALETTE, NAP_X, ROLLER_AT.y + 1),
    ];
    const rig = svgEl('g', { id: 'gd-paint-rig' });
    rig.append(
      layer('gd-paint-roller', ROLLER, PALETTE, ROLLER_AT.x, ROLLER_AT.y),
      ...naps,
      layer('gd-paint-pole', vline('M', POLE_END - poleTop), PALETTE, POLE_X, poleTop),
    );
    const led = layer('gd-paint-led', ['b'], PALETTE, right + 1, HOIST_Y + 2);
    led.setAttribute('class', 'gd-station__led');
    svg.append(
      defs,
      // Back to front: the paint on the page, the duck's contour, cables,
      // roller and pole (over the contour, under the duck), what stands on
      // the deck, then the guardrail, hoists and deck in front.
      ...PASSES.map((paint, i) => layer(`gd-paint-pass-${i}`, pass(paint), PALETTE, paint.x, PAINT_TOP)),
      contour,
      layer('gd-paint-cable-0', vline('x', HOIST_Y), PALETTE, left + 2, 0),
      layer('gd-paint-cable-1', vline('x', HOIST_Y), PALETTE, right + 2, 0),
      rig,
      layer('gd-paint-bucket', BUCKET, PALETTE, BUCKET_AT.x, BUCKET_AT.y),
      duck,
      ...POSTS_X.map((x, i) => layer(`gd-paint-post-${i}`, vline('c', DECK_AT.y - RAIL_TOP - 1), PALETTE, x, RAIL_TOP + 1)),
      ...RAILS.map(({ y, char }, i) => layer(`gd-paint-rail-${i}`, [char.repeat(right - left - 5)], PALETTE, left + 5, y)),
      layer('gd-paint-hoist-0', HOIST, PALETTE, left, HOIST_Y),
      layer('gd-paint-hoist-1', HOIST, PALETTE, right, HOIST_Y),
      layer('gd-paint-deck', DECK, PALETTE, DECK_AT.x, DECK_AT.y),
      led,
    );
    // Show a pose: the duck's frame and contour, the roller at its wing
    // tips, and the nap pattern turned whenever the roller moves.
    let nap = 0;
    let dy = 0;
    const show = (name) => {
      duck.setAttribute('href', `#gd-paint-pose-${name}`);
      contour.setAttribute('href', `#gd-paint-contour-${name}`);
      if (RIG_DY[name] !== dy) nap = 1 - nap;
      dy = RIG_DY[name];
      rig.setAttribute('transform', `translate(0 ${dy})`);
      naps.forEach((group, i) => group.setAttribute('visibility', i === nap ? 'visible' : 'hidden'));
    };
    show('rest');
    return { svg, show };
  }

  function init() {
    const station = document.querySelector('[data-guide-station="painter"]');
    const aside = station && station.closest('.gd-aside');
    if (!aside) return;
    const scene = buildScene();
    station.append(scene.svg);

    // The stroke plays only while the scene is on screen and the tab is
    // visible; with reduced motion the duck stays in its rest pose.
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let onScreen = false;
    let step = 0;
    let timer = 0;
    const shouldRun = () => onScreen && !station.hidden && !document.hidden && !reducedMotion.matches;
    const advance = () => {
      timer = 0;
      step = (step + 1) % TIMELINE.length;
      scene.show(TIMELINE[step][0]);
      sync();
    };
    function sync() {
      if (shouldRun()) {
        if (!timer) timer = setTimeout(advance, TIMELINE[step][1]);
        return;
      }
      clearTimeout(timer);
      timer = 0;
      if (reducedMotion.matches && step) {
        step = 0;
        scene.show(TIMELINE[0][0]);
      }
    }

    // Same rule as the duck station: show the scene only when it fits in the
    // sticky sidebar under the navigator, so it never adds a scrollbar.
    const nav = aside.querySelector('[data-guide-nav]');
    const fit = () => {
      station.hidden = false;
      const room = parseFloat(getComputedStyle(aside).maxHeight) || Infinity;
      const used = (nav ? nav.offsetHeight : 0) + station.offsetHeight + parseFloat(getComputedStyle(station).marginTop);
      station.hidden = used > room;
      sync();
    };
    fit();
    if (nav) new ResizeObserver(fit).observe(nav);
    window.addEventListener('resize', fit);
    new IntersectionObserver(([entry]) => {
      onScreen = entry.isIntersecting;
      sync();
    }).observe(station);
    document.addEventListener('visibilitychange', sync);
    reducedMotion.addEventListener('change', sync);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
