/**
 * animations.js — Page animation module.
 *
 * Exports pure/injectable functions for testability, plus an `initAnimations()`
 * entry point that wires everything together using real browser globals.
 *
 * Responsibilities:
 *  - Uses IntersectionObserver to apply fade-in / slide-up CSS animations to
 *    page sections when they first enter the viewport
 *  - Checks window.matchMedia('(prefers-reduced-motion: reduce)') and skips
 *    all non-essential animations when true
 *  - Applies hover transitions (150–300ms) to buttons, links, and .card-hover
 *    elements via CSS classes
 *  - Applies underline slide-in animation to .nav-link elements on hover
 *
 * Requirements: 8.1, 8.2, 8.3, 8.4
 */

// ---------------------------------------------------------------------------
// CSS class definitions injected by this module (self-contained)
// ---------------------------------------------------------------------------

let _stylesInjected = false;

/**
 * Inject the hover-transition and nav-underline class definitions into the
 * document <head> once per page load.
 */
function ensureStyles() {
  if (_stylesInjected) return;
  _stylesInjected = true;

  const style = document.createElement('style');
  style.setAttribute('data-animations-module', 'true');
  style.textContent = `
    .hover-transition {
      transition: all 200ms ease;
    }
    .nav-underline {
      position: relative;
    }
    .nav-underline::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      width: 0;
      height: 2px;
      background: currentColor;
      transition: width 200ms ease;
    }
    .nav-underline:hover::after {
      width: 100%;
    }
    .motion-reduced,
    .motion-reduced * {
      transition-duration: 0ms !important;
      animation-duration: 0ms !important;
    }
  `;
  document.head.appendChild(style);
}

// ---------------------------------------------------------------------------
// Pure / injectable functions (exported for testability)
// ---------------------------------------------------------------------------

/**
 * Determine whether the user prefers reduced motion.
 *
 * @param {(query: string) => { matches: boolean }} matchMediaFn - Injected
 *   matchMedia function (defaults to window.matchMedia in production).
 * @returns {boolean} true if prefers-reduced-motion: reduce is active.
 */
export function prefersReducedMotion(matchMediaFn) {
  try {
    return matchMediaFn('(prefers-reduced-motion: reduce)').matches;
  } catch {
    return false;
  }
}

/**
 * Add or remove CSS transition classes on interactive elements based on the
 * reduced-motion flag.
 *
 * When reducedMotion is false:
 *   - Adds 'hover-transition' to buttons, links, and .card-hover elements
 *   - Adds 'nav-underline' to .nav-link elements
 *
 * When reducedMotion is true:
 *   - Adds 'motion-reduced' to all targeted elements
 *   - Does NOT add 'hover-transition' or 'nav-underline'
 *
 * @param {Element[]} elements - Array of interactive elements to process.
 * @param {boolean} reducedMotion - Whether reduced motion is preferred.
 */
export function applyHoverClasses(elements, reducedMotion) {
  for (const el of elements) {
    if (reducedMotion) {
      el.classList.add('motion-reduced');
      el.classList.remove('hover-transition');
      el.classList.remove('nav-underline');
    } else {
      el.classList.remove('motion-reduced');
      if (el.classList.contains('nav-link')) {
        el.classList.add('nav-underline');
      } else {
        el.classList.add('hover-transition');
      }
    }
  }
}

/**
 * Set up an IntersectionObserver on `.animate-on-scroll` elements.
 *
 * When an element enters the viewport, the 'visible' class is added (which
 * triggers the CSS transition already defined in input.css). Each element is
 * unobserved after it becomes visible (animate once).
 *
 * Skips setup entirely when reducedMotion is true.
 *
 * @param {Element[]} elements - Elements to observe.
 * @param {boolean} reducedMotion - Whether reduced motion is preferred.
 * @param {typeof IntersectionObserver} ObserverClass - Injected
 *   IntersectionObserver constructor (for testability).
 * @returns {IntersectionObserver|null} The created observer, or null if skipped.
 */
export function initIntersectionObserver(elements, reducedMotion, ObserverClass) {
  if (reducedMotion) return null;
  if (!elements || elements.length === 0) return null;

  const observer = new ObserverClass((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    }
  });

  for (const el of elements) {
    observer.observe(el);
  }

  return observer;
}

// ---------------------------------------------------------------------------
// Main entry point
// ---------------------------------------------------------------------------

/**
 * Wire up all animations using real browser globals.
 * Called by HTML pages on DOMContentLoaded.
 *
 * @param {{ root?: Document }} [options]
 */
export function initAnimations(options = {}) {
  const root = options.root ?? document;

  ensureStyles();

  const reduced = prefersReducedMotion(window.matchMedia.bind(window));

  // Collect interactive elements for hover transitions
  const interactiveElements = Array.from(
    root.querySelectorAll('button, a, .card-hover, .nav-link')
  );
  applyHoverClasses(interactiveElements, reduced);

  // Collect scroll-animation elements
  const scrollElements = Array.from(root.querySelectorAll('.animate-on-scroll'));
  initIntersectionObserver(scrollElements, reduced, IntersectionObserver);
}

// ---------------------------------------------------------------------------
// Auto-init on DOMContentLoaded (when loaded as a script tag)
// ---------------------------------------------------------------------------

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initAnimations());
  } else {
    // DOM already ready (e.g. script loaded with defer)
    initAnimations();
  }
}

export default { prefersReducedMotion, applyHoverClasses, initIntersectionObserver, initAnimations };
