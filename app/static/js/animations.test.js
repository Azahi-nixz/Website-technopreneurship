/**
 * Tests for animations.js — page animation module.
 *
 * Covers:
 *  - prefersReducedMotion() returns true/false based on media query
 *  - initIntersectionObserver() skips setup when reducedMotion is true
 *  - initIntersectionObserver() creates an observer when reducedMotion is false
 *  - Observer callback adds 'visible' class when element intersects
 *  - Observer callback does NOT add 'visible' class when element does not intersect
 *  - Observer unobserves element after it becomes visible
 *  - applyHoverClasses() adds 'hover-transition' when reducedMotion is false
 *  - applyHoverClasses() does NOT add 'hover-transition' when reducedMotion is true
 *  - applyHoverClasses() adds 'motion-reduced' when reducedMotion is true
 *
 * Property-based test:
 *  - Property 18: prefers-reduced-motion disables non-essential animations
 *    Validates: Requirements 8.4
 *
 * Requirements: 8.1, 8.2, 8.3, 8.4
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as fc from 'fast-check';
import {
  prefersReducedMotion,
  applyHoverClasses,
  initIntersectionObserver,
} from './animations.js';

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.useFakeTimers();
  document.body.innerHTML = '';
  document.head.innerHTML = '';
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Build a mock matchMedia function.
 * @param {boolean} matches
 */
function mockMatchMedia(matches) {
  return vi.fn().mockReturnValue({ matches });
}

/**
 * Build a mock IntersectionObserver class.
 * Returns the captured callback and a mock observe/unobserve.
 */
function createMockObserver() {
  let capturedCallback = null;
  const observeMock = vi.fn();
  const unobserveMock = vi.fn();

  class MockObserver {
    constructor(callback) {
      capturedCallback = callback;
    }
    observe(el) { observeMock(el); }
    unobserve(el) { unobserveMock(el); }
  }

  return { MockObserver, observeMock, unobserveMock, getCallback: () => capturedCallback };
}

/**
 * Create a simple DOM element with optional classes.
 * @param {string} tag
 * @param {...string} classes
 */
function createElement(tag, ...classes) {
  const el = document.createElement(tag);
  if (classes.length) el.className = classes.join(' ');
  return el;
}

// ---------------------------------------------------------------------------
// prefersReducedMotion()
// ---------------------------------------------------------------------------

