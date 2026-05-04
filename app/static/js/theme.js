/**
 * theme.js — Fetches the active ThemeConfig and applies it as CSS custom
 * properties on :root so every page reflects the stored theme.
 *
 * Requirements: 14.3, 14.6
 */

/**
 * Apply a ThemeConfig object to the document's :root element as CSS custom
 * properties.  Called both on page load and after an admin saves a new theme
 * (live preview without reload).
 *
 * @param {Object} config - ThemeConfig with accent_color, background_color, font_family
 */
export function applyTheme(config) {
  const root = document.documentElement;
  if (config.accent_color) {
    root.style.setProperty('--accent-color', config.accent_color);
  }
  if (config.background_color) {
    root.style.setProperty('--bg-color', config.background_color);
    root.style.setProperty('background-color', config.background_color);
    document.body.style.backgroundColor = config.background_color;
  }
  if (config.font_family) {
    root.style.setProperty('--font-family', config.font_family);
    document.body.style.fontFamily = `'${config.font_family}', system-ui, sans-serif`;
  }
}

/**
 * Fetch the active ThemeConfig from the public API and apply it.
 * Silently ignores network errors so a theme fetch failure never breaks the page.
 */
export async function loadAndApplyTheme() {
  try {
    const res = await fetch('/api/v1/theme');
    if (res.ok) {
      const config = await res.json();
      applyTheme(config);
    }
  } catch {
    // Theme fetch failed — continue with default styles
  }
}

// Auto-run on every page load
document.addEventListener('DOMContentLoaded', loadAndApplyTheme);
