const lenis = new Lenis({
  duration: 1.4,
  easing: (t) => Math.min(1, 1.001 - 
    Math.pow(2, -10 * t)),
  orientation: 'vertical',
  smoothWheel: true,
  wheelMultiplier: 1.0,
  touchMultiplier: 1.8,
});

lenis.on('scroll', ScrollTrigger.update);

gsap.ticker.add(function(time) {
  lenis.raf(time * 1000);
});
gsap.ticker.lagSmoothing(0);

var chipTrackEl = document.getElementById(
  'vizChipsTrack'
);
if (chipTrackEl) {
  chipTrackEl.addEventListener(
    'touchstart', function() {
      lenis.stop();
    },
    { passive: true }
  );
  chipTrackEl.addEventListener(
    'touchend', function() {
      setTimeout(function() {
        lenis.start();
      }, 100);
    },
    { passive: true }
  );
}

// Connect lenis to anchor scroll
document.querySelectorAll('a[href^="#"]')
  .forEach(a => {
    a.addEventListener('click', e => {
      const id = a.getAttribute('href').slice(1);
      if (!id) return;
      const target = document.getElementById(id);
      if (!target) return;
      e.preventDefault();
      lenis.scrollTo(target, { offset: -20 });
    });
  });

lenis.on('scroll', (e) => {
  document.dispatchEvent(
    new CustomEvent('lenis-scroll', {
      detail: e
    })
  );
});

const timers = {
  stats: [],
  mani: [],
  svc: []
};

function clearTimers(key) {
  timers[key].forEach(id => clearTimeout(id));
  timers[key] = [];
}

/* MAK-SHANG PAINTS — interactions */

console.log('hero-meta:', document.querySelector('.hero-meta'))
console.log('lines:', document.querySelectorAll('.hero-headline .line'))
console.log('hero-sub:', document.querySelector('.hero-sub'))
console.log('stats:', document.querySelectorAll('.hero-foot-stat'))

const vidDesktop = document.querySelector('.vid-desktop');
const vidMobile  = document.querySelector('.vid-mobile');
const BREAKPOINT = 768;

function getActive() {
  return window.innerWidth <= BREAKPOINT 
    ? 'mobile' 
    : 'desktop';
}

let current = null;

function switchVideo() {
  const active = getActive();
  if (active === current) return;
  current = active;

  if (active === 'desktop') {
    // pause + unload mobile
    if (vidMobile) {
      vidMobile.pause();
      vidMobile.src = '';
      vidMobile.load();
    }
    // load + play desktop
    if (vidDesktop) {
      vidDesktop.src = 'images/hero-loop.mp4';
      vidDesktop.load();
      vidDesktop.play();
    }
  } else {
    // pause + unload desktop
    if (vidDesktop) {
      vidDesktop.pause();
      vidDesktop.src = '';
      vidDesktop.load();
    }
    // load + play mobile
    if (vidMobile) {
      vidMobile.src = 'images/hero-mobile.mp4';
      vidMobile.load();
      vidMobile.play();
    }
  }
}

// Run on page load
switchVideo();

document.addEventListener('DOMContentLoaded', () => {
  const hamBtn = document.getElementById('hamBtn');
  const mobNav = document.getElementById('mobNav');

  if (hamBtn && mobNav) {
    hamBtn.addEventListener('click', () => {
      if (hamBtn.classList.contains('open')) {
        hamBtn.classList.remove('open');
        mobNav.classList.remove('open');
        document.body.style.overflow = '';
      } else {
        hamBtn.classList.add('open');
        mobNav.classList.add('open');
        document.body.style.overflow = 'hidden';
      }
    });

    const mobClose = document.getElementById('mobClose');
    if (mobClose) {
      mobClose.addEventListener('click', () => {
        hamBtn.classList.remove('open');
        mobNav.classList.remove('open');
        document.body.style.overflow = '';
      });
    }

    mobNav.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        hamBtn.classList.remove('open');
        mobNav.classList.remove('open');
        document.body.style.overflow = '';
      });
    });
  }
});

// Run on resize with debounce
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(switchVideo, 150);
});

/* ───── Video Fallback ───── */
(function () {
  const isMobile = window.innerWidth <= 768;
  const activeVideo = isMobile
    ? document.querySelector('.hero-video-mobile')
    : document.querySelector('.hero-video-desktop');

  if (activeVideo) {
    const fallbackTimer = setTimeout(() => {
      const hero = document.querySelector('.hero');
      if (hero) hero.classList.add('video-failed');
    }, 3000);

    activeVideo.addEventListener('playing', () => {
      clearTimeout(fallbackTimer);
    });
  }

  const inactiveVideo = isMobile
    ? document.querySelector('.hero-video-desktop')
    : document.querySelector('.hero-video-mobile');

  if (inactiveVideo) {
    inactiveVideo.pause();
    inactiveVideo.removeAttribute('src');
    inactiveVideo.load();
  }
})();

/* ───── Scroll reveal ───── */
(function () {
  const els = document.querySelectorAll(
    '.stat, .service-row, .ba-card, .step, .swatch, .proj, .why-card, .testi-card, .area-pill, .faq-row, .founders-title, .founders-story, .founder, .color-title, .color-desc, .manifesto-quote, .stats-row, .hero-headline .line, .cta-title'
  );
  els.forEach((el) => el.classList.add('reveal'));

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e, i) => {
        if (e.isIntersecting) {
          // stagger inside a section
          const peers = Array.from(e.target.parentElement.children).filter((c) => c === e.target);
          e.target.style.transitionDelay = (Math.random() * 0.18).toFixed(2) + 's';
          e.target.classList.add('is-in');
          io.unobserve(e.target);
        }
      });
    },
    { threshold: 0.12 }
  );
  els.forEach((el) => io.observe(el));
})();

/* ───── Services accordion ───── */
(function () {
  const rows = document.querySelectorAll('.service-row');
  rows.forEach((row) => {
    const btn = row.querySelector('.srv-toggle');
    if (!btn) return;
    btn.addEventListener('click', () => {
      const wasOpen = row.classList.contains('open');
      rows.forEach((r) => {
        r.classList.remove('open');
        const t = r.querySelector('.srv-toggle');
        if (t) t.textContent = '+';
      });
      if (!wasOpen) {
        row.classList.add('open');
        btn.textContent = '×';
      }
    });
  });
})();

/* ───── Before/After draggable dividers ───── */
// ═══ BEFORE/AFTER SLIDERS ═══
(function() {

  document.querySelectorAll('.ba-card')
    .forEach(function(card) {

    var afterImg = card.querySelector('.ba-img-after');
    var line     = card.querySelector('.ba-slider-line');
    var handle   = card.querySelector('.ba-slider-handle');

    var dragging  = false;
    var animated  = false;
    var rafId     = null;

    // Track touch start position
    // to detect horizontal vs vertical intent
    var touchStartX = 0;
    var touchStartY = 0;
    var touchLocked = false; // true = horizontal drag confirmed

    function setPos(p) {
      p = Math.max(2, Math.min(98, p));
      afterImg.style.clipPath =
        'inset(0 ' + (100 - p) + '% 0 0)';
      line.style.left   = p + '%';
      handle.style.left = p + '%';
    }

    function getPct(clientX) {
      var rect = card.getBoundingClientRect();
      return Math.max(2, Math.min(98,
        ((clientX - rect.left) / rect.width) * 100
      ));
    }

    // Initial position
    setPos(50);

    // ── AUTO ANIMATE ON ENTER ──
    var obs = new IntersectionObserver(
      function(entries) {
        entries.forEach(function(e) {
          if (e.isIntersecting && !animated) {
            animated = true;
            obs.unobserve(card);
            var pos = 95;
            setPos(pos);
            setTimeout(function() {
              function step() {
                pos -= 1.2;
                setPos(pos);
                if (pos > 50) {
                  rafId = requestAnimationFrame(step);
                } else {
                  setPos(50);
                  rafId = null;
                }
              }
              rafId = requestAnimationFrame(step);
            }, 400);
          }
        });
      },
      { threshold: 0.3 }
    );
    obs.observe(card);

    // ── MOUSE EVENTS (desktop) ──
    card.addEventListener('mousedown', function(e) {
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      dragging = true;
      card.classList.add('is-dragging');
      setPos(getPct(e.clientX));
      e.preventDefault();
    });

    document.addEventListener('mousemove', function(e) {
      if (!dragging) return;
      setPos(getPct(e.clientX));
    });

    document.addEventListener('mouseup', function() {
      if (!dragging) return;
      dragging = false;
      card.classList.remove('is-dragging');
    });

    // ── TOUCH EVENTS (mobile) ──
    // Step 1: record where touch started
    card.addEventListener('touchstart', function(e) {
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
      touchLocked = false;
      dragging    = false;
    }, { passive: true });

    // Step 2: on first move decide H or V
    // passive: false so we can preventDefault
    card.addEventListener('touchmove', function(e) {
      var dx = Math.abs(e.touches[0].clientX - touchStartX);
      var dy = Math.abs(e.touches[0].clientY - touchStartY);

      if (!touchLocked) {
        // Need 6px movement to decide direction
        if (dx < 6 && dy < 6) return;

        if (dx > dy) {
          // Horizontal intent → lock as drag
          touchLocked = true;
          dragging    = true;
          card.classList.add('is-dragging');
        } else {
          // Vertical intent → let page scroll
          touchLocked = true;
          dragging    = false;
          return;
        }
      }

      if (!dragging) return;

      // Block page scroll during horizontal drag
      e.preventDefault();
      e.stopPropagation();

      setPos(getPct(e.touches[0].clientX));

    }, { passive: false }); // MUST be false to preventDefault

    document.addEventListener('touchend', function() {
      dragging    = false;
      touchLocked = false;
      card.classList.remove('is-dragging');
    }, { passive: true });

    // ── CLICK TO JUMP (tap anywhere on card) ──
    card.addEventListener('click', function(e) {
      // Only jump if it was not a drag
      if (touchLocked && dragging) return;
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      setPos(getPct(e.clientX));
    });

  });

})();


