/**
 * gallery.js — Product image slideshow module.
 *
 * Exports a pure state-machine API (init, advance, goTo) for testability,
 * plus a createGallery() function that wires the state machine to the DOM.
 *
 * State machine:
 *   { images: string[], currentIndex: number, timerId: number|null }
 *
 * Behaviour:
 *   - init(images)              → initial state (index 0, no timer)
 *   - advance(state)            → new state with index incremented mod N
 *   - goTo(state, index, setInterval, clearInterval) → new state at index,
 *       old timer cancelled, new 15 000 ms timer started (if images.length > 1)
 *   - createGallery(container, images) → mounts DOM, wires up events
 *
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7
 */

// ---------------------------------------------------------------------------
// Placeholder SVG used when an image fails to load or no images are provided.
// ---------------------------------------------------------------------------
const PLACEHOLDER_SVG =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300' " +
  "viewBox='0 0 400 300'%3E%3Crect fill='%231A2340' width='400' height='300'/%3E" +
  "%3Ctext fill='%23D4AF37' font-size='14' x='50%25' y='50%25' text-anchor='middle' " +
  "dy='.3em'%3ENo Image%3C/text%3E%3C/svg%3E";

// ---------------------------------------------------------------------------
// Pure state-machine helpers
// ---------------------------------------------------------------------------

/**
 * Create the initial gallery state.
 *
 * @param {string[]} images - Ordered array of image URLs.
 * @returns {{ images: string[], currentIndex: number, timerId: number|null }}
 */
export function init(images) {
  return {
    images: Array.isArray(images) ? images : [],
    currentIndex: 0,
    timerId: null,
  };
}

/**
 * Advance to the next image (circular).
 * Returns a new state object — does NOT mutate the original.
 *
 * @param {{ images: string[], currentIndex: number, timerId: number|null }} state
 * @returns {{ images: string[], currentIndex: number, timerId: number|null }}
 */
export function advance(state) {
  const n = state.images.length;
  if (n === 0) return { ...state };
  return {
    ...state,
    currentIndex: (state.currentIndex + 1) % n,
  };
}

/**
 * Jump to a specific image index.
 * Cancels the existing timer (if any) and starts a fresh 15 000 ms timer
 * (only when images.length > 1).
 * Returns a new state object — does NOT mutate the original.
 *
 * @param {{ images: string[], currentIndex: number, timerId: number|null }} state
 * @param {number} index - Target image index.
 * @param {Function} setIntervalFn - Injected setInterval (for testability).
 * @param {Function} clearIntervalFn - Injected clearInterval (for testability).
 * @returns {{ images: string[], currentIndex: number, timerId: number|null }}
 */
export function goTo(state, index, setIntervalFn, clearIntervalFn) {
  // Cancel existing timer.
  if (state.timerId !== null) {
    clearIntervalFn(state.timerId);
  }

  // Start a fresh timer only when there is more than one image.
  let newTimerId = null;
  if (state.images.length > 1) {
    newTimerId = setIntervalFn(() => {}, 15000);
  }

  return {
    ...state,
    currentIndex: index,
    timerId: newTimerId,
  };
}

// ---------------------------------------------------------------------------
// DOM component
// ---------------------------------------------------------------------------

/**
 * Mount a gallery into `container`.
 *
 * - Empty / null images → renders a placeholder element (.gallery-placeholder).
 * - Single image        → renders a static <img>; no timer, no nav controls.
 * - Multiple images     → renders a sliding track, dots, prev/next arrows,
 *                         and starts a 15 000 ms auto-advance timer.
 *
 * @param {HTMLElement} container - The element to render into.
 * @param {string[]|null} images  - Ordered array of image URLs.
 */
