/* Guide sidebar illustration for Linear fit: a capybara with a mandarin on its
   head riding a fitted line, y = mx + q. It slides down the line, naps at the
   bottom, turns round and climbs back up, forever. The line never moves and
   the capybara never leaves it: every frame is sheared onto the line's own
   pixel staircase, so its feet always rest on the fit. Decorative only: drawn
   into the empty [data-guide-station="capybara"] block under the guide
   navigator and hidden whenever the sticky sidebar has no room for it. */
(() => {
  const { svgEl, frameGroup } = window.mespyPixel;

  const UNIT = 3; // CSS px per logical pixel, the same scale as the other stations
  const COLS = 74;
  const ROWS = 42;

  // The fit, descending left to right: one row down every RUN columns. The
  // capybara is placed on the same staircase, so it cannot drift off it.
  const LINE = { x0: 1, x1: 72, y0: 18 };
  const RUN = 3;
  const lineY = (x) => LINE.y0 + Math.floor((x - LINE.x0) / RUN);
  // Data points around the fit: [column, rows from the line]. 2x2 pixels.
  const POINTS = [[9, -3], [27, 2], [45, -3], [62, 2]];

  // The capybara, facing right, level: o outline, b coat, l lit back,
  // d shade, s snout, e eye; a mandarin (f, F lit, r shade) with its leaf (g).
  const BODY = [
    '.................g....',
    '...............oogo...',
    '....oooooo..o.offFFo..',
    '..oolllllloodoffffFo..',
    '.obbbbbbbbbbbborrrroo.',
    'obbbbbbbbbbbdbbbbbbbbo',
    'obbbbbbbbbbbdbbbbebbso',
    'obbbbbbbbbbdbbbbbbbsso',
    'obbbbbbbbbbdbbbbbbsoso',
    'odbbbbbbbbbdbbbbbbssso',
    '.oddbbbbbbbbddbbbbooo.',
    '..oddddddddddddddo....',
  ];
  const WIDTH = BODY[0].length;
  const BLANK = '.'.repeat(WIDTH);
  // Eye shut: a two-pixel line, for blinks, naps and the joy of sliding.
  const shut = (rows) => rows.map((row) => row.replace('be', 'oo'));
  // Every pose has the same height; its bottom row stands on the line.
  const POSES = {
    stand: [...BODY, '..odo.odo....odo.odo..', '..ooo.ooo....ooo.ooo..'],
    walkA: [...BODY, '.odo...odo..odo...odo.', '.ooo...ooo..ooo...ooo.'], // stride
    walkB: [BLANK, ...BODY, '...oooooo....oooooo...'], // legs passing: the body dips
    slide: [BLANK, ...shut(BODY), 'ooo...............ooo.'], // belly down, legs stretched
    lie: [BLANK, BLANK, ...BODY],
    nap: [BLANK, BLANK, ...shut(BODY)],
  };
  const HEIGHT = POSES.stand.length;
  // Speed lines trailing the slide, two alternating frames (w).
  const SPEED = [
    ['ww.www.', '.......', '.www.w.'],
    ['.www.ww', '.......', 'w.www..'],
  ];
  // Nap particles: a small z, then a big one, rising and fading (z).
  const Z_SMALL = ['zzzz', '..z.', '.z..', 'zzzz'];
  const Z_BIG = ['zzzzz', '...z.', '..z..', '.z...', 'zzzzz'];

  const v = (name) => `var(--gd-capy-${name})`;
  const PALETTE = {
    o: v('outline'), b: v('coat'), l: v('coat-light'), d: v('coat-shade'), s: v('snout'), e: v('outline'),
    f: v('fruit'), F: v('fruit-light'), r: v('fruit-shade'), g: v('leaf'),
    L: v('line'), P: v('point'), w: v('speed'), z: v('zz'),
  };

  const mirror = (rows) => rows.map((row) => [...row].reverse().join(''));
  // Shear rows onto the line: column c drops by the rows the line drops
  // between the sprite's left column and its column c. phase is the left
  // column's position within its run of the staircase.
  function shear(rows, phase) {
    const drop = (c) => Math.floor((phase + c) / RUN);
    const grid = Array.from({ length: rows.length + drop(rows[0].length - 1) }, () => [...'.'.repeat(rows[0].length)]);
    rows.forEach((row, y) => [...row].forEach((char, c) => { if (char !== '.') grid[y + drop(c)][c] = char; }));
    return grid.map((row) => row.join(''));
  }
  const phaseOf = (x) => (((x - LINE.x0) % RUN) + RUN) % RUN;
  const cache = new Map();
  function sprite(id, rows, x) {
    const key = `${id}-${phaseOf(x)}`;
    if (!cache.has(key)) cache.set(key, frameGroup(`gd-capy-${key}`, shear(rows, phaseOf(x)), PALETTE));
    return cache.get(key);
  }
  const FLIPPED = Object.fromEntries(Object.entries(POSES).map(([name, rows]) => [name, mirror(rows)]));

  // The loop as a list of steps: pose, facing, left column on the line, how
  // long it lasts, and optional hop height, speed-line frame and nap tick.
  const LEFT_MIN = LINE.x0;
  const LEFT_MAX = LINE.x1 - WIDTH + 1;
  function timeline() {
    const steps = [];
    const at = (pose, right, x, ms, extra) => steps.push({ pose, right, x, ms, ...extra });
    // Slide down, picking up speed.
    for (let x = LEFT_MIN; x <= LEFT_MAX; x += 1) {
      const t = (x - LEFT_MIN) / (LEFT_MAX - LEFT_MIN);
      at('slide', true, x, Math.round(55 - 40 * t), t > 0.2 ? { speed: x % 2 } : {});
    }
    // Stop, lie down, blink, nap, wake up.
    at('stand', true, LEFT_MAX, 180);
    at('lie', true, LEFT_MAX, 420);
    at('nap', true, LEFT_MAX, 140);
    at('lie', true, LEFT_MAX, 380);
    for (let zz = 0; zz < 7; zz += 1) at('nap', true, LEFT_MAX, 230, { zz });
    at('lie', true, LEFT_MAX, 320);
    // Hop round to face the top.
    at('stand', true, LEFT_MAX, 120);
    at('stand', true, LEFT_MAX, 80, { hop: 1 });
    at('stand', false, LEFT_MAX, 100, { hop: 2 });
    at('stand', false, LEFT_MAX, 80, { hop: 1 });
    at('stand', false, LEFT_MAX, 160);
    // Climb back up, one pixel at a time, legs cycling.
    const gait = ['walkA', 'stand', 'walkB', 'stand'];
    for (let x = LEFT_MAX - 1, i = 0; x >= LEFT_MIN; x -= 1, i += 1) at(gait[i % gait.length], false, x, 62);
    // Catch breath at the top, hop round, off again.
    at('stand', false, LEFT_MIN, 420);
    at('stand', false, LEFT_MIN, 80, { hop: 1 });
    at('stand', true, LEFT_MIN, 100, { hop: 2 });
    at('stand', true, LEFT_MIN, 80, { hop: 1 });
    at('slide', true, LEFT_MIN, 160);
    return steps;
  }
  const STEPS = timeline();
  // Shown when motion is reduced: napping at the bottom of the fit.
  const REST = { pose: 'nap', right: true, x: LEFT_MAX, zz: 3 };

  function layer(id, rows, x, y) {
    const group = frameGroup(id, rows, PALETTE);
    group.setAttribute('transform', `translate(${x} ${y})`);
    return group;
  }

  function buildScene() {
    const svg = svgEl('svg', {
      viewBox: `0 0 ${COLS} ${ROWS}`,
      width: COLS * UNIT,
      height: ROWS * UNIT,
      'shape-rendering': 'crispEdges',
      'aria-hidden': 'true',
      focusable: 'false',
    });
    const line = Array.from({ length: lineY(LINE.x1) - LINE.y0 + 1 }, () => [...'.'.repeat(LINE.x1 - LINE.x0 + 1)]);
    for (let x = LINE.x0; x <= LINE.x1; x += 1) line[lineY(x) - LINE.y0][x - LINE.x0] = 'L';
    svg.append(
      ...POINTS.map(([x, off], i) => layer(`gd-capy-point-${i}`, ['PP', 'PP'], x, lineY(x) + off)),
      layer('gd-capy-line', line.map((row) => row.join('')), LINE.x0, LINE.y0),
    );
    const speed = svgEl('g', {});
    const zz = [svgEl('g', {}), svgEl('g', {})];
    zz[0].append(frameGroup('gd-capy-z-small', Z_SMALL, PALETTE));
    zz[1].append(frameGroup('gd-capy-z-big', Z_BIG, PALETTE));
    const capy = svgEl('g', {});
    svg.append(speed, capy, ...zz);
    return { svg, speed, capy, zz };
  }

  function draw(scene, step) {
    const { pose, right, x, hop = 0 } = step;
    const top = lineY(x) - HEIGHT - hop;
    scene.capy.replaceChildren(sprite(`${pose}-${right ? 'r' : 'l'}`, (right ? POSES : FLIPPED)[pose], x));
    scene.capy.setAttribute('transform', `translate(${x} ${top})`);

    scene.speed.replaceChildren();
    if (step.speed !== undefined) {
      const sx = x - SPEED[0][0].length - 1;
      scene.speed.append(sprite(`speed-${step.speed}`, SPEED[step.speed], sx));
      scene.speed.setAttribute('transform', `translate(${sx} ${lineY(sx) - 8})`);
    }

    // Two z's over the napping head: the small one rises from the start, the
    // big one two ticks later; each fades out as it goes up.
    const tick = step.zz;
    [0, 2].forEach((delay, i) => {
      const t = tick === undefined ? -1 : tick - delay;
      const z = scene.zz[i];
      z.style.display = t < 0 || t > 4 ? 'none' : '';
      if (t < 0 || t > 4) return;
      z.setAttribute('transform', `translate(${x + 13 + 5 * i} ${lineY(x) - 12 - 5 * i - t})`);
      z.setAttribute('opacity', t < 3 ? 1 : 0.5);
    });
  }

  function init() {
    const station = document.querySelector('[data-guide-station="capybara"]');
    const aside = station && station.closest('.gd-aside');
    if (!aside) return;
    const scene = buildScene();
    station.append(scene.svg);

    // Same rule as the other stations: show the scene only when it fits in
    // the sticky sidebar under the navigator, so it never adds a scrollbar.
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

    // One timer for the whole loop, running only while the scene is on
    // screen and motion is allowed; otherwise the capybara naps, still.
    const still = window.matchMedia('(prefers-reduced-motion: reduce)');
    let index = 0;
    let timer = null;
    let visible = false;
    const stop = () => { clearTimeout(timer); timer = null; };
    const tick = () => {
      const step = STEPS[index];
      draw(scene, step);
      index = (index + 1) % STEPS.length;
      timer = setTimeout(tick, step.ms);
    };
    const update = () => {
      stop();
      if (still.matches) draw(scene, REST);
      else if (visible) tick();
    };
    draw(scene, still.matches ? REST : STEPS[0]);
    new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; update(); }).observe(station);
    still.addEventListener('change', update);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