describe('prefersReducedMotion()', () => {
  it('returns true when media query matches', () => {
    const result = prefersReducedMotion(mockMatchMedia(true));
    expect(result).toBe(true);
  });

  it('returns false when media query does not match', () => {
    const result = prefersReducedMotion(mockMatchMedia(false));
    expect(result).toBe(false);
  });

  it('calls matchMedia with the correct query string', () => {
    const fn = mockMatchMedia(false);
    prefersReducedMotion(fn);
    expect(fn).toHaveBeenCalledWith('(prefers-reduced-motion: reduce)');
  });

  it('returns false when matchMedia throws', () => {
    const fn = vi.fn().mockImplementation(() => { throw new Error('not supported'); });
    expect(prefersReducedMotion(fn)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// initIntersectionObserver()
// ---------------------------------------------------------------------------

describe('initIntersectionObserver()', () => {
  it('does NOT create an observer when reducedMotion is true', () => {
    const { MockObserver, observeMock } = createMockObserver();
    const el = createElement('div', 'animate-on-scroll');

    const result = initIntersectionObserver([el], true, MockObserver);

    expect(result).toBeNull();
    expect(observeMock).not.toHaveBeenCalled();
  });

  it('creates an observer when reducedMotion is false', () => {
    const { MockObserver, observeMock } = createMockObserver();
    const el = createElement('div', 'animate-on-scroll');

    const result = initIntersectionObserver([el], false, MockObserver);

    expect(result).not.toBeNull();
    expect(observeMock).toHaveBeenCalledWith(el);
  });

  it('returns null when elements array is empty', () => {
    const { MockObserver } = createMockObserver();
    const result = initIntersectionObserver([], false, MockObserver);
    expect(result).toBeNull();
  });

  it('observer callback adds "visible" class when element intersects', () => {
    const { MockObserver, getCallback } = createMockObserver();
    const el = createElement('div', 'animate-on-scroll');

    initIntersectionObserver([el], false, MockObserver);

    // Simulate intersection
    getCallback()([{ target: el, isIntersecting: true }]);

    expect(el.classList.contains('visible')).toBe(true);
  });

  it('observer callback does NOT add "visible" class when element does not intersect', () => {
    const { MockObserver, getCallback } = createMockObserver();
    const el = createElement('div', 'animate-on-scroll');

    initIntersectionObserver([el], false, MockObserver);

    // Simulate non-intersection
    getCallback()([{ target: el, isIntersecting: false }]);

    expect(el.classList.contains('visible')).toBe(false);
  });

  it('observer unobserves element after it becomes visible', () => {
    const { MockObserver, unobserveMock, getCallback } = createMockObserver();
    const el = createElement('div', 'animate-on-scroll');

    initIntersectionObserver([el], false, MockObserver);

    // Simulate intersection
    getCallback()([{ target: el, isIntersecting: true }]);

    expect(unobserveMock).toHaveBeenCalledWith(el);
  });

  it('observer does NOT unobserve element when it does not intersect', () => {
    const { MockObserver, unobserveMock, getCallback } = createMockObserver();
    const el = createElement('div', 'animate-on-scroll');

    initIntersectionObserver([el], false, MockObserver);

    getCallback()([{ target: el, isIntersecting: false }]);

    expect(unobserveMock).not.toHaveBeenCalled();
  });

  it('observes all provided elements', () => {
    const { MockObserver, observeMock } = createMockObserver();
    const els = [
      createElement('div', 'animate-on-scroll'),
      createElement('section', 'animate-on-scroll'),
      createElement('article', 'animate-on-scroll'),
    ];

    initIntersectionObserver(els, false, MockObserver);

    expect(observeMock).toHaveBeenCalledTimes(3);
  });
});

// ---------------------------------------------------------------------------
// applyHoverClasses()
// ---------------------------------------------------------------------------

describe('applyHoverClasses()', () => {
  it('adds "hover-transition" class to buttons when reducedMotion is false', () => {
    const btn = createElement('button');
    applyHoverClasses([btn], false);
    expect(btn.classList.contains('hover-transition')).toBe(true);
  });

  it('adds "hover-transition" class to links when reducedMotion is false', () => {
    const link = createElement('a');
    applyHoverClasses([link], false);
    expect(link.classList.contains('hover-transition')).toBe(true);
  });

  it('adds "hover-transition" class to .card-hover elements when reducedMotion is false', () => {
    const card = createElement('div', 'card-hover');
    applyHoverClasses([card], false);
    expect(card.classList.contains('hover-transition')).toBe(true);
  });

  it('adds "nav-underline" class to .nav-link elements when reducedMotion is false', () => {
    const navLink = createElement('a', 'nav-link');
    applyHoverClasses([navLink], false);
    expect(navLink.classList.contains('nav-underline')).toBe(true);
  });

  it('does NOT add "hover-transition" to .nav-link elements (uses nav-underline instead)', () => {
    const navLink = createElement('a', 'nav-link');
    applyHoverClasses([navLink], false);
    expect(navLink.classList.contains('hover-transition')).toBe(false);
  });

  it('does NOT add "hover-transition" class when reducedMotion is true', () => {
    const btn = createElement('button');
    applyHoverClasses([btn], true);
    expect(btn.classList.contains('hover-transition')).toBe(false);
  });

  it('does NOT add "nav-underline" class when reducedMotion is true', () => {
    const navLink = createElement('a', 'nav-link');
    applyHoverClasses([navLink], true);
    expect(navLink.classList.contains('nav-underline')).toBe(false);
  });

  it('adds "motion-reduced" class when reducedMotion is true', () => {
    const btn = createElement('button');
    applyHoverClasses([btn], true);
    expect(btn.classList.contains('motion-reduced')).toBe(true);
  });

  it('adds "motion-reduced" to all elements when reducedMotion is true', () => {
    const elements = [
      createElement('button'),
      createElement('a'),
      createElement('div', 'card-hover'),
      createElement('a', 'nav-link'),
    ];
    applyHoverClasses(elements, true);
    for (const el of elements) {
      expect(el.classList.contains('motion-reduced')).toBe(true);
    }
  });

  it('removes "hover-transition" if previously set when reducedMotion becomes true', () => {
    const btn = createElement('button');
    btn.classList.add('hover-transition');
    applyHoverClasses([btn], true);
    expect(btn.classList.contains('hover-transition')).toBe(false);
    expect(btn.classList.contains('motion-reduced')).toBe(true);
  });

  it('removes "motion-reduced" if previously set when reducedMotion becomes false', () => {
    const btn = createElement('button');
    btn.classList.add('motion-reduced');
    applyHoverClasses([btn], false);
    expect(btn.classList.contains('motion-reduced')).toBe(false);
    expect(btn.classList.contains('hover-transition')).toBe(true);
  });

  it('handles empty elements array without throwing', () => {
    expect(() => applyHoverClasses([], false)).not.toThrow();
    expect(() => applyHoverClasses([], true)).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// Property 18: prefers-reduced-motion disables non-essential animations
// Validates: Requirements 8.4
// ---------------------------------------------------------------------------

/**
 * Property 18: prefers-reduced-motion disables non-essential animations
 *
 * For any animated element, when prefers-reduced-motion: reduce is active,
 * the element SHALL NOT have CSS transition, animation, or transform properties
 * applied that produce motion (durations should be 0ms or the properties
 * should be absent).
 *
 * Validates: Requirements 8.4
 */
describe('Property 18: prefers-reduced-motion disables non-essential animations', () => {
  it('when reduced-motion is true: no hover-transition, motion-reduced added, no observer', () => {
    fc.assert(
      fc.property(
        fc.boolean(),
        (reducedMotion) => {
          // Create a set of representative interactive elements
          const button = createElement('button');
          const link = createElement('a');
          const card = createElement('div', 'card-hover');
          const navLink = createElement('a', 'nav-link');
          const scrollEl = createElement('div', 'animate-on-scroll');
          const elements = [button, link, card, navLink];

          // Apply hover classes based on the reduced-motion flag
          applyHoverClasses(elements, reducedMotion);

          // Set up mock observer to track whether it was created
          const { MockObserver, observeMock } = createMockObserver();
          const observer = initIntersectionObserver([scrollEl], reducedMotion, MockObserver);

          if (reducedMotion) {
            // All elements must have motion-reduced class
            const allHaveMotionReduced = elements.every(
              (el) => el.classList.contains('motion-reduced')
            );
            // No element should have hover-transition
            const noneHaveHoverTransition = elements.every(
              (el) => !el.classList.contains('hover-transition')
            );
            // No element should have nav-underline
            const noneHaveNavUnderline = elements.every(
              (el) => !el.classList.contains('nav-underline')
            );
            // No IntersectionObserver should be created
            const noObserver = observer === null;
            const noObserveCalls = observeMock.mock.calls.length === 0;

            // Elements must not have inline transition/animation styles with non-zero durations
            const noInlineMotionStyles = elements.every((el) => {
              const transition = el.style.transition;
              const animation = el.style.animation;
              // Either empty/absent, or explicitly 0ms
              const transitionOk = !transition || transition === '' || transition.includes('0ms');
              const animationOk = !animation || animation === '' || animation.includes('0ms');
              return transitionOk && animationOk;
            });

            return (
              allHaveMotionReduced &&
              noneHaveHoverTransition &&
              noneHaveNavUnderline &&
              noObserver &&
              noObserveCalls &&
              noInlineMotionStyles
            );
          } else {
            // Non-nav elements should have hover-transition
            const nonNavElements = [button, link, card];
            const haveHoverTransition = nonNavElements.every(
              (el) => el.classList.contains('hover-transition')
            );
            // nav-link should have nav-underline
            const navHasUnderline = navLink.classList.contains('nav-underline');
            // No element should have motion-reduced
            const noneHaveMotionReduced = elements.every(
              (el) => !el.classList.contains('motion-reduced')
            );
            // Observer should be created
            const hasObserver = observer !== null;

            return haveHoverTransition && navHasUnderline && noneHaveMotionReduced && hasObserver;
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('motion-reduced elements have no inline transition/animation styles with non-zero durations', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.constantFrom('button', 'a', 'div', 'section', 'article'),
          { minLength: 1, maxLength: 10 }
        ),
        (tagNames) => {
          const elements = tagNames.map((tag) => createElement(tag));

          // Apply with reduced motion = true
          applyHoverClasses(elements, true);

          return elements.every((el) => {
            // motion-reduced class must be present
            if (!el.classList.contains('motion-reduced')) return false;
            // hover-transition must NOT be present
            if (el.classList.contains('hover-transition')) return false;
            // No inline transition with non-zero duration
            const transition = el.style.transition;
            if (transition && transition !== '' && !transition.includes('0ms')) return false;
            // No inline animation with non-zero duration
            const animation = el.style.animation;
            if (animation && animation !== '' && !animation.includes('0ms')) return false;
            return true;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  it('non-reduced-motion elements have hover-transition and no motion-reduced', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.constantFrom('button', 'a', 'div'),
          { minLength: 1, maxLength: 10 }
        ),
        (tagNames) => {
          const elements = tagNames.map((tag) => createElement(tag));

          // Apply with reduced motion = false
          applyHoverClasses(elements, false);

          return elements.every((el) => {
            // hover-transition must be present
            if (!el.classList.contains('hover-transition')) return false;
            // motion-reduced must NOT be present
            if (el.classList.contains('motion-reduced')) return false;
            return true;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  it('IntersectionObserver is created iff reducedMotion is false', () => {
    fc.assert(
      fc.property(
        fc.boolean(),
        fc.array(fc.constant('animate-on-scroll'), { minLength: 1, maxLength: 5 }),
        (reducedMotion, _classes) => {
          const { MockObserver, observeMock } = createMockObserver();
          const elements = _classes.map(() => createElement('div', 'animate-on-scroll'));

          const observer = initIntersectionObserver(elements, reducedMotion, MockObserver);

          if (reducedMotion) {
            return observer === null && observeMock.mock.calls.length === 0;
          } else {
            return observer !== null && observeMock.mock.calls.length === elements.length;
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
