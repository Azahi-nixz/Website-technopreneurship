/**
 * notifications.js — Toast notification module.
 *
 * Exposes a single `show(message, type)` function that:
 *  - Injects a toast element into the DOM (appended to #notification-area,
 *    or to document.body if that container is absent)
 *  - Applies a slide-down CSS animation on show
 *  - Auto-dismisses the notification after 3 000 ms with a fade-out animation
 *  - Removes the element from the DOM after the fade-out completes
 *
 * Supported types: 'success' | 'error' | 'info' | 'warning'
 * Defaults to 'info' for unknown types.
 *
 * Requirements: 5.3, 8.5
 */

/** @typedef {'success' | 'error' | 'info' | 'warning'} NotificationType */

/**
 * Duration (ms) before the fade-out animation begins.
 * Exported so tests can reference the same constant.
 */
export const DISMISS_DELAY_MS = 3000;

/**
 * Duration (ms) of the fade-out animation.
 * The element is removed from the DOM after this period.
 * Exported so tests can reference the same constant.
 */
export const FADE_DURATION_MS = 400;

// ---------------------------------------------------------------------------
// Inline styles — avoids a dependency on an external stylesheet while still
// producing the required slide-down and fade-out animations.
// ---------------------------------------------------------------------------

/** @type {Record<NotificationType, { bg: string; border: string; text: string; icon: string }>} */
const TYPE_STYLES = {
  success: {
    bg: 'rgba(6, 78, 59, 0.95)',
    border: 'rgba(52, 211, 153, 0.4)',
    text: '#6ee7b7',
    icon: '✓',
  },
  error: {
    bg: 'rgba(127, 29, 29, 0.95)',
    border: 'rgba(248, 113, 113, 0.4)',
    text: '#fca5a5',
    icon: '✕',
  },
  warning: {
    bg: 'rgba(120, 53, 15, 0.95)',
    border: 'rgba(251, 191, 36, 0.4)',
    text: '#fde68a',
    icon: '⚠',
  },
  info: {
    bg: 'rgba(15, 22, 41, 0.95)',
    border: 'rgba(96, 165, 250, 0.4)',
    text: '#93c5fd',
    icon: 'ℹ',
  },
};

// ---------------------------------------------------------------------------
// CSS keyframe injection (once per page load)
// ---------------------------------------------------------------------------

let _keyframesInjected = false;

/**
 * Inject the @keyframes rule for the slide-down animation into the document
 * <head> the first time a notification is shown.
 */
function ensureKeyframes() {
  if (_keyframesInjected) return;
  _keyframesInjected = true;

  const style = document.createElement('style');
  style.textContent = `
    @keyframes kiro-slide-down {
      from {
        opacity: 0;
        transform: translateY(-16px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `;
  document.head.appendChild(style);
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Display a toast notification.
 *
 * @param {string} message - The text to display inside the toast.
 * @param {NotificationType} [type='info'] - Visual style variant.
 * @returns {HTMLElement} The toast element (useful for testing).
 */
export function show(message, type = 'info') {
  ensureKeyframes();

  const styles = TYPE_STYLES[type] ?? TYPE_STYLES.info;

  // -------------------------------------------------------------------------
  // Build the toast element
  // -------------------------------------------------------------------------
  const toast = document.createElement('div');
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');
  toast.setAttribute('data-notification-type', type);

  // Base layout styles
  toast.style.cssText = [
    `background:${styles.bg}`,
    `border:1px solid ${styles.border}`,
    `color:${styles.text}`,
    'padding:12px 16px',
    'border-radius:8px',
    'font-size:0.875rem',
    'line-height:1.5',
    'box-shadow:0 8px 24px rgba(0,0,0,0.4)',
    'display:flex',
    'align-items:center',
    'gap:10px',
    'min-width:240px',
    'max-width:420px',
    'pointer-events:auto',
    // Slide-down animation
    `animation:kiro-slide-down 300ms cubic-bezier(0.16,1,0.3,1) both`,
  ].join(';');

  // Icon span
  const icon = document.createElement('span');
  icon.setAttribute('aria-hidden', 'true');
  icon.style.cssText = 'font-size:1rem;flex-shrink:0;';
  icon.textContent = styles.icon;
  toast.appendChild(icon);

  // Message span
  const msg = document.createElement('span');
  msg.textContent = message;
  toast.appendChild(msg);

  // -------------------------------------------------------------------------
  // Mount into the DOM
  // -------------------------------------------------------------------------
  const container = document.getElementById('notification-area') ?? document.body;
  container.appendChild(toast);

  // -------------------------------------------------------------------------
  // Auto-dismiss: fade out after DISMISS_DELAY_MS, then remove from DOM
  // -------------------------------------------------------------------------
  const dismissTimer = setTimeout(() => {
    // Begin fade-out
    toast.style.transition = `opacity ${FADE_DURATION_MS}ms ease, transform ${FADE_DURATION_MS}ms ease`;
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-8px)';

    // Remove from DOM after the fade-out completes
    const removeTimer = setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, FADE_DURATION_MS);

    // Expose the inner timer ID on the element for testing convenience
    toast._removeTimer = removeTimer;
  }, DISMISS_DELAY_MS);

  // Expose timer IDs on the element so tests can inspect / fast-forward them
  toast._dismissTimer = dismissTimer;

  return toast;
}

export default { show };