/* (old FAQ toggle handler removed — superseded by faqAccordion) */

/* ───── Smooth-scroll for anchor links ───── */
(function () {
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href').slice(1);
      if (!id) return;
      const target = document.getElementById(id);
      if (!target) return;
      e.preventDefault();
      window.scrollTo({ top: target.offsetTop - 20, behavior: 'smooth' });
    });
  });
})();

/* ───── Hero Animations ───── */
(function heroAnimations() {

  // ── safety check ──
  const headline = document.querySelector('.hero-headline');
  if (!headline) return;

  // ── SETUP: hide everything first ──
  const meta    = document.querySelector('.hero-meta');
  const lines   = document.querySelectorAll('.hero-headline .line');
  const sub     = document.querySelector('.hero-sub');
  const foot    = document.querySelector('.hero-foot');
  const stats   = document.querySelectorAll('.hero-foot-num');
  const ticker  = document.querySelector('.ticker-track');
  const scroll  = document.querySelector('.hero-side-mark');
  const redDot  = document.querySelector('.red-dot');
  const isMob = window.innerWidth <= 768;
  const t = isMob ? 0.5 : 1;

  // hide all initially
  if (meta)   { meta.style.opacity = '0'; meta.style.transform = 'translateY(16px)'; }
  lines.forEach(l => { l.style.opacity = '0'; l.style.transform = 'translateY(60px)'; });
  if (sub)    { sub.style.opacity  = '0'; sub.style.transform  = 'translateY(20px)'; }
  if (foot)   { foot.style.opacity = '0'; }
  if (scroll) { scroll.style.opacity = '0'; }
  if (redDot) { redDot.style.opacity = '0'; redDot.style.transform = 'scale(3)'; }

  // ── HELPER: smooth reveal ──
  function reveal(el, delay, extraStyles) {
    if (!el) return;
    setTimeout(() => {
      el.style.transition = 'opacity 0.7s ease, transform 0.7s cubic-bezier(0.16,1,0.3,1)';
      el.style.opacity    = '1';
      el.style.transform  = 'none';
      if (extraStyles) Object.assign(el.style, extraStyles);
    }, delay);
  }

  // ── HELPER: decode text ──
  function decode(el, delay) {
    if (!el) return;
    const symbols  = '@#$%&!?/\\|*^~◣';
    const original = el.textContent;
    const chars    = original.split('');
    let iteration  = 0;

    setTimeout(() => {
      el.style.opacity = '1';
      el.style.transform = 'none';

      const interval = setInterval(() => {
        el.textContent = chars
          .map((char, i) => {
            if (char === ' ' || char === '·' || char === '—') return char;
            if (i < iteration) return original[i];
            return symbols[Math.floor(Math.random() * symbols.length)];
          })
          .join('');

        iteration += 1.5;
        if (iteration >= chars.length) {
          el.textContent = original;
          clearInterval(interval);
        }
      }, 40);
    }, delay);
  }

  // ── HELPER: count up ──
  function countUp(el, target, suffix, delay) {
    if (!el) return;
    setTimeout(() => {
      el.style.transition = 'opacity 0.4s ease';
      el.style.opacity = '1';
      let current = 0;
      const overshoot = Math.round(target * 1.08);
      const duration  = 1600;
      const start     = performance.now();

      function step(now) {
        const elapsed  = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const ease     = 1 - Math.pow(1 - progress, 3);
        current = Math.round(ease * overshoot);
        el.textContent = current + suffix;
        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          // snap to real value
          setTimeout(() => {
            el.textContent = target + suffix;
          }, 80);
        }
      }
      requestAnimationFrame(step);
    }, delay);
  }

  // ── RED DOT PULSE ──
  function fireDot(delay) {
    if (!redDot) return;
    setTimeout(() => {
      redDot.style.transition = 'opacity 0.05s, transform 0.15s steps(1)';
      redDot.style.opacity    = '1';
      redDot.style.transform  = 'scale(1)';

      setTimeout(() => {
        redDot.style.animation = 'dotPulse 0.6s ease-out forwards';
      }, 80);
    }, delay);
  }

  // ── TICKER SPEED RAMP ──
  function rampTicker(delay) {
    if (!ticker) return;
    setTimeout(() => {
      let dur   = 8;
      const end = 28;
      const t   = 3000;
      const s   = performance.now();

      function step(now) {
        const p = Math.min((now - s) / t, 1);
        ticker.style.animationDuration = (dur + (end - dur) * p) + 's';
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }, delay);
  }

  // ── RUN SEQUENCE ──
  
  decode(meta, 0);

  if (isMob) {
    function runWordTakeover(onComplete) {
      const headline = document.querySelector('.hero-headline');
      const lineEls = document.querySelectorAll('.hero-headline .line');
      const words = ['YOUR', 'WALLS', 'REBORN.'];

      // Create overlay
      const overlay = document.createElement('div');
      overlay.className = 'takeover-overlay';
      document.body.appendChild(overlay);

      // Hide headline during sequence
      headline.classList.add('doing-takeover');

      // Create 3 full-screen word elements
      const wordEls = words.map((word, i) => {
        const el = document.createElement('div');
        el.className = 'line takeover';

        if (i === 0) el.classList.add('line-outline');
        else el.classList.add('line-solid');

        if (word === 'REBORN.') {
          el.innerHTML = 'REBORN<span class="red-dot">.</span>';
        } else {
          el.textContent = word;
        }

        document.body.appendChild(el);
        return el;
      });

      let step = 0;

      function nextWord() {
        if (step >= words.length) {
          // All words shown — settle into headline
          settleWords();
          return;
        }

        const el = wordEls[step];

        // Show overlay
        overlay.classList.add('visible');

        // Slam word in
        el.classList.add('slam-in');

        const holdTime = step === 2 ? 600 : 400;

        setTimeout(() => {
          if (step < words.length - 1) {
            // Exit this word
            el.classList.remove('slam-in');
            el.classList.add('slam-out');

            setTimeout(() => {
              el.classList.remove('slam-out');
              el.style.opacity = '0';
              step++;
              nextWord();
            }, 200);
          } else {
            // Last word — go straight to settle
            step++;
            nextWord();
          }
        }, holdTime);
      }

      function settleWords() {
        // Remove overlay
        overlay.classList.remove('visible');
        setTimeout(() => overlay.remove(), 300);

        // Remove takeover word elements
        wordEls.forEach(el => {
          el.style.opacity = '0';
          setTimeout(() => el.remove(), 300);
        });

        // Reveal real headline
        setTimeout(() => {
          headline.classList.remove('doing-takeover');
          headline.classList.add('takeover-done');

          // Stagger each line appearing
          lineEls.forEach((line, i) => {
            line.style.opacity = '0';
            line.style.transform = 'translateY(20px)';
            setTimeout(() => {
              line.style.transition = 'opacity 0.5s ease, transform 0.5s cubic-bezier(0.16,1,0.3,1)';
              line.style.opacity = '1';
              line.style.transform = 'none';
            }, i * 120);
          });

          // Fire red dot pulse after REBORN appears
          setTimeout(() => {
            const dot = document.querySelector('.hero-headline .red-dot');
            if (dot) {
              dot.style.opacity = '1';
              dot.style.transform = 'scale(1)';
              dot.style.animation = 'dotPulse 0.6s ease-out forwards';
            }
          }, lineEls.length * 120 + 200);

          // Run callback — continue rest of hero animation sequence
          if (onComplete) onComplete();
        }, 200);
      }

      // Start sequence
      nextWord();
    }

    // Run takeover FIRST then rest of sequence
    runWordTakeover(() => {
      // After takeover done continue sequence:
      // sub text, stats, scroll indicator etc.
      reveal(sub,    500);
      reveal(foot,   1200);

      stats.forEach((s, i) => {
        const targets  = [200, 5, 24];
        const suffixes = ['+', '★', 'h'];
        s.textContent = '0';
        s.style.opacity = '0';
        countUp(s, targets[i], suffixes[i], 1500 + i * 200);
      });

      reveal(scroll, 2500);
      rampTicker(3000);
    });
  } else {
    reveal(lines[0], 1200 * t);   // YOUR
    reveal(lines[1], 2000 * t);   // WALLS
    reveal(lines[2], 2800 * t);   // REBORN.
    fireDot(3050 * t);

    reveal(sub,   3500 * t);
    reveal(foot,  5500 * t);

    stats.forEach((s, i) => {
      const targets  = [200, 5, 24];
      const suffixes = ['+', '★', 'h'];
      s.textContent = '0';
      s.style.opacity = '0';
      countUp(s, targets[i], suffixes[i], (5800 + i * 200) * t);
    });

    reveal(scroll, 8000 * t);
    rampTicker(9000 * t);
  }

})();

