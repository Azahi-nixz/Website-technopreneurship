/**
 * content.js — Fetches the active ContentConfig and populates all
 * [data-content-key] elements so every page reflects the stored content.
 *
 * Requirements: 16.2, 16.4
 */

/**
 * Apply a ContentConfig object to the DOM.
 * Every element with a [data-content-key] attribute has its textContent set
 * to the corresponding field value from the config.
 * Also updates document.title if site_title is present.
 *
 * @param {Object} config - ContentConfig object
 */
export function applyContent(config) {
  if (config.site_title) {
    document.title = config.site_title;
  }

  document.querySelectorAll('[data-content-key]').forEach(el => {
    const key = el.getAttribute('data-content-key');
    if (key && config[key] !== undefined) {
      el.textContent = config[key];
    }
  });
}

/**
 * Fetch the active ContentConfig from the public API and apply it.
 * Silently ignores network errors so a content fetch failure never breaks the page.
 */
export async function loadAndApplyContent() {
  try {
    const res = await fetch('/api/v1/content');
    if (res.ok) {
      const config = await res.json();
      applyContent(config);
    }
  } catch {
    // Content fetch failed — continue with default HTML text
  }
}

// Auto-run on every page load
document.addEventListener('DOMContentLoaded', loadAndApplyContent);
