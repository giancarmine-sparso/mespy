/* Homepage cat mascot: Schrödinger's cat asleep on the playground's Run button.
   It breathes and now and then stretches; a run wakes it up until the run is
   over. Purely decorative. */
(() => {
  const { svgEl, frameGroup } = window.mespyPixel;
  const { BODY, HARNESS, TAIL, PALETTE, ANCHOR, BODY_COLS, BODY_ROWS, COLS, ROWS, UNIT } = window.mespyCatFrames;

  // Tunables. Every mode plays a body track and a tail track, [frame, ms]
  // steps each, side by side; PACE scales every step (above 1 is slower).
  // Looped modes repeat both tracks; a one-shot mode ends with its body track,
  // its tail holding the last frame if it runs out first.
  const PACE = 1;
  const SHOW_HARNESS = false; // purple harness over the coat
  const MODES = {
    asleep: { // breathing, the tail swaying slowly against the button
      loop: true,
      body: [['dorme1', 2600], ['dorme2', 2200]],
      tail: [['giu1', 1800], ['giu2', 300], ['giu3', 280], ['giu4', 900], ['giu3', 280], ['giu2', 300]],
    },
    stretch: { // then back to sleep; the tail lifts with the rump
      body: [['occhiAperti', 900], ['stiracchio', 2400], ['occhiAperti', 1100]],
      tail: [['giu1', 900], ['orizzontale', 2400], ['giu1', 1100]],
    },
    wake: { // then awake
      body: [['occhiAperti', 700], ['stiracchio', 2000]],
      tail: [['giu1', 700], ['orizzontale', 1300], ['su', 700]],
    },
    awake: { // looking at the run, the question-mark tip twitching
      loop: true,
      body: [['attento', 2900]],
      tail: [['su', 2400], ['su2', 500]],
    },
    fallAsleep: { // then asleep; the tail comes down first
      body: [['occhiAperti', 1300]],
      tail: [['orizzontale', 500], ['giu1', 800]],
    },
  };
  for (const { body, tail } of Object.values(MODES)) for (const s of [...body, ...tail]) s[1] *= PACE;
  const FIRST_STRETCH = 6000; // ms after the cat first comes into view
  const STRETCH_EVERY = [30000, 60000]; // ms, random pause between stretches
  const STAY_AWAKE = 5000; // ms awake after a run ends, looking at the results
  const MAX_DT = 100; // ms, clamps the step after a pause or a slow frame

  // A track walks one sequence: { seq, index, wait }.
  const track = (seq, index = 0) => ({ seq, index, wait: seq[index][1] });

  // mode: one of MODES
  const cat = { mode: 'asleep', body: track(MODES.asleep.body), tail: track(MODES.asleep.tail), nextStretch: FIRST_STRETCH, busy: false, awakeFor: 0, shown: { body: null, tail: null }, bodyUse: null, harnessUse: null, tailUse: null };

  // Every frame is drawn once in <defs>; body and tail each show one through a <use>.
  function buildSprite() {
    const svg = svgEl('svg', {
      viewBox: `0 0 ${COLS} ${ROWS}`,
      width: COLS * UNIT,
      height: ROWS * UNIT,
      'shape-rendering': 'crispEdges',
      'aria-hidden': 'true',
      focusable: 'false',
    });
    const defs = svgEl('defs', {});
    for (const [name, rows] of Object.entries(BODY)) defs.append(frameGroup(`mh-cat-body-${name}`, rows, PALETTE));
    for (const [name, rows] of Object.entries(TAIL)) defs.append(frameGroup(`mh-cat-tail-${name}`, rows, PALETTE));
    cat.bodyUse = svgEl('use', {});
    cat.tailUse = svgEl('use', { transform: `translate(${ANCHOR.tail.x} ${ANCHOR.tail.y})` });
    svg.append(defs, cat.bodyUse);
    if (SHOW_HARNESS) {
      for (const [name, rows] of Object.entries(HARNESS)) defs.append(frameGroup(`mh-cat-harness-${name}`, rows, PALETTE));
      cat.harnessUse = svgEl('use', {});
      svg.append(cat.harnessUse);
    }
    svg.append(cat.tailUse);
    show();
    return svg;
  }

  function show() {
    const body = cat.body.seq[cat.body.index][0];
    const tail = cat.tail.seq[cat.tail.index][0];
    if (cat.shown.body !== body) {
      cat.bodyUse.setAttribute('href', `#mh-cat-body-${(cat.shown.body = body)}`);
      cat.harnessUse?.setAttribute('href', `#mh-cat-harness-${body}`);
    }
    if (cat.shown.tail !== tail) cat.tailUse.setAttribute('href', `#mh-cat-tail-${(cat.shown.tail = tail)}`);
  }

  function enter(mode, index = 0) {
    const { body, tail } = MODES[mode];
    Object.assign(cat, { mode, body: track(body, Math.min(index, body.length - 1)), tail: track(tail, Math.min(index, tail.length - 1)) });
    show();
  }

  function randomPause() {
    const [min, max] = STRETCH_EVERY;
    return min + Math.random() * (max - min);
  }

  // What comes after the last step of a one-shot mode.
  function finished() {
    if (cat.mode === 'wake') {
      cat.awakeFor = STAY_AWAKE;
      enter('awake');
    } else {
      cat.nextStretch = randomPause();
      enter('asleep');
    }
  }

  // Advances a track by dt; false once a one-shot track has run out.
  function advance(t, dt, loop) {
    t.wait -= dt;
    while (t.wait <= 0) {
      if (t.index + 1 >= t.seq.length) {
        if (!loop) { t.wait = 0; return false; }
        t.index = -1;
      }
      t.index += 1;
      t.wait += t.seq[t.index][1];
    }
    return true;
  }

  function step(dt) {
    if (cat.mode === 'asleep') {
      cat.nextStretch -= dt;
      if (cat.nextStretch <= 0) { enter('stretch'); return; }
    }
    if (cat.mode === 'awake' && !cat.busy) {
      cat.awakeFor -= dt;
      if (cat.awakeFor <= 0) { enter('fallAsleep'); return; }
    }
    const { loop } = MODES[cat.mode];
    advance(cat.tail, dt, loop);
    if (!advance(cat.body, dt, loop)) { finished(); return; }
    show();
  }

  // A run starts: wake up (an ongoing stretch just carries on into it).
  function runStarted(reduced) {
    cat.busy = true;
    if (reduced) { enter('awake'); return; }
    if (cat.mode === 'asleep') enter('wake');
    else if (cat.mode === 'stretch') enter('wake', cat.body.index);
    else if (cat.mode === 'fallAsleep') enter('awake');
  }

  function runEnded() {
    cat.busy = false;
    cat.awakeFor = STAY_AWAKE;
  }

  function init() {
    const run = document.querySelector('.mespy-home .mh-fit-run');
    if (!run) return;
    const card = run.closest('.mh-fit-editor');
    const code = card.querySelector('.mh-editor-code'); // aria-busy while a run loads or executes
    const perch = run.parentElement; // the toolbar's button group; Run is its last child
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let visible = false;
    let frame = 0;
    let last = null;
    let stillTimer = 0;

    const el = document.createElement('span');
    el.className = 'mh-cat';
    // Body's rear on the button's right edge, its baseline on the button's top border.
    el.style.setProperty('--mh-cat-top', `${-BODY_ROWS * UNIT}px`);
    el.style.setProperty('--mh-cat-right', `${-(COLS - BODY_COLS) * UNIT}px`);
    el.append(buildSprite());
    perch.classList.add('mh-cat-perch');
    card.classList.add('mh-has-cat');
    perch.append(el);

    const shouldRun = () => !reducedMotion.matches && visible && !document.hidden;

    function tick(now) {
      frame = 0;
      const dt = last === null ? 0 : Math.min(now - last, MAX_DT);
      last = now;
      step(dt);
      if (shouldRun()) frame = requestAnimationFrame(tick);
    }

    function sync() {
      const play = shouldRun();
      if (play && !frame) {
        last = null;
        frame = requestAnimationFrame(tick);
      } else if (!play && frame) {
        cancelAnimationFrame(frame);
        frame = 0;
      }
    }

    // Reduced motion: no breathing or stretching, just asleep or awake.
    function still() {
      clearTimeout(stillTimer);
      if (cat.busy) enter('awake');
      else stillTimer = setTimeout(() => { if (!cat.busy) enter('asleep'); }, cat.mode === 'awake' ? STAY_AWAKE : 0);
    }

    new MutationObserver(() => {
      const busy = code?.getAttribute('aria-busy') === 'true';
      if (busy === cat.busy) return;
      if (busy) runStarted(reducedMotion.matches);
      else runEnded();
      if (reducedMotion.matches) still();
    }).observe(code, { attributes: true, attributeFilter: ['aria-busy'] });

    reducedMotion.addEventListener('change', () => {
      if (reducedMotion.matches) still();
      sync();
    });
    document.addEventListener('visibilitychange', sync);
    new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      sync();
    }).observe(card);
    if (reducedMotion.matches) still();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