// --- STEP 2 STATS ---
function slotMachine(el, target, suffix, delay) {
  if (!el) return;
  timers.stats.push(
    setTimeout(() => {
      el.classList.add('visible');

      const parent = el.closest('.stat');
      const cap = parent 
        ? parent.querySelector('.stat-cap') 
        : null;

      let frame    = 0;
      const frames = 28;
      const fast   = 40;
      const slow   = 120;

      const spin = setInterval(() => {
        frame++;
        const progress = frame / frames;
        const interval = fast + 
          (slow - fast) * Math.pow(progress, 2);

        // show random number during spin
        const rand = Math.floor(
          Math.random() * (target * 1.5)
        );
        el.firstChild.textContent = rand;

        if (frame >= frames) {
          clearInterval(spin);
          // snap to final value
          el.firstChild.textContent = target;

          // suffix stamps in
          const sfx = el.querySelector('sup');
          if (sfx) {
            sfx.style.transition = 
              'transform 0.2s cubic-bezier(0.34,1.56,0.64,1), opacity 0.2s';
            sfx.style.transform  = 'scale(1)';
            sfx.style.opacity    = '1';
          }

          // caption fades in
          if (cap) {
            timers.stats.push(
              setTimeout(() => {
                cap.classList.add('visible');
              }, 200)
            );
          }
        }
      }, fast);
    }, delay)
  );
}

// Wrap stat number text in span 
// and hide sup initially
document.querySelectorAll('.stat-num')
  .forEach(el => {
    const sup = el.querySelector('sup');
    const txt = el.childNodes[0];
    if (sup) {
      sup.style.opacity   = '0';
      sup.style.transform = 'scale(0.5)';
    }
  });

// IntersectionObserver for stats
const statsObs = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {

        const statEls = entry.target
          .querySelectorAll('.stat');
        const data = [
          { target:200, suffix:'+' },
          { target:5,   suffix:'yrs' },
          { target:98,  suffix:'%' },
          { target:24,  suffix:'h' },
        ];

        statEls.forEach((s,i) => {
          timers.stats.push(
            setTimeout(() => {
              s.classList.add('visible');
            }, i * 80)
          );
        });

        entry.target.querySelectorAll('.stat-num')
          .forEach((el,i) => {
            const { target, suffix } = data[i] || {};
            if (target !== undefined) {
              slotMachine(el, target, suffix,
                300 + i * 220);
            }
          });

      } else {

        // RESET
        clearTimers('stats');

        entry.target.querySelectorAll('.stat')
          .forEach(s => s.classList.remove('visible'));

        entry.target.querySelectorAll('.stat-num')
          .forEach(el => {
            el.firstChild.textContent = '0';
            const sup = el.querySelector('sup');
            if (sup) {
              sup.style.opacity = '0';
          sup.style.transform = 'scale(0.5)';
            }
          });

        entry.target.querySelectorAll('.stat-cap')
          .forEach(c => c.classList.remove('visible'));
      }
    });
  },
  { threshold: 0.2 }
);

const statsSection = document.querySelector('.stats');
if (statsSection) statsObs.observe(statsSection);

