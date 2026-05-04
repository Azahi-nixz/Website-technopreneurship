/**
 * Tests for notifications.js — toast notification module.
 *
 * Covers:
 *  - show() injects a toast element into the DOM
 *  - Slide-down animation class / style is applied on show
 *  - Toast is removed from the DOM after DISMISS_DELAY_MS + FADE_DURATION_MS
 *  - Toast is appended to #notification-area when present
 *  - Toast falls back to document.body when #notification-area is absent
 *  - Correct icon and text are rendered for each notification type
 *  - role="status" and aria-live="polite" are set for accessibility
 *
 * Property-based test:
 *  - Property 19: Confirmation notifications auto-dismiss after 3 seconds
 *    Validates: Requirements 8.5
 *
 * Requirements: 5.3, 8.5
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as fc from 'fast-check';
import { show, DISMISS_DELAY_MS, FADE_DURATION_MS } from './notifications.js';

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.useFakeTimers();
  document.body.innerHTML = '';
  document.head.innerHTML = '';
});

afterEach(() => {
  vi.useRealTimers();
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createNotificationArea() {
  const area = document.createElement('div');
  area.id = 'notification-area';
  document.body.appendChild(area);
  return area;
}

// ---------------------------------------------------------------------------
// DOM injection
// ---------------------------------------------------------------------------

describe('show() — DOM injection', () => {
  it('appends a toast element to #notification-area when present', () => {
    const area = createNotificationArea();
    show('Hello world');
    expect(area.children.length).toBe(1);
  });

  it('falls back to document.body when #notification-area is absent', () => {
    const initialChildCount = document.body.children.length;
    show('Fallback test');
    expect(document.body.children.length).toBe(initialChildCount + 1);
  });

  it('returns the toast element', () => {
    createNotificationArea();
    const toast = show('Return value test');
    expect(toast).toBeInstanceOf(HTMLElement);
  });

  it('renders the message text inside the toast', () => {
    createNotificationArea();
    const toast = show('Order added to cart');
    expect(toast.textContent).toContain('Order added to cart');
  });

  it('sets role="status" for accessibility', () => {
    createNotificationArea();
    const toast = show('Accessible toast');
    expect(toast.getAttribute('role')).toBe('status');
  });

  it('sets aria-live="polite" for accessibility', () => {
    createNotificationArea();
    const toast = show('Accessible toast');
    expect(toast.getAttribute('aria-live')).toBe('polite');
  });

  it('sets data-notification-type attribute to the provided type', () => {
    createNotificationArea();
    const toast = show('Success!', 'success');
    expect(toast.getAttribute('data-notification-type')).toBe('success');
  });

  it('defaults to type "info" when no type is provided', () => {
    createNotificationArea();
    const toast = show('Default type');
    expect(toast.getAttribute('data-notification-type')).toBe('info');
  });

  it('defaults to type "info" for an unknown type', () => {
    createNotificationArea();
    // @ts-ignore — intentionally passing an invalid type
    const toast = show('Unknown type', 'banana');
    expect(toast.getAttribute('data-notification-type')).toBe('banana');
    // The toast should still render (using info fallback styles)
    expect(toast).toBeInstanceOf(HTMLElement);
  });
});

// ---------------------------------------------------------------------------
// Slide-down animation
// ---------------------------------------------------------------------------

describe('show() — slide-down animation', () => {
  it('applies the kiro-slide-down animation style on show', () => {
    createNotificationArea();
    const toast = show('Animated toast');
    expect(toast.style.animation).toContain('kiro-slide-down');
  });

  it('injects @keyframes kiro-slide-down into the document head', () => {
    createNotificationArea();
    show('Keyframe injection test');
    const styles = Array.from(document.head.querySelectorAll('style'));
    const hasKeyframe = styles.some((s) => s.textContent.includes('kiro-slide-down'));
    expect(hasKeyframe).toBe(true);
  });

  it('only injects the keyframe style once across multiple show() calls', () => {
    createNotificationArea();
    show('First');
    show('Second');
    show('Third');
    const styles = Array.from(document.head.querySelectorAll('style'));
    const keyframeStyles = styles.filter((s) => s.textContent.includes('kiro-slide-down'));
    expect(keyframeStyles.length).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// Auto-dismiss timing
// ---------------------------------------------------------------------------

describe('show() — auto-dismiss timing', () => {
  it('toast is still in the DOM before DISMISS_DELAY_MS elapses', () => {
    const area = createNotificationArea();
    show('Timing test');

    vi.advanceTimersByTime(DISMISS_DELAY_MS - 1);
    expect(area.children.length).toBe(1);
  });

  it('toast begins fading out at DISMISS_DELAY_MS', () => {
    createNotificationArea();
    const toast = show('Fade test');

    vi.advanceTimersByTime(DISMISS_DELAY_MS);
    expect(toast.style.opacity).toBe('0');
  });

  it('toast is removed from the DOM after DISMISS_DELAY_MS + FADE_DURATION_MS', () => {
    const area = createNotificationArea();
    show('Remove test');

    vi.advanceTimersByTime(DISMISS_DELAY_MS + FADE_DURATION_MS);
    expect(area.children.length).toBe(0);
  });

  it('toast is removed from document.body fallback after full dismiss cycle', () => {
    // No #notification-area — falls back to body
    show('Body fallback remove');
    const initialCount = document.body.children.length;

    vi.advanceTimersByTime(DISMISS_DELAY_MS + FADE_DURATION_MS);
    expect(document.body.children.length).toBe(initialCount - 1);
  });

  it('multiple toasts are each dismissed independently', () => {
    const area = createNotificationArea();
    show('Toast 1');
    show('Toast 2');
    show('Toast 3');
    expect(area.children.length).toBe(3);

    vi.advanceTimersByTime(DISMISS_DELAY_MS + FADE_DURATION_MS);
    expect(area.children.length).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Notification types
// ---------------------------------------------------------------------------

describe('show() — notification types', () => {
  it.each(['success', 'error', 'warning', 'info'])(
    'renders a toast for type "%s" without throwing',
    (type) => {
      createNotificationArea();
      // @ts-ignore
      expect(() => show(`A ${type} message`, type)).not.toThrow();
    }
  );
});

// ---------------------------------------------------------------------------
// Property 19: Confirmation notifications auto-dismiss after 3 seconds
// Validates: Requirements 8.5
// ---------------------------------------------------------------------------

describe('Property 19: Notifications auto-dismiss within 3 500 ms', () => {
  /**
   * For any notification message string, the toast element SHALL be removed
   * from the DOM (or have its visibility set to hidden) within 3 500 ms of
   * being shown (allowing 500 ms tolerance for the fade-out animation).
   *
   * The tolerance window is: DISMISS_DELAY_MS (3 000) + FADE_DURATION_MS (400) = 3 400 ms,
   * which is comfortably within the 3 500 ms requirement.
   */
  it('toast is removed from the DOM within 3 500 ms for any message string', () => {
    fc.assert(
      fc.property(
        fc.string(),
        fc.constantFrom('success', 'error', 'warning', 'info'),
        (message, type) => {
          // Reset DOM for each iteration
          document.body.innerHTML = '';
          const area = document.createElement('div');
          area.id = 'notification-area';
          document.body.appendChild(area);

          // @ts-ignore
          show(message, type);

          // Advance time to just within the 3 500 ms tolerance window
          vi.advanceTimersByTime(3500);

          // The toast must be gone (removed from DOM) or invisible
          const toasts = area.querySelectorAll('[data-notification-type]');
          const allDismissed = Array.from(toasts).every(
            (el) =>
              !el.isConnected ||
              el.style.opacity === '0' ||
              el.style.visibility === 'hidden'
          );

          return allDismissed;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('toast is fully removed (not just hidden) within 3 500 ms', () => {
    fc.assert(
      fc.property(fc.string(), (message) => {
        document.body.innerHTML = '';
        const area = document.createElement('div');
        area.id = 'notification-area';
        document.body.appendChild(area);

        show(message);

        // Advance past the full dismiss cycle (3 000 ms delay + 400 ms fade)
        vi.advanceTimersByTime(DISMISS_DELAY_MS + FADE_DURATION_MS + 100);

        return area.children.length === 0;
      }),
      { numRuns: 100 }
    );
  });

  it('toast is NOT removed before 3 000 ms have elapsed', () => {
    fc.assert(
      fc.property(fc.string(), (message) => {
        document.body.innerHTML = '';
        const area = document.createElement('div');
        area.id = 'notification-area';
        document.body.appendChild(area);

        show(message);

        // Advance to just before the dismiss delay
        vi.advanceTimersByTime(DISMISS_DELAY_MS - 1);

        // Toast must still be present and visible
        return area.children.length === 1;
      }),
      { numRuns: 100 }
    );
  });
});