export function createGallery(container, images) {
  // Normalise input.
  const imgs = Array.isArray(images) ? images : [];

  // ── Empty ──────────────────────────────────────────────────────────────────
  if (imgs.length === 0) {
    const placeholder = document.createElement('div');
    placeholder.className = 'gallery-placeholder w-full h-full flex items-center justify-center bg-navy-700';
    placeholder.setAttribute('aria-label', 'No product images available');
    const label = document.createElement('span');
    label.className = 'text-gray-600 text-sm';
    label.textContent = 'No image';
    placeholder.appendChild(label);
    container.appendChild(placeholder);
    return;
  }

  // ── Single image ───────────────────────────────────────────────────────────
  if (imgs.length === 1) {
    const img = document.createElement('img');
    img.src = imgs[0];
    img.alt = 'Product image';
    img.loading = 'lazy';
    img.className = 'w-full h-full object-cover';
    img.onerror = () => { img.src = PLACEHOLDER_SVG; };
    container.appendChild(img);
    // No timer, no nav controls — requirement 4.7.
    return;
  }

  // ── Multiple images ────────────────────────────────────────────────────────
  let state = init(imgs);

  // Track (slides laid out horizontally).
  const track = document.createElement('div');
  track.className = 'gallery-track';
  track.style.cssText = 'display:flex;height:100%;transition:transform 500ms cubic-bezier(0.4,0,0.2,1);';

  imgs.forEach((url, i) => {
    const slide = document.createElement('div');
    slide.className = 'gallery-slide';
    slide.style.cssText = 'flex-shrink:0;width:100%;height:100%;';
    const img = document.createElement('img');
    img.src = url;
    img.alt = `Product image ${i + 1}`;
    img.loading = 'lazy';
    img.style.cssText = 'width:100%;height:100%;object-fit:cover;';
    img.onerror = () => { img.src = PLACEHOLDER_SVG; };
    slide.appendChild(img);
    track.appendChild(slide);
  });

  // Navigation dots.
  const dotsContainer = document.createElement('div');
  dotsContainer.className = 'gallery-dots';
  dotsContainer.style.cssText =
    'position:absolute;bottom:8px;left:50%;transform:translateX(-50%);display:flex;gap:6px;';

  const dots = imgs.map((_, i) => {
    const dot = document.createElement('button');
    dot.className = 'gallery-dot' + (i === 0 ? ' active' : '');
    dot.setAttribute('aria-label', `Go to image ${i + 1}`);
    dot.style.cssText =
      'width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,0.4);' +
      'border:none;cursor:pointer;transition:background 0.2s,transform 0.2s;' +
      'min-width:20px;min-height:20px;display:flex;align-items:center;justify-content:center;';
    dot.addEventListener('click', () => navigateTo(i));
    dotsContainer.appendChild(dot);
    return dot;
  });

  // Previous button.
  const prevBtn = document.createElement('button');
  prevBtn.className = 'gallery-prev gallery-arrow';
  prevBtn.setAttribute('aria-label', 'Previous image');
  prevBtn.style.cssText =
    'position:absolute;top:50%;left:4px;transform:translateY(-50%);' +
    'background:rgba(10,14,26,0.7);border:1px solid rgba(212,175,55,0.3);' +
    'color:#D4AF37;border-radius:50%;width:32px;height:32px;' +
    'min-width:44px;min-height:44px;display:flex;align-items:center;' +
    'justify-content:center;cursor:pointer;transition:background 0.2s,transform 0.2s;';
  prevBtn.innerHTML =
    '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">' +
    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>';
  prevBtn.addEventListener('click', () =>
    navigateTo((state.currentIndex - 1 + imgs.length) % imgs.length)
  );

  // Next button.
  const nextBtn = document.createElement('button');
  nextBtn.className = 'gallery-next gallery-arrow';
  nextBtn.setAttribute('aria-label', 'Next image');
  nextBtn.style.cssText =
    'position:absolute;top:50%;right:4px;transform:translateY(-50%);' +
    'background:rgba(10,14,26,0.7);border:1px solid rgba(212,175,55,0.3);' +
    'color:#D4AF37;border-radius:50%;width:32px;height:32px;' +
    'min-width:44px;min-height:44px;display:flex;align-items:center;' +
    'justify-content:center;cursor:pointer;transition:background 0.2s,transform 0.2s;';
  nextBtn.innerHTML =
    '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">' +
    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>';
  nextBtn.addEventListener('click', () =>
    navigateTo((state.currentIndex + 1) % imgs.length)
  );

  // Assemble DOM.
  container.appendChild(track);
  container.appendChild(dotsContainer);
  container.appendChild(prevBtn);
  container.appendChild(nextBtn);

  // Apply initial transform.
  applyTransition(track, dots, state.currentIndex);

  /**
   * Navigate to a specific index: cancel old timer, update DOM, start new timer.
   * @param {number} index
   */
  function navigateTo(index) {
    state = goTo(state, index, setInterval, clearInterval);
    applyTransition(track, dots, state.currentIndex);

    // The goTo helper stores a dummy callback; replace the timer with the real one.
    if (state.timerId !== null) {
      clearInterval(state.timerId);
    }
    state = {
      ...state,
      timerId: setInterval(() => navigateTo((state.currentIndex + 1) % imgs.length), 15000),
    };
  }

  // Start the initial auto-advance timer (images.length > 1 guaranteed here).
  state = {
    ...state,
    timerId: setInterval(() => navigateTo((state.currentIndex + 1) % imgs.length), 15000),
  };
}

/**
 * Apply the horizontal slide transform and update dot active states.
 *
 * @param {HTMLElement} track - The .gallery-track element.
 * @param {HTMLElement[]} dots - Array of dot button elements.
 * @param {number} index - The current image index.
 */
export function applyTransition(track, dots, index) {
  track.style.transform = `translateX(-${index * 100}%)`;
  dots.forEach((dot, i) => {
    if (i === index) {
      dot.classList.add('active');
      dot.style.background = '#D4AF37';
      dot.style.transform = 'scale(1.2)';
    } else {
      dot.classList.remove('active');
      dot.style.background = 'rgba(255,255,255,0.4)';
      dot.style.transform = 'scale(1)';
    }
  });
}