(function processV2() {

  gsap.registerPlugin(ScrollTrigger);

  var track    = document.querySelector('.pv2-track');
  var sticky   = document.querySelector('.pv2-sticky');
  var progress = document.getElementById('pv2Progress');
  var scrollCue = document.getElementById('pv2ScrollCue');
  var images   = document.querySelectorAll('.pv2-bg-img');
  var steps    = document.querySelectorAll('.pv2-step');
  var dots     = document.querySelectorAll('.pv2-dot');

  if (!track || !sticky) return;

  // ── MOBILE SETUP ──
  if (window.innerWidth <= 768) {
    setupMobile();
    return;
  }

  // ── DESKTOP SCROLL SETUP ──
  var currentStep = 0;

  function showStep(index) {
    if (index === currentStep) return;
    currentStep = index;

    // Update images with cross-fade
    images.forEach(function(img, i) {
      if (i === index) {
        img.classList.add('active');
      } else {
        img.classList.remove('active');
      }
    });

    // Update step text
    steps.forEach(function(step, i) {
      if (i === index) {
        step.classList.remove('exit');
        step.classList.add('active');
      } else if (step.classList.contains('active')) {
        step.classList.add('exit');
        step.classList.remove('active');
        setTimeout(function() {
          step.classList.remove('exit');
        }, 700);
      } else {
        step.classList.remove('active','exit');
      }
    });

    // Update dots
    dots.forEach(function(dot, i) {
      dot.classList.toggle('active', i === index);
    });

    // Hide scroll cue after first scroll
    if (index > 0 && scrollCue) {
      scrollCue.classList.add('hidden');
    }

    // Step 4: special treatment
    if (index === 3) {
      // Remove dark overlay slightly
      // when reveal room shows
      document.querySelector('.pv2-overlay')
        .style.background = 
        'linear-gradient(to right,' +
        'rgba(0,0,0,0.82) 0%,' +
        'rgba(0,0,0,0.6) 35%,' +
        'rgba(0,0,0,0.2) 60%,' +
        'rgba(0,0,0,0.0) 100%)';
    } else {
      document.querySelector('.pv2-overlay')
        .style.background = '';
    }
  }

  // ── SCROLL TRIGGER ──
  ScrollTrigger.create({
    trigger: '.pv2-track',
    start: 'top top',
    end: 'bottom bottom',
    pin: '.pv2-sticky',
    pinSpacing: false,
    anticipatePin: 1,
    onUpdate: function(self) {
      var prog = self.progress;
      if (progress) {
        progress.style.height = 
          (prog * 100) + '%';
      }
      var stepIndex = Math.min(
        Math.floor(prog * 4), 3
      );
      showStep(stepIndex);
    }
  });

  // ── DOT CLICKS — jump to step ──
  dots.forEach(function(dot, i) {
    dot.addEventListener('click', function() {
      var trackTop = track.getBoundingClientRect().top 
        + window.scrollY;
      var trackH   = track.offsetHeight;
      var target   = trackTop + (i / 4) * trackH 
        + 10;
      window.scrollTo({
        top: target,
        behavior: 'smooth'
      });
    });
  });



  function setupMobile() {
    var sticky = document.querySelector('.pv2-sticky');
    if (!sticky) return;

    sticky.style.cssText =
      'position:relative;height:auto;' +
      'overflow:visible;background:#0A0A0A';

    var stepData = [
      {
        img: 'images/step1-raw.png',
        num: '01',
        title: 'YOU DESERVE<br>BETTER WALLS.',
        body: 'You\'ve looked at those walls long enough. WhatsApp us a photo. Tell us what you\'re dreaming of. We respond same day — not same week.',
        tag: '24h Response'
      },
      {
        img: 'images/step2-prep.png',
        num: '02',
        title: 'WE SHOW UP.<br>IN PERSON.',
        body: 'No decisions made over a phone screen. We stand in your room, in your light. Measure every surface. Leave you a written quote before we walk out. Free.',
        tag: 'Free Site Visit'
      },
      {
        img: 'images/step3-progress.png',
        num: '03',
        title: 'THE PART<br>NOBODY SEES.',
        body: 'Sand every crack. Fill every hole. Prime every surface. The foundation that makes the finish last 7 years. Most painters skip this. We built our name on it.',
        tag: '7 Year Guarantee'
      },
      {
        img: 'images/step4-reveal.png',
        num: '04',
        title: 'WALK IN.<br>FEEL IT.',
        body: 'We pack up. We clean completely. Not a paint tin left behind. You walk into a space that feels entirely new. That first moment — that is why we do this.',
        tag: 'Est. 2020 · 200+ Homes'
      }
    ];

    sticky.innerHTML = '';

    var head = document.createElement('div');
    head.style.cssText =
      'padding:48px 20px 32px;background:#0A0A0A';
    head.innerHTML =
      '<div style="font-family:\'JetBrains Mono\',monospace;' +
      'font-size:9px;letter-spacing:0.28em;text-transform:uppercase;' +
      'color:#E02020;display:flex;align-items:center;gap:8px;' +
      'margin-bottom:12px">' +
      '<span style="width:8px;height:8px;background:#E02020;' +
      'display:inline-block;flex-shrink:0"></span>' +
      'HOW WE WORK</div>' +
      '<h2 style="font-family:\'Anton\',sans-serif;' +
      'font-size:clamp(40px,10vw,56px);line-height:0.9;' +
      'text-transform:uppercase;color:#FFFFFF">' +
      'RAW TO<br>REFINED.</h2>';
    sticky.appendChild(head);

    stepData.forEach(function(step) {
      var card = document.createElement('div');
      card.className = 'pv2-cin-card';
      card.style.cssText =
        'background:#0A0A0A;' +
        'border-bottom:1px solid rgba(255,255,255,0.06);' +
        'overflow:hidden';

      var img = document.createElement('img');
      img.src = step.img;
      img.alt = step.title.replace(/<br>/g, ' ');
      img.style.cssText =
        'width:100%;aspect-ratio:16/9;' +
        'object-fit:cover;object-position:center;' +
        'display:block;' +
        'transform:scale(1.08);' +
        'transition:transform 0.9s cubic-bezier(.16,1,.3,1)';

      var content = document.createElement('div');
      content.style.cssText =
        'padding:28px 20px 40px 28px;' +
        'background:#0A0A0A;' +
        'position:relative;' +
        'border-left:2px solid rgba(224,32,32,0)';

      var numEl = document.createElement('div');
      numEl.innerHTML = step.num;
      numEl.style.cssText =
        'font-family:\'Anton\',sans-serif;' +
        'font-size:72px;line-height:1;' +
        'color:transparent;' +
        '-webkit-text-stroke:1px rgba(224,32,32,0.25);' +
        'margin-bottom:8px;' +
        'opacity:0;transform:translateY(20px);' +
        'transition:opacity 0.5s ease 0.1s,' +
        'transform 0.5s cubic-bezier(.16,1,.3,1) 0.1s';

      var titleEl = document.createElement('h3');
      titleEl.innerHTML = step.title;
      titleEl.style.cssText =
        'font-family:\'Anton\',sans-serif;' +
        'font-size:clamp(28px,7vw,38px);' +
        'line-height:0.92;text-transform:uppercase;' +
        'color:#FFFFFF;margin-bottom:16px;' +
        'opacity:0;transform:translateY(24px);' +
        'transition:opacity 0.5s ease 0.2s,' +
        'transform 0.5s cubic-bezier(.16,1,.3,1) 0.2s';

      var bodyEl = document.createElement('p');
      bodyEl.textContent = step.body;
      bodyEl.style.cssText =
        'font-family:\'Space Grotesk\',sans-serif;' +
        'font-size:13px;line-height:1.7;' +
        'color:rgba(255,255,255,0.55);' +
        'margin-bottom:22px;' +
        'opacity:0;transform:translateY(16px);' +
        'transition:opacity 0.5s ease 0.32s,' +
        'transform 0.5s cubic-bezier(.16,1,.3,1) 0.32s';

      var tagEl = document.createElement('div');
      tagEl.textContent = step.tag;
      tagEl.style.cssText =
        'display:inline-flex;align-items:center;' +
        'font-family:\'JetBrains Mono\',monospace;' +
        'font-size:9px;letter-spacing:0.2em;' +
        'text-transform:uppercase;color:#E02020;' +
        'border:1px solid rgba(224,32,32,0.3);' +
        'padding:8px 14px;' +
        'opacity:0;transform:translateX(-12px);' +
        'transition:opacity 0.4s ease 0.44s,' +
        'transform 0.4s cubic-bezier(.16,1,.3,1) 0.44s';

      content.appendChild(numEl);
      content.appendChild(titleEl);
      content.appendChild(bodyEl);
      content.appendChild(tagEl);
      card.appendChild(img);
      card.appendChild(content);
      sticky.appendChild(card);

      new IntersectionObserver(function(entries, obs) {
        entries.forEach(function(entry) {
          if (!entry.isIntersecting) return;
          img.style.transform = 'scale(1)';
          content.style.borderLeftColor = '#E02020';
          content.style.transition =
            'border-left-color 0.6s cubic-bezier(.16,1,.3,1)';
          numEl.style.opacity  = '1';
          numEl.style.transform = 'translateY(0)';
          titleEl.style.opacity  = '1';
          titleEl.style.transform = 'translateY(0)';
          bodyEl.style.opacity  = '1';
          bodyEl.style.transform = 'translateY(0)';
          tagEl.style.opacity  = '1';
          tagEl.style.transform = 'translateX(0)';
          obs.unobserve(entry.target);
        });
      }, {
        threshold: 0,
        rootMargin: '0px 0px -10% 0px'
      }).observe(card);
    });
  }

})();

// --- STEP 3 MANIFESTO ---
// Split quote into word spans
const quote = document.querySelector(
  '.manifesto-quote'
);
if (quote) {
  quote.innerHTML = quote.innerHTML
    .split(' ')
    .map(word => {
      if (word.includes('<em>') || 
          word.includes('</em>')) {
        return word;
      }
      return `<span class="q-word">
        ${word}
      </span>`;
    })
    .join(' ');
  quote.style.opacity = '1';
}

const maniObs = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {

        const sec = entry.target;
        const stroke = sec.querySelector(
          '.brush-stroke'
        );
        if (stroke) stroke.classList.add('drawn');

        const words = sec.querySelectorAll('.q-word');
        words.forEach((w,i) => {
          timers.mani.push(
            setTimeout(() => {
              w.classList.add('vis');
            }, 900 + i * 65)
          );
        });

        const em = sec.querySelector(
          '.manifesto-quote em'
        );
        if (em) {
          timers.mani.push(
            setTimeout(() => {
              em.classList.add('underlined');
            }, 900 + words.length * 65 * 0.6 + 300)
          );
        }

        const rule = sec.querySelector(
          '.manifesto-rule'
        );
        if (rule) {
          timers.mani.push(
            setTimeout(() => {
              rule.classList.add('vis');
            }, 900 + words.length * 65 + 200)
          );
        }

        const cred = sec.querySelector(
          '.manifesto-cred'
        );
        if (cred) {
          timers.mani.push(
            setTimeout(() => {
              cred.classList.add('vis');
            }, 900 + words.length * 65 + 500)
          );
        }

      } else {

        // RESET
        clearTimers('mani');

        const sec = entry.target;

        const stroke = sec.querySelector(
          '.brush-stroke'
        );
        if (stroke) stroke.classList.remove('drawn');

        sec.querySelectorAll('.q-word')
          .forEach(w => w.classList.remove('vis'));

        const em = sec.querySelector(
          '.manifesto-quote em'
        );
        if (em) em.classList.remove('underlined');

        const rule = sec.querySelector(
          '.manifesto-rule'
        );
        if (rule) rule.classList.remove('vis');

        const cred = sec.querySelector(
          '.manifesto-cred'
        );
        if (cred) cred.classList.remove('vis');
      }
    });
  },
  { threshold: 0.2 }
);

const maniSec = document.querySelector('.manifesto');
if (maniSec) maniObs.observe(maniSec);

