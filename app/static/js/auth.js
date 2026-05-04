/**
 * auth.js — Reusable authentication utilities module.
 *
 * Provides shared auth helpers that any page can import:
 *  - checkAuth()              — fetch current user, update nav UI
 *  - requireAuth(action)      — gate an action behind authentication
 *  - completePendingAction()  — replay a saved action after login
 *  - logout()                 — POST /logout and redirect
 *  - handleLoginFormSubmit()  — attach a submit handler to a login form
 *  - handleRegisterFormSubmit() — attach a submit handler to a register form
 *  - redirectToLogin()        — redirect to /login with return_to param
 *
 * Requirements: 1.4, 5.3, 5.4, 5.7
 */

import api, { ApiError } from './api.js';

// ─── Constants ────────────────────────────────────────────────────────────────

/** sessionStorage key used to persist a pending action across the login redirect. */
const PENDING_ACTION_KEY = 'pending_action';

// ─── Notification helper ──────────────────────────────────────────────────────

/**
 * Display a brief toast notification in #notification-area.
 *
 * @param {string} message - The text to display.
 * @param {'success'|'error'|'info'} [type='info'] - Visual style variant.
 */
export function showNotification(message, type = 'info') {
  const area = document.getElementById('notification-area');
  if (!area) return;

  const colorMap = {
    success: 'bg-green-900/90 border-green-500/40 text-green-300',
    error:   'bg-red-900/90 border-red-500/40 text-red-300',
    info:    'bg-navy-800/95 border-gold-400/30 text-gray-200',
  };
  const colors = colorMap[type] ?? colorMap.info;

  const toast = document.createElement('div');
  toast.className = `border ${colors} px-4 py-3 rounded-lg text-sm shadow-lg`;
  toast.style.cssText = [
    'background:rgba(15,22,41,0.95)',
    'animation:slideDown 0.3s ease-out',
    'transition:opacity 0.5s',
  ].join(';');
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');
  toast.textContent = message;

  area.appendChild(toast);

  // Auto-dismiss after 3 s with a fade-out.
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 500);
  }, 3000);
}

// ─── Core auth helpers ────────────────────────────────────────────────────────

/**
 * Fetch the currently authenticated user from GET /api/v1/auth/me.
 *
 * Also updates nav UI elements when they exist on the page:
 *  - #user-menu-auth / #mobile-user-auth  — shown when logged in
 *  - #user-email-display / #mobile-user-email — populated with email
 *  - #login-link / #mobile-login-link     — hidden when logged in
 *
 * @returns {Promise<object|null>} The user object, or null if not authenticated.
 */
export async function checkAuth() {
  try {
    const user = await api.get('/api/v1/auth/me');

    // Update desktop nav
    const userMenuAuth = document.getElementById('user-menu-auth');
    if (userMenuAuth) {
      userMenuAuth.classList.remove('hidden');
      userMenuAuth.classList.add('flex');
    }
    const userEmailDisplay = document.getElementById('user-email-display');
    if (userEmailDisplay) userEmailDisplay.textContent = user.email || '';

    const loginLink = document.getElementById('login-link');
    if (loginLink) loginLink.classList.add('hidden');

    // Update mobile nav
    const mobileUserAuth = document.getElementById('mobile-user-auth');
    if (mobileUserAuth) {
      mobileUserAuth.classList.remove('hidden');
      mobileUserAuth.classList.add('flex');
    }
    const mobileUserEmail = document.getElementById('mobile-user-email');
    if (mobileUserEmail) mobileUserEmail.textContent = user.email || '';

    const mobileLoginLink = document.getElementById('mobile-login-link');
    if (mobileLoginLink) mobileLoginLink.classList.add('hidden');

    return user;
  } catch {
    // 401 is handled by api.js (redirect to /login); any other error means
    // we treat the user as unauthenticated without redirecting.
    return null;
  }
}

/**
 * Redirect the browser to /login, preserving the current path as `return_to`.
 *
 * @param {string} [returnTo] - The path to return to after login.
 *   Defaults to `window.location.pathname + window.location.search`.
 */
export function redirectToLogin(returnTo) {
  const path = returnTo ?? (window.location.pathname + window.location.search);
  window.location.href = `/login?return_to=${encodeURIComponent(path)}`;
}

/**
 * Gate an action behind authentication.
 *
 * If the user is not logged in, the pending action is serialised to
 * sessionStorage and the browser is redirected to /login.  After a
 * successful login, `completePendingAction()` will replay the action.
 *
 * @param {object|null} pendingAction - Describes the action to save, e.g.
 *   `{ type: 'add_to_cart', product_id: 42 }` or
 *   `{ type: 'buy_now', product_id: 42 }`.
 *   Pass `null` to redirect without saving an action.
 * @returns {Promise<boolean>} `true` if the user is authenticated (caller may
 *   proceed), `false` if a redirect was initiated.
 */
export async function requireAuth(pendingAction) {
  const user = await checkAuth();
  if (user) return true;

  if (pendingAction) {
    sessionStorage.setItem(PENDING_ACTION_KEY, JSON.stringify(pendingAction));
  }
  redirectToLogin();
  return false;
}

/**
 * Complete a pending action that was saved before the login redirect.
 *
 * Reads `pending_action` from sessionStorage, clears it, then executes:
 *  - `add_to_cart` → POST /api/v1/cart/items  (shows success notification)
 *  - `buy_now`     → POST /api/v1/orders/buy-now (redirects to confirmation)
 *
 * Does nothing if there is no pending action.
 *
 * @returns {Promise<void>}
 */
