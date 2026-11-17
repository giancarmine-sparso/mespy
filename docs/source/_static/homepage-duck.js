/* Homepage duck mascot: a pixel sprite swimming on the bottom line of the strip under the hero; click to salute. */
(() => {
  const { svgEl, frameGroup } = window.mespyPixel;

  // Tunables.
  const SPEED = 24; // swim speed, px/s
  const BOB_AMPLITUDE = 2; // vertical bob peak, px (rounded to whole px)
  const BOB_PERIOD = 1600; // ms
  const TURN_PAUSE = 300; // ms spent still at an edge before turning
  const EDGE_MARGIN = 0; // px inside the strip's content box
  // Salute on click / Enter / Space: [frame, ms] in order, then back to profilo.
  const SALUTE = [
    ['treQuarti', 110],
    ['fronte', 140],
    ['salutoMeta', 90],
    ['salutoSu', 900],
    ['salutoMeta', 90],
    ['fronte', 160],
    ['treQuarti', 110],
  ];

  const { FRAMES, PALETTE } = window.mespyDuckFrames;
  const FRONTAL = new Set(['fronte', 'salutoMeta', 'salutoSu']); // never mirrored
  const WATERLINE = 10; // sprite row resting on the line
  const UNIT = 3; // CSS px per logical pixel
  const MAX_DT = 50; // ms, clamps the step after a pause or a slow frame
  const MIN_RUN = 4; // shortest swimmable line, in duck widths

  const COLS = FRAMES.profilo[0].length;
  const ROWS = FRAMES.profilo.length;
  const PAD = 1; // logical rows of headroom above/below for the bob
  const WIDTH = COLS * UNIT;

  const duck = { x: 0, y: 0, dir: 1, state: 'idle', wait: 0, clock: 0, min: 0, max: 0, frame: null, salute: -1, saluteWait: 0, el: null, body: null, frameUse: null };

  // The svg never moves vertically: its two clip paths keep the dry/wet split on
  // the strip's line while the bob only shifts the sprite group inside them.
  function buildSprite() {
    const svg = svgEl('svg', {
      viewBox: `0 ${-PAD} ${COLS} ${ROWS + 2 * PAD}`,
      width: WIDTH,
      height: (ROWS + 2 * PAD) * UNIT,
      'shape-rendering': 'crispEdges',
      'aria-hidden': 'true',
      focusable: 'false',
    });
    const defs = svgEl('defs', {});
    // One cached group per frame; the sprite shows one of them through a <use>.
    for (const [name, rows] of Object.entries(FRAMES)) defs.append(frameGroup(`mh-duck-frame-${name}`, rows, PALETTE));
    const body = svgEl('g', { id: 'mh-duck-sprite' });
    duck.frameUse = svgEl('use', {});
    body.append(duck.frameUse);
    const clip = (id, y, height) => {
      const path = svgEl('clipPath', { id });
      path.append(svgEl('rect', { x: 0, y, width: COLS, height }));
      return path;
    };
    defs.append(body, clip('mh-duck-dry', -PAD, WATERLINE + PAD), clip('mh-duck-wet', WATERLINE, ROWS - WATERLINE + PAD));
    svg.append(
      defs,
      svgEl('use', { href: '#mh-duck-sprite', 'clip-path': 'url(#mh-duck-dry)' }),
      svgEl('use', { href: '#mh-duck-sprite', 'clip-path': 'url(#mh-duck-wet)', class: 'mh-duck-wet' }),
    );
    duck.body = body;
    setFrame('profilo');
    return svg;
  }

  function setFrame(name) {
    if (duck.frame === name) return;
    duck.frame = name;
    duck.frameUse.setAttribute('href', `#mh-duck-frame-${name}`);
  }

  function render() {
    // Facing the viewer, the sprite is never mirrored: the salute keeps its wing.
    const face = FRONTAL.has(duck.frame) ? 1 : duck.dir;
    duck.el.style.transform = `translateX(${Math.round(duck.x)}px) scaleX(${face})`;
    duck.body.setAttribute('transform', `translate(0 ${duck.y / UNIT})`);
  }

  function salute() {
    if (duck.salute >= 0) return;
    duck.salute = 0;
    duck.saluteWait = SALUTE[0][1];
    setFrame(SALUTE[0][0]);
  }

  function advanceSalute(dt) {
    duck.saluteWait -= dt;
    while (duck.saluteWait <= 0) {
      duck.salute += 1;
      if (duck.salute >= SALUTE.length) {
        duck.salute = -1;
        setFrame('profilo');
        return;
      }
      duck.saluteWait += SALUTE[duck.salute][1];
      setFrame(SALUTE[duck.salute][0]);
    }
  }

  // moving: false on a line too short to swim on and with reduced motion (no swim, no bob).
  function step(dt, moving) {
    duck.clock += dt;
    duck.y = moving ? Math.round(BOB_AMPLITUDE * Math.sin((2 * Math.PI * duck.clock) / BOB_PERIOD)) : 0;
    // A salute pauses swimming (and a pending turn) where the duck is.
    if (duck.salute >= 0) {
      advanceSalute(dt);
      return;
    }
    if (!moving) return;
    if (duck.state === 'turn') {
      duck.wait -= dt;
      if (duck.wait <= 0) {
        duck.dir = -duck.dir;
        duck.state = 'swim';
      }
      return;
    }
    duck.x += (duck.dir * SPEED * dt) / 1000;
    const edge = duck.dir > 0 ? duck.max : duck.min;
    if ((edge - duck.x) * duck.dir <= 0) {
      duck.x = edge;
      duck.state = 'turn';
      duck.wait = TURN_PAUSE;
    }
  }

  function init() {
    const strip = document.querySelector('.mespy-home .mh-principles');
    // The translated name comes from the template; no duck without one, since
    // the sprite is hidden from assistive technology.
    const label = strip?.dataset.duckLabel;
    if (!label) return;
    const grid = strip.querySelector('.mh-principles-grid');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let swimmable = false;
    let visible = false;
    let frame = 0;
    let last = null;

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'mh-duck';
    button.setAttribute('aria-label', label);
    button.style.setProperty('--mh-duck-sink', `${(ROWS - WATERLINE + PAD) * UNIT}px`);
    button.append(buildSprite());
    // Native button: Enter and Space also fire click.
    button.addEventListener('click', () => {
      salute();
      render();
      sync();
    });
    duck.el = button;
    strip.append(button);

    // The loop also runs for a salute on a short line or with reduced motion.
    const shouldRun = () => (swimmable || duck.salute >= 0) && visible && !document.hidden;

    function tick(now) {
      frame = 0;
      const dt = last === null ? 0 : Math.min(now - last, MAX_DT);
      last = now;
      step(dt, swimmable);
      render();
      if (shouldRun()) frame = requestAnimationFrame(tick);
    }

    function sync() {
      const run = shouldRun();
      if (run && !frame) {
        last = null;
        frame = requestAnimationFrame(tick);
      } else if (!run && frame) {
        cancelAnimationFrame(frame);
        frame = 0;
      }
    }

    // The lane is the inner box's width (.mh-principles-grid, an .mh-shell).
    function layout() {
      const box = strip.getBoundingClientRect();
      const content = grid.getBoundingClientRect();
      duck.min = content.left - box.left + EDGE_MARGIN;
      duck.max = Math.max(duck.min, content.right - box.left - WIDTH - EDGE_MARGIN);
      const wasSwimmable = swimmable;
      swimmable = !reducedMotion.matches && duck.max - duck.min >= MIN_RUN * WIDTH;
      // Not swimming: at rest at the start of the lane.
      if (!swimmable) {
        Object.assign(duck, { x: duck.min, y: 0, dir: 1, state: 'idle' });
      } else if (!wasSwimmable) {
        Object.assign(duck, { x: duck.min, dir: 1, state: 'swim' });
      }
      duck.x = Math.min(Math.max(duck.x, duck.min), duck.max);
      render();
      sync();
    }

    layout();
    new ResizeObserver(layout).observe(strip);
    reducedMotion.addEventListener('change', layout);
    document.addEventListener('visibilitychange', sync);
    new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      sync();
    }).observe(strip);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