// --- STEP 4 SERVICES ---
// Wrap services title lines
const svcTitle = document.querySelector(
  '.services-title'
);
if (svcTitle) {
  svcTitle.innerHTML = svcTitle.innerHTML
    .split('<br>')
    .map(line => 
      `<span class="title-line">${line}</span>`
    )
    .join('');
}

// Split section-tag into letter spans
const svcTag = document.querySelector(
  '.services .section-tag'
);
if (svcTag) {
  const bullet = svcTag.querySelector(
    '.tag-bullet'
  );
  const text = svcTag.lastChild.textContent;
  svcTag.lastChild.remove();
  text.split('').forEach((ch, i) => {
    const s = document.createElement('span');
    s.textContent = ch;
    s.style.transitionDelay = (i * 30) + 'ms';
    svcTag.appendChild(s);
  });
}

const svcObs = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {

        const sec = entry.target;

        const tag = sec.querySelector('.section-tag');
        if (tag) {
          timers.svc.push(
            setTimeout(() => {
              tag.classList.add('revealed');
            }, 0)
          );
        }

        sec.querySelectorAll('.title-line')
          .forEach((line,i) => {
            timers.svc.push(
              setTimeout(() => {
                line.classList.add('vis');
              }, 200 + i * 150)
            );
          });

        sec.querySelectorAll('.service-row')
          .forEach((row,i) => {
            timers.svc.push(
              setTimeout(() => {
                row.classList.add('unrolled');
              }, 500 + i * 120)
            );
          });

      } else {

        // RESET
        clearTimers('svc');

        const sec = entry.target;

        const tag = sec.querySelector('.section-tag');
        if (tag) tag.classList.remove('revealed');

        sec.querySelectorAll('.title-line')
          .forEach(l => l.classList.remove('vis'));

        sec.querySelectorAll('.service-row')
          .forEach(r => r.classList.remove('unrolled'));
      }
    });
  },
  { threshold: 0.1 }
);

const svcSec = document.querySelector('.services');
if (svcSec) svcObs.observe(svcSec);

const COLORS = [
  {
    id: 'neutral',
    name: 'Raw Canvas',
    hex: '#E8E4DC',
    brand: 'Starting Point',
    mood: 'BEFORE',
    image: 'images/visualizer/room-neutral.png',
    mobileImage: 'images/visualizer/room-neutral-mobile.png'
  },
  {
    id: 'ivory',
    name: 'Warm Ivory',
    hex: '#F5EFE4',
    brand: 'Asian Paints · Ivory Glow',
    mood: 'BRIGHT & TIMELESS',
    image: 'images/visualizer/room-ivory.png',
    mobileImage: 'images/visualizer/room-ivory-mobile.png'
  },
  {
    id: 'sage',
    name: 'Sage Whisper',
    hex: '#7D9B7A',
    brand: 'Asian Paints · Muted Botanical',
    mood: 'FRESH & ORGANIC',
    image: 'images/visualizer/room-sage.png',
    mobileImage: 'images/visualizer/room-sage-mobile.png'
  },
  {
    id: 'terracotta',
    name: 'Terracotta Clay',
    hex: '#C4622D',
    brand: 'Asian Paints · Spice Route',
    mood: 'WARM & GROUNDED',
    image: 'images/visualizer/room-terracotta.png',
    mobileImage: 'images/visualizer/room-terracotta-mobile.png'
  },
  {
    id: 'teal',
    name: 'Deep Teal',
    hex: '#2D6A6A',
    brand: 'Asian Paints · Tropical Storm',
    mood: 'CALM & FOCUSED',
    image: 'images/visualizer/room-teal.png',
    mobileImage: 'images/visualizer/room-teal-mobile.png'
  },
  {
    id: 'slate',
    name: 'Stone Whisper',
    hex: '#52606D',
    brand: 'Asian Paints · Urban Grey',
    mood: 'MODERN & MINIMAL',
    image: 'images/visualizer/room-slate.png',
    mobileImage: 'images/visualizer/room-slate-mobile.png'
  },
  {
    id: 'navy',
    name: 'Deep Navy',
    hex: '#1F2A3A',
    brand: 'Asian Paints · Naval Depths',
    mood: 'BOLD & CONFIDENT',
    image: 'images/visualizer/room-navy.png',
    mobileImage: 'images/visualizer/room-navy-mobile.png'
  },
  {
    id: 'rose',
    name: 'Dusty Rose',
    hex: '#C99A95',
    brand: 'Asian Paints · Blush Whisper',
    mood: 'WARM & ROMANTIC',
    image: 'images/visualizer/room-rose.png',
    mobileImage: 'images/visualizer/room-rose-mobile.png'
  },
  {
    id: 'charcoal',
    name: 'Warm Charcoal',
    hex: '#2E2E2E',
    brand: 'Asian Paints · Dark Espresso',
    mood: 'DRAMATIC & PREMIUM',
    image: 'images/visualizer/room-charcoal.png',
    mobileImage: 'images/visualizer/room-charcoal-mobile.png'
  },
  {
    id: 'forest',
    name: 'Forest Canopy',
    hex: '#3D5247',
    brand: 'Asian Paints · Deep Moss',
    mood: 'RICH & ORGANIC',
    image: 'images/visualizer/room-forest.png',
    mobileImage: 'images/visualizer/room-forest-mobile.png'
  }
];