export async function completePendingAction() {
  const raw = sessionStorage.getItem(PENDING_ACTION_KEY);
  if (!raw) return;

  let action;
  try {
    action = JSON.parse(raw);
  } catch {
    // Corrupt data — discard silently.
    sessionStorage.removeItem(PENDING_ACTION_KEY);
    return;
  }

  // Clear before executing so a failure doesn't leave a stale action.
  sessionStorage.removeItem(PENDING_ACTION_KEY);

  if (!action?.type) return;

  try {
    if (action.type === 'add_to_cart') {
      await api.post('/api/v1/cart/items', {
        product_id: action.product_id,
        quantity: 1,
      });
      showNotification('Item added to your cart!', 'success');

    } else if (action.type === 'buy_now') {
      const data = await api.post('/api/v1/orders/buy-now', {
        product_id: action.product_id,
      });
      const orderId = data?.id ?? data?.order_id ?? '';
      window.location.href = `/order-confirmation?order_id=${orderId}`;
    }
  } catch (err) {
    const message = err instanceof ApiError
      ? err.message
      : 'Failed to complete your pending action. Please try again.';
    showNotification(message, 'error');
  }
}

/**
 * Log the current user out.
 *
 * POSTs to /api/v1/auth/logout (CSRF token is injected by api.js) then
 * redirects to /login.
 *
 * @returns {Promise<void>}
 */
export async function logout() {
  try {
    await api.post('/api/v1/auth/logout', {});
  } catch {
    // Proceed with redirect even if the server call fails.
  } finally {
    window.location.href = '/login';
  }
}

// ─── Form helpers ─────────────────────────────────────────────────────────────

/**
 * Attach a submit handler to a login `<form>` element.
 *
 * On submit the handler:
 *  1. Validates that email and password are non-empty.
 *  2. POSTs to /api/v1/auth/login via api.js.
 *  3. On success: calls `completePendingAction()`, then redirects to the
 *     `?return_to` query param (or `/` if absent).
 *  4. On failure: calls `options.onError(message)` if provided, otherwise
 *     shows a notification.
 *
 * @param {HTMLFormElement} formEl - The login form element.
 * @param {object} [options={}]
 * @param {function(object): void} [options.onSuccess] - Called with the
 *   server response after a successful login (before the redirect).
 * @param {function(string): void} [options.onError] - Called with an error
 *   message string on failure.
 */
export function handleLoginFormSubmit(formEl, options = {}) {
  if (!formEl) return;

  formEl.addEventListener('submit', async (e) => {
    e.preventDefault();

    const emailEl    = formEl.querySelector('[name="email"], [type="email"]');
    const passwordEl = formEl.querySelector('[name="password"], [type="password"]');

    const email    = emailEl?.value.trim() ?? '';
    const password = passwordEl?.value ?? '';

    if (!email || !password) {
      const msg = 'Please enter your email and password.';
      if (options.onError) {
        options.onError(msg);
      } else {
        showNotification(msg, 'error');
      }
      return;
    }

    try {
      const data = await api.post('/api/v1/auth/login', { email, password });

      if (options.onSuccess) options.onSuccess(data);

      // Complete any action the user was trying to perform before login.
      await completePendingAction();

      // Redirect to the originally requested page, or home.
      const returnTo = new URLSearchParams(window.location.search).get('return_to') || '/';
      window.location.href = returnTo;

    } catch (err) {
      const message = err instanceof ApiError
        ? err.message
        : 'Network error. Please check your connection and try again.';
      if (options.onError) {
        options.onError(message);
      } else {
        showNotification(message, 'error');
      }
    }
  });
}

/**
 * Attach a submit handler to a registration `<form>` element.
 *
 * On submit the handler:
 *  1. Validates email is non-empty and password is ≥ 8 characters.
 *  2. POSTs to /api/v1/auth/register via api.js.
 *  3. On success: calls `options.onSuccess(data)` if provided (e.g. to switch
 *     to the login tab and show a success message).
 *  4. On failure: calls `options.onError(message)` if provided, otherwise
 *     shows a notification.
 *
 * @param {HTMLFormElement} formEl - The registration form element.
 * @param {object} [options={}]
 * @param {function(object): void} [options.onSuccess] - Called with the
 *   server response after successful registration.
 * @param {function(string): void} [options.onError] - Called with an error
 *   message string on failure.
 */
export function handleRegisterFormSubmit(formEl, options = {}) {
  if (!formEl) return;

  formEl.addEventListener('submit', async (e) => {
    e.preventDefault();

    const emailEl    = formEl.querySelector('[name="email"], [type="email"]');
    const passwordEl = formEl.querySelector('[name="password"], [type="password"]');

    const email    = emailEl?.value.trim() ?? '';
    const password = passwordEl?.value ?? '';

    if (!email) {
      const msg = 'Please enter a valid email address.';
      if (options.onError) {
        options.onError(msg);
      } else {
        showNotification(msg, 'error');
      }
      return;
    }

    if (password.length < 8) {
      const msg = 'Password must be at least 8 characters.';
      if (options.onError) {
        options.onError(msg);
      } else {
        showNotification(msg, 'error');
      }
      return;
    }

    try {
      const data = await api.post('/api/v1/auth/register', { email, password });

      if (options.onSuccess) {
        options.onSuccess(data);
      } else {
        showNotification('Account created! Please sign in.', 'success');
      }

    } catch (err) {
      const message = err instanceof ApiError
        ? err.message
        : 'Network error. Please check your connection and try again.';
      if (options.onError) {
        options.onError(message);
      } else {
        showNotification(message, 'error');
      }
    }
  });
}