(function colorVisualizer() {

  var stack     = document.getElementById('vizStack');
  var swatches  = document.getElementById('vizSwatches');
  var wipe      = document.getElementById('vizWipe');
  var wipePath  = document.getElementById('vizWipePath');
  var badge     = document.getElementById('vizBadge');
  var badgeDot  = document.getElementById('vizBadgeDot');
  var badgeName = document.getElementById('vizBadgeName');
  var hint      = document.getElementById('vizHint');
  var swatchBig = document.getElementById('vizSwatchBig');
  var colorName = document.getElementById('vizColorName');
  var colorHex  = document.getElementById('vizColorHex');
  var colorBrand = document.getElementById('vizColorBrand');
  var moodTag   = document.getElementById('vizMoodTag');
  var waBtn     = document.getElementById('vizWaBtn');

  if (!stack || !swatches) return;

  var currentIndex = 0;
  var isAnimating  = false;
  var hoverImg     = null;

  // ── BUILD ROOM IMAGES — desktop only ──
  if (window.innerWidth > 768) {
    COLORS.forEach(function(color, i) {
      var img = document.createElement('img');
      img.className = 'viz-room-img' +
        (i === 0 ? ' active' : '');
      img.src = color.image;
      img.alt = color.name + ' room';
      img.draggable = false;
      img.setAttribute('data-index', i);
      img.loading = i === 0 ? 'eager' : 'lazy';
      stack.appendChild(img);
    });
  }

  // ── BUILD SWATCHES — desktop only ──
  if (window.innerWidth > 768) {
  COLORS.forEach(function(color, i) {
    var sw = document.createElement('div');
    sw.className = 'viz-swatch' + 
      (i === 0 ? ' active' : '');
    sw.setAttribute('data-index', i);
    sw.innerHTML =
      '<div class="viz-swatch-circle" ' +
        'style="background:' + color.hex + '">' +
      '</div>' +
      '<span class="viz-swatch-label">' +
        color.name + 
      '</span>';
    swatches.appendChild(sw);

    // Click
    sw.addEventListener('click', function() {
      if (isAnimating) return;
      if (i === currentIndex) return;
      activateColor(i);
    });

    // Hover preview
    sw.addEventListener('mouseenter', function() {
      if (i === currentIndex) return;
      var imgs = stack.querySelectorAll('.viz-room-img');
      if (hoverImg) {
        hoverImg.classList.remove('hover-preview');
      }
      hoverImg = imgs[i];
      hoverImg.classList.add('hover-preview');
    });

    sw.addEventListener('mouseleave', function() {
      if (hoverImg) {
        hoverImg.classList.remove('hover-preview');
        hoverImg = null;
      }
    });
  });
  } // end desktop swatches guard

  // ── PAINT WIPE ANIMATION ──
  function paintWipe(callback) {
    isAnimating = true;
    wipe.classList.add('animating');

    // Sweep in left to right
    var startTime = null;
    var sweepDur  = 400; // ms for wipe in
    var holdDur   = 80;  // ms hold
    var wipeDur   = 300; // ms for wipe out

    function sweepIn(ts) {
      if (!startTime) startTime = ts;
      var p = Math.min((ts - startTime) / sweepDur, 1);
      var ease = 1 - Math.pow(1 - p, 3);
      // Translate from -110% to 0%
      var tx = -110 + ease * 120;
      wipePath.style.transform = 
        'translateX(' + tx + '%)';
      if (p < 1) {
        requestAnimationFrame(sweepIn);
      } else {
        // Switch image at peak
        if (callback) callback();
        setTimeout(sweepOut, holdDur);
      }
    }

    function sweepOut() {
      var outStart = null;
      function step(ts) {
        if (!outStart) outStart = ts;
        var p = Math.min(
          (ts - outStart) / wipeDur, 1
        );
        var ease = 1 - Math.pow(1 - p, 3);
        var tx = ease * 120;
        wipePath.style.transform = 
          'translateX(' + tx + '%)';
        if (p < 1) {
          requestAnimationFrame(step);
        } else {
          wipe.classList.remove('animating');
          wipePath.style.transform = 
            'translateX(-110%)';
          isAnimating = false;
        }
      }
      requestAnimationFrame(step);
    }

    requestAnimationFrame(sweepIn);
  }

  // ── UPDATE UI INFO ──
  function updateInfo(color) {
    // Color swatch big
    swatchBig.style.background = color.hex;

    // Text info
    colorName.textContent = color.name;
    colorHex.textContent  = color.hex;
    colorBrand.textContent = color.brand;
    moodTag.textContent   = color.mood;

    // Badge
    badgeDot.style.background = color.hex;
    badgeName.textContent = color.name;

    // WhatsApp link
    var msg = encodeURIComponent(
      'Hi MAK-SHANG, I liked the ' + 
      color.name + ' (' + color.hex + 
      ') color for my room. ' +
      'Can we discuss a free consultation?'
    );
    waBtn.href = 
      'https://wa.me/917085585443?text=' + msg;
  }

  // ── ACTIVATE COLOR ──
  function activateColor(index) {
    var imgs    = stack.querySelectorAll(
      '.viz-room-img'
    );
    var swatchEls = swatches.querySelectorAll(
      '.viz-swatch'
    );
    var color = COLORS[index];

    // Remove hover preview
    if (hoverImg) {
      hoverImg.classList.remove('hover-preview');
      hoverImg = null;
    }

    paintWipe(function() {
      // Switch active image
      imgs.forEach(function(img, i) {
        img.classList.toggle('active', i === index);
      });
      currentIndex = index;
    });

    // Update swatches
    swatchEls.forEach(function(sw, i) {
      sw.classList.toggle('active', i === index);
    });

    // Update info
    updateInfo(color);

    // Hide hint after first click
    if (hint) hint.classList.add('hidden');
  }

  if (window.innerWidth > 768) {

    // ── INIT — set first color info ──
    updateInfo(COLORS[0]);
    if (swatchBig) {
      swatchBig.style.background = COLORS[0].hex;
    }

    // ── REVEAL SECTION ON SCROLL ──
    new IntersectionObserver(function(ens, ob) {
      ens.forEach(function(e) {
        if (e.isIntersecting) {
          e.target.style.opacity = '1';
          e.target.style.transform = 'none';
          ob.unobserve(e.target);
        }
      });
    }, { threshold: 0.1 }).observe(
      document.querySelector('.viz')
    );

  }

})();

document.addEventListener('DOMContentLoaded', function() {
  if (window.innerWidth > 768) return;

  var roomWrap   = document.getElementById('vizRoomWrap');
  var stack      = document.getElementById('vizStack');
  var wipe       = document.getElementById('vizWipe');
  var wipePath   = document.getElementById('vizWipePath');
  var badgeName  = document.getElementById('vizBadgeName');
  var badgeDot   = document.getElementById('vizBadgeDot');
  var colorName  = document.getElementById('vizColorName');
  var colorHex   = document.getElementById('vizColorHex');
  var colorBrand = document.getElementById('vizColorBrand');
  var moodTag    = document.getElementById('vizMoodTag');
  var swatchBig  = document.getElementById('vizSwatchBig');
  var waBtn      = document.getElementById('vizWaBtn');
  var hint       = document.getElementById('vizHint');

  if (!stack || !roomWrap || !wipe || !wipePath) return;

  var current     = 0;
  var isAnimating = false;

  // CLEAR STACK — remove any existing images
  stack.innerHTML = '';

  // BUILD MOBILE IMAGES
  COLORS.forEach(function(color, i) {
    var img = document.createElement('img');
    img.className = 'viz-room-img' +
      (i === 0 ? ' active' : '');
    img.src = 'images/visualizer/room-' +
      color.id + '-mobile.png';
    img.alt = color.name;
    img.draggable = false;
    img.loading = i === 0 ? 'eager' : 'lazy';
    stack.appendChild(img);
  });

  // REMOVE OLD LABEL AND STRIP IF EXIST
  var oldLabel = roomWrap.querySelector('.viz-mob-label');
  var oldStrip = roomWrap.querySelector('.viz-side-strip');
  if (oldLabel) oldLabel.remove();
  if (oldStrip) oldStrip.remove();

  // BUILD BOTTOM LABEL
  var mobLabel = document.createElement('div');
  mobLabel.className = 'viz-mob-label';
  mobLabel.innerHTML =
    '<span class="viz-mob-label-name">' +
    COLORS[0].name + '</span>' +
    '<span class="viz-mob-label-mood">' +
    COLORS[0].mood + '</span>';
  roomWrap.appendChild(mobLabel);

  // BUILD SIDE STRIP
  var strip = document.createElement('div');
  strip.className = 'viz-side-strip';
  roomWrap.appendChild(strip);

  var stripDots = [];
  COLORS.forEach(function(color, i) {
    var dot = document.createElement('button');
    dot.className = 'viz-strip-dot' +
      (i === 0 ? ' active' : '');
    dot.style.background = color.hex;
    dot.setAttribute('type', 'button');
    dot.setAttribute('aria-label', color.name);
    strip.appendChild(dot);
    stripDots.push(dot);

    dot.addEventListener('click', function() {
      if (isAnimating || i === current) return;
      activateMobile(i);
    });
  });

  // MOBILE PAINT WIPE
  function mobilePaintWipe(callback) {
    isAnimating = true;
    wipe.classList.add('animating');

    var startTime = null;
    var sweepDur  = 380;
    var holdDur   = 60;
    var wipeDur   = 280;

    function sweepIn(ts) {
      if (!startTime) startTime = ts;
      var p    = Math.min((ts - startTime) / sweepDur, 1);
      var ease = 1 - Math.pow(1 - p, 3);
      var tx   = -110 + ease * 120;
      wipePath.style.transform =
        'translateX(' + tx + '%)';
      if (p < 1) {
        requestAnimationFrame(sweepIn);
      } else {
        if (callback) callback();
        setTimeout(sweepOut, holdDur);
      }
    }

    function sweepOut() {
      var outStart = null;
      function step(ts) {
        if (!outStart) outStart = ts;
        var p    = Math.min((ts - outStart) / wipeDur, 1);
        var ease = 1 - Math.pow(1 - p, 3);
        var tx   = ease * 120;
        wipePath.style.transform =
          'translateX(' + tx + '%)';
        if (p < 1) {
          requestAnimationFrame(step);
        } else {
          wipe.classList.remove('animating');
          wipePath.style.transform =
            'translateX(-110%)';
          isAnimating = false;
        }
      }
      requestAnimationFrame(step);
    }

    requestAnimationFrame(sweepIn);
  }

  // ACTIVATE COLOR
  function activateMobile(index) {
    var imgs  = stack.querySelectorAll('.viz-room-img');
    var color = COLORS[index];

    mobilePaintWipe(function() {
      imgs.forEach(function(img, i) {
        img.classList.toggle('active', i === index);
      });
      current = index;
    });

    stripDots.forEach(function(d, i) {
      d.classList.toggle('active', i === index);
    });

    mobLabel.classList.add('updating');
    setTimeout(function() {
      mobLabel.querySelector(
        '.viz-mob-label-name'
      ).textContent = color.name;
      mobLabel.querySelector(
        '.viz-mob-label-mood'
      ).textContent = color.mood;
      mobLabel.classList.remove('updating');
    }, 200);

    if (badgeName)  badgeName.textContent      = color.name;
    if (badgeDot)   badgeDot.style.background  = color.hex;
    if (colorName)  colorName.textContent      = color.name;
    if (colorHex)   colorHex.textContent       = color.hex;
    if (colorBrand) colorBrand.textContent     = color.brand;
    if (moodTag)    moodTag.textContent        = color.mood;
    if (swatchBig)  swatchBig.style.background = color.hex;
    if (waBtn) {
      var msg = encodeURIComponent(
        'Hi MAK-SHANG, I liked the ' +
        color.name + ' (' + color.hex +
        ') color. Can we discuss a free consultation?'
      );
      waBtn.href =
        'https://wa.me/917085585443?text=' + msg;
    }
    if (hint) hint.classList.add('hidden');
  }

  // INIT INFO ROW
  if (badgeName)  badgeName.textContent      = COLORS[0].name;
  if (badgeDot)   badgeDot.style.background  = COLORS[0].hex;
  if (colorName)  colorName.textContent      = COLORS[0].name;
  if (colorHex)   colorHex.textContent       = COLORS[0].hex;
  if (colorBrand) colorBrand.textContent     = COLORS[0].brand;
  if (moodTag)    moodTag.textContent        = COLORS[0].mood;
  if (swatchBig)  swatchBig.style.background = COLORS[0].hex;

});

/* ────────────────────────────────────────────────
   PORTFOLIO V3 (CONCEPT 3) STICKY NAV LOGIC
   ──────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function() {
  if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
    gsap.registerPlugin(ScrollTrigger);
    
    const navLinks = document.querySelectorAll('.pv3-link');
    const categories = document.querySelectorAll('.pv3-category');
    
    if (navLinks.length > 0 && categories.length > 0) {
      categories.forEach(function(cat, index) {
        ScrollTrigger.create({
          trigger: cat,
          start: 'top 60%',
          end: 'bottom 60%',
          onToggle: function(self) {
            if (self.isActive) {
              navLinks.forEach(link => link.classList.remove('active'));
              navLinks[index].classList.add('active');
            }
          }
        });
      });
      
      // Smooth scroll for pv3 nav links
      navLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
          e.preventDefault();
          const targetId = this.getAttribute('href').slice(1);
          const target = document.getElementById(targetId);
          if (target && typeof lenis !== 'undefined') {
            lenis.scrollTo(target, { offset: -40 });
          } else if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
          }
        });
      });
    }
  }
});

(function whyCards() {
  var cards = document.querySelectorAll('.why-card');
  if (!cards.length) return;

  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('in-view');
      observer.unobserve(entry.target);
    });
  }, {
    threshold: 0,
    rootMargin: '0px 0px -8% 0px'
  });

  cards.forEach(function(card) {
    observer.observe(card);
  });
})();

(function foundersTypewriter() {

  var story = document.querySelector('.founders-story');
  if (!story) return;

  var paras = Array.from(story.querySelectorAll('p'));
  if (!paras.length) return;

  var triggered = false;

  // Store original text and clear all paragraphs
  var texts = paras.map(function(p) {
    var text = p.textContent;
    p.textContent = '';
    return text;
  });

  function typeParas(index) {
    if (index >= paras.length) return;

    var p    = paras[index];
    var text = texts[index];
    var i    = 0;
    var isPunch = p.classList.contains('founders-punch');
    var speed   = isPunch ? 22 : 16;

    p.classList.add('typing');

    function typeChar() {
      if (i < text.length) {
        p.textContent = text.slice(0, i + 1);
        i++;
        setTimeout(typeChar, speed);
      } else {
        // Typing done — remove cursor after short pause
        setTimeout(function() {
          p.classList.remove('typing');
          // Start next paragraph after short gap
          setTimeout(function() {
            typeParas(index + 1);
          }, 180);
        }, 400);
      }
    }

    typeChar();
  }

  // Trigger on scroll into view — once only
  var observer = new IntersectionObserver(function(entries, obs) {
    entries.forEach(function(entry) {
      if (!entry.isIntersecting || triggered) return;
      triggered = true;
      obs.unobserve(entry.target);
      // Small delay before starting
      setTimeout(function() {
        typeParas(0);
      }, 300);
    });
  }, {
    threshold: 0,
    rootMargin: '0px 0px -10% 0px'
  });

  observer.observe(story);

})();

(function areaPills() {
  var pills = document.querySelectorAll('.area-pill');
  if (!pills.length) return;

  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('in-view');
      observer.unobserve(entry.target);
    });
  }, {
    threshold: 0,
    rootMargin: '0px 0px -8% 0px'
  });

  pills.forEach(function(pill, i) {
    pill.style.transitionDelay = (i * 40) + 'ms';
    observer.observe(pill);
  });
})();

(function scrollProgress() {

  var fill   = document.getElementById('scrollProgressFill');
  var btn    = document.getElementById('scrollTopBtn');
  if (!fill || !btn) return;

  var ticking = false;

  function updateProgress() {
    var scrollTop = window.pageYOffset ||
      document.documentElement.scrollTop;
    var docHeight =
      document.documentElement.scrollHeight -
      document.documentElement.clientHeight;

    var progress = docHeight > 0
      ? (scrollTop / docHeight) * 100
      : 0;

    fill.style.height = Math.min(progress, 100) + '%';

    // Show button after 400px scroll
    if (scrollTop > 400) {
      btn.classList.add('visible');
    } else {
      btn.classList.remove('visible');
    }

    ticking = false;
  }

  window.addEventListener('scroll', function() {
    if (!ticking) {
      requestAnimationFrame(updateProgress);
      ticking = true;
    }
  }, { passive: true });

  // Scroll to top on click
  btn.addEventListener('click', function() {
    if (typeof lenis !== 'undefined') {
      lenis.scrollTo(0, {
        duration: 1.4,
        easing: function(t) {
          return 1 - Math.pow(1 - t, 4);
        }
      });
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });

  // Init on load
  updateProgress();

})();


/* ════════════════════════════════════════════════
   UPGRADE 1 — PAGE LOAD SCREEN
   ════════════════════════════════════════════════ */



/* ════════════════════════════════════════════════
   UPGRADE 2 — PORTFOLIO LIGHTBOX
   ════════════════════════════════════════════════ */
(function portfolioLightbox() {
  if (window.innerWidth <= 768) return;

  var items = document.querySelectorAll('.pv3-item');
  if (!items.length) return;

  var currentIndex = 0;
  var images = [];

  // Collect all portfolio images with metadata
  items.forEach(function(item, i) {
    var img = item.querySelector('.pv3-img');
    var nameEl = item.querySelector('.pv3-name');
    var tagEl = item.querySelector('.pv3-tag');
    if (!img) return;
    images.push({
      src: img.src,
      alt: img.alt,
      name: nameEl ? nameEl.textContent : '',
      tag: tagEl ? tagEl.textContent : ''
    });
    item.style.cursor = 'zoom-in';
  });

  if (!images.length) return;

  // Create lightbox DOM
  var lb = document.createElement('div');
  lb.className = 'lightbox';
  lb.id = 'portfolioLightbox';
  lb.setAttribute('role', 'dialog');
  lb.setAttribute('aria-modal', 'true');
  lb.setAttribute('aria-label', 'Image preview');
  lb.innerHTML =
    '<button class="lightbox-close" aria-label="Close">&times;</button>' +
    '<button class="lightbox-nav lightbox-prev" aria-label="Previous">&#8592;</button>' +
    '<button class="lightbox-nav lightbox-next" aria-label="Next">&#8594;</button>' +
    '<img class="lightbox-img" src="" alt="" draggable="false">' +
    '<div class="lightbox-info">' +
      '<div class="lightbox-name"></div>' +
      '<div class="lightbox-tag"></div>' +
    '</div>';
  document.body.appendChild(lb);

  var lbImg = lb.querySelector('.lightbox-img');
  var lbName = lb.querySelector('.lightbox-name');
  var lbTag = lb.querySelector('.lightbox-tag');

  function open(index) {
    currentIndex = index;
    updateImage();
    lb.classList.add('active');
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', handleKey);
  }

  function close() {
    lb.classList.remove('active');
    document.body.style.overflow = '';
    document.removeEventListener('keydown', handleKey);
  }

  function updateImage() {
    var img = images[currentIndex];
    lbImg.src = img.src;
    lbImg.alt = img.alt;
    lbName.textContent = img.name;
    lbTag.textContent = img.tag;
  }

  function next() {
    currentIndex = (currentIndex + 1) % images.length;
    updateImage();
  }

  function prev() {
    currentIndex = (currentIndex - 1 + images.length) % images.length;
    updateImage();
  }

  function handleKey(e) {
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowRight') next();
    if (e.key === 'ArrowLeft') prev();
  }

  // Click on portfolio items
  items.forEach(function(item, i) {
    item.addEventListener('click', function() { open(i); });
  });

  // Lightbox controls
  lb.querySelector('.lightbox-close').addEventListener('click', close);
  lb.querySelector('.lightbox-prev').addEventListener('click', function(e) { e.stopPropagation(); prev(); });
  lb.querySelector('.lightbox-next').addEventListener('click', function(e) { e.stopPropagation(); next(); });
  lb.addEventListener('click', function(e) {
    if (e.target === lb) close();
  });
})();


/* ════════════════════════════════════════════════
   UPGRADE 3 — CUSTOM CURSOR (Desktop only)
   ════════════════════════════════════════════════ */
(function customCursor() {
  if (window.innerWidth <= 768 || 'ontouchstart' in window) return;

  var dot = document.createElement('div');
  dot.className = 'cursor-dot';
  document.body.appendChild(dot);

  var ring = document.createElement('div');
  ring.className = 'cursor-ring';
  document.body.appendChild(ring);

  var mouseX = 0, mouseY = 0;
  var ringX = 0, ringY = 0;
  var isHovering = false;

  document.addEventListener('mousemove', function(e) {
    mouseX = e.clientX;
    mouseY = e.clientY;
    dot.style.left = (mouseX - 4) + 'px';
    dot.style.top = (mouseY - 4) + 'px';
  });

  // Ring follows with 80ms lag
  function updateRing() {
    ringX += (mouseX - ringX) * 0.15;
    ringY += (mouseY - ringY) * 0.15;
    ring.style.left = (ringX - 20) + 'px';
    ring.style.top = (ringY - 20) + 'px';
    requestAnimationFrame(updateRing);
  }
  updateRing();

  // Hover detection
  var hoverSelectors = 'a, button, .btn-pill, .btn-red, .btn-outline, .srv-toggle, .pv3-item, .viz-swatch, .ba-card, .faq-row summary, .area-pill, .lightbox-nav, .lightbox-close';

  document.addEventListener('mouseover', function(e) {
    if (e.target.closest(hoverSelectors)) {
      dot.classList.add('hover');
      ring.classList.add('hover');
    }
  });

  document.addEventListener('mouseout', function(e) {
    if (e.target.closest(hoverSelectors)) {
      dot.classList.remove('hover');
      ring.classList.remove('hover');
    }
  });

  // Hide default cursor
  var style = document.createElement('style');
  style.textContent = 'body { cursor: none; } @media (max-width: 768px) { body { cursor: auto; } }';
  document.head.appendChild(style);
})();


/* ════════════════════════════════════════════════
   UPGRADE 4 — ACTIVE SECTION NAV HIGHLIGHT
   ════════════════════════════════════════════════ */
(function activeNav() {
  var navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
  if (!navLinks.length) return;

  var sections = [];
  navLinks.forEach(function(link) {
    var id = link.getAttribute('href').slice(1);
    var sec = document.getElementById(id);
    if (sec) sections.push({ link: link, section: sec });
  });

  if (!sections.length) return;

  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        sections.forEach(function(item) {
          if (item.section === entry.target) {
            item.link.classList.add('active');
          } else {
            item.link.classList.remove('active');
          }
        });
      }
    });
  }, {
    threshold: 0,
    rootMargin: '-40% 0px -55% 0px'
  });

  sections.forEach(function(item) {
    observer.observe(item.section);
  });
})();


/* ════════════════════════════════════════════════
   UPGRADE 5 — FAQ SMOOTH ACCORDION
   ════════════════════════════════════════════════ */
(function faqAccordion() {
  var rows = document.querySelectorAll('.faq-row');
  if (!rows.length) return;

  rows.forEach(function(row) {
    var summary = row.querySelector('summary');
    var ans     = row.querySelector('.faq-ans');
    if (!summary || !ans) return;

    // Keep details natively open permanently so the browser doesn't apply display:none
    // Our CSS .is-open class and max-height 0 will control actual visibility and animation
    row.setAttribute('open', '');

    // Wrap answer for max-height animation if not already wrapped
    if (!row.querySelector('.faq-ans-wrap')) {
      var wrap = document.createElement('div');
      wrap.className = 'faq-ans-wrap';
      ans.parentNode.insertBefore(wrap, ans);
      wrap.appendChild(ans);
    }

    summary.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();

      var isOpen = row.classList.contains('is-open');

      // Close all rows
      rows.forEach(function(r) {
        r.classList.remove('is-open');
        // Do NOT change textContent of toggle. CSS transform: rotate(45deg) turns '+' into '×' natively.
      });

      // If this row was closed open it
      if (!isOpen) {
        row.classList.add('is-open');
      }
    });
  });

  // Open first row by default
  var first = rows[0];
  if (first) {
    first.classList.add('is-open');
  }
})();


/* ════════════════════════════════════════════════
   UPGRADE 6 — BEFORE/AFTER KEYBOARD SUPPORT
   ════════════════════════════════════════════════ */
(function baKeyboard() {
  if (window.innerWidth <= 768) return;

  var cards = document.querySelectorAll('.ba-card');
  if (!cards.length) return;

  cards.forEach(function(card) {
    card.setAttribute('tabindex', '0');
    card.setAttribute('role', 'slider');
    card.setAttribute('aria-label', 'Before and after comparison. Use arrow keys to adjust.');

    var afterImg = card.querySelector('.ba-img-after');
    var line = card.querySelector('.ba-slider-line');
    var handle = card.querySelector('.ba-slider-handle');

    function setPos(p) {
      p = Math.max(2, Math.min(98, p));
      if (afterImg) afterImg.style.clipPath = 'inset(0 ' + (100 - p) + '% 0 0)';
      if (line) line.style.left = p + '%';
      if (handle) handle.style.left = p + '%';
    }

    card.addEventListener('keydown', function(e) {
      var currentLeft = parseFloat(line.style.left) || 50;
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        setPos(currentLeft - 5);
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        setPos(currentLeft + 5);
      }
    });
  });
})();




/* ════════════════════════════════════════════════
   PRODUCTION INTERACTIONS (additive)
   ════════════════════════════════════════════════ */

/* ── STAT COUNT-UP ── */
(function statCountUp() {
  var nums = document.querySelectorAll('.stat-num');
  if (!nums.length) return;

  function animateNum(el) {
    var sup = el.querySelector('sup');
    var supHTML = sup ? sup.outerHTML : '';
    var target = parseInt(el.textContent, 10);
    if (isNaN(target)) { el.classList.add('counted'); return; }
    var dur = 1400, start = null;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var ease = 1 - Math.pow(1 - p, 3);
      el.innerHTML = Math.round(target * ease) + supHTML;
      if (p < 1) requestAnimationFrame(step);
    }
    el.classList.add('counted');
    requestAnimationFrame(step);
  }

  var obs = new IntersectionObserver(function(entries, o) {
    entries.forEach(function(e) {
      if (!e.isIntersecting) return;
      animateNum(e.target);
      o.unobserve(e.target);
    });
  }, { threshold: 0.4 });
  nums.forEach(function(n) { obs.observe(n); });
})();

/* ── GENERIC SCROLL REVEAL ── */
(function scrollReveal() {
  var targets = document.querySelectorAll(
    '.areas-head, .areas-map-wrap, .areas-tags, ' +
    '.faq-left, .faq-list, .cta-inner, .foot-cols'
  );
  targets.forEach(function(t) { t.classList.add('reveal-up'); });
  var all = document.querySelectorAll('.reveal-up');
  if (!all.length) return;
  var obs = new IntersectionObserver(function(entries, o) {
    entries.forEach(function(e) {
      if (!e.isIntersecting) return;
      e.target.classList.add('in');
      o.unobserve(e.target);
    });
  }, { threshold: 0, rootMargin: '0px 0px -8% 0px' });
  all.forEach(function(el) { obs.observe(el); });
})();

/* ── SMOOTH ANCHOR SCROLL VIA LENIS ── */
(function smoothAnchors() {
  if (typeof lenis === 'undefined') return;
  document.querySelectorAll('a[href^="#"]').forEach(function(a) {
    a.addEventListener('click', function(e) {
      var id = a.getAttribute('href');
      if (id === '#' || id.length < 2) return;
      var target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      lenis.scrollTo(target, { offset: -20, duration: 1.2 });
      var mobNav = document.getElementById('mobNav');
      var ham = document.getElementById('hamBtn');
      if (mobNav) mobNav.classList.remove('open');
      if (ham) ham.classList.remove('open');
    });
  });
})();