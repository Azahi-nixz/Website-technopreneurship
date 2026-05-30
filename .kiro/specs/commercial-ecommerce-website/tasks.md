# Implementation Plan: Commercial E-Commerce Website

## Overview

Implement a Flask + PostgreSQL e-commerce platform with a Tailwind CSS / vanilla JavaScript frontend. The plan follows the layered architecture (routes → services → repositories) defined in the design, building incrementally from the database schema up through the API, then the frontend, and finally wiring everything together. Property-based tests (Hypothesis for Python, fast-check for JavaScript) are included as optional sub-tasks alongside each implementation step.

---

## Tasks

- [x] 1. Project scaffolding and database schema
  - Create the Flask application package structure: `app/`, `app/routes/`, `app/services/`, `app/repositories/`, `app/models/`, `app/schemas/`, `app/static/`
  - Create `requirements.txt` pinning Flask, psycopg2-binary, bcrypt, marshmallow, Flask-Session, pytest, hypothesis, and other dependencies
  - Write `app/db.py` with a `get_connection()` helper that returns a psycopg2 connection using environment variables
  - Write `migrations/001_initial_schema.sql` containing the full DDL from the design (users, products, product_images, cart_items, orders, order_items tables with all constraints and foreign keys)
  - Write a `scripts/init_db.py` script that applies the migration against the configured database
  - Create `vitest.config.js` and `package.json` with vitest and fast-check as dev dependencies
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ] 2. Python domain models and marshmallow schemas
  - [x] 2.1 Implement Python dataclasses in `app/models/`
    - Write `User`, `Product`, `ProductImage`, `CartItem`, `Order`, `OrderItem` dataclasses matching the design
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [x] 2.2 Implement marshmallow schemas in `app/schemas/`
    - Write request/response schemas for auth (RegisterSchema, LoginSchema), products (ProductSchema, ProductImageSchema), cart (CartItemSchema, AddToCartSchema, UpdateCartItemSchema), and orders (OrderSchema, OrderItemSchema, BuyNowSchema)
    - Ensure all schemas validate required fields, types, and constraints (email format, password min length 8, quantity ≥ 1, price ≥ 0)
    - _Requirements: 9.4, 11.5_



- [-] 3. Repository layer
  - [x] 3.1 Implement `app/repositories/user_repository.py`
    - Write `create_user(email, password_hash) -> User`, `find_by_email(email) -> Optional[User]`, `find_by_id(user_id) -> Optional[User]` using parameterized queries
    - _Requirements: 1.1, 1.2, 11.4_

  - [x] 3.2 Implement `app/repositories/product_repository.py`
    - Write `list_active() -> List[Product]`, `find_by_id(product_id) -> Optional[Product]`, `get_images(product_id) -> List[ProductImage]` using parameterized queries
    - _Requirements: 3.1, 4.1, 11.4_

  - [x] 3.3 Implement `app/repositories/cart_repository.py`
    - Write `get_cart(user_id) -> List[CartItem]`, `add_item(user_id, product_id, quantity) -> CartItem`, `update_item(cart_item_id, quantity) -> CartItem`, `remove_item(cart_item_id) -> None`, `clear_cart(user_id) -> None` using parameterized queries
    - _Requirements: 6.1, 6.3, 6.4, 11.4_

  - [x] 3.4 Implement `app/repositories/order_repository.py`
    - Write `create_order(user_id, items, total_amount) -> Order`, `find_by_id(order_id) -> Optional[Order]`, `list_by_user(user_id) -> List[Order]` (sorted descending by `created_at`) using parameterized queries
    - _Requirements: 7.1, 7.3, 11.4_



- [x] 4. Auth service and routes
  - [x] 4.1 Implement `app/services/auth_service.py`
    - Write `hash_password(password) -> bytes` using bcrypt at cost factor ≥ 12
    - Write `register(email, password) -> User` (raises `ConflictError` on duplicate email)
    - Write `login(email, password) -> Session` (raises `AuthError` on invalid credentials with generic message)
    - Write `logout(session_id) -> None` and `get_current_user(session_id) -> Optional[User]`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 11.2_

  - [x] 4.7 Implement `app/routes/auth_routes.py`
    - Register Blueprint at `/api/v1/auth`
    - Implement `POST /register`, `POST /login`, `POST /logout`, `GET /me`
    - Apply RegisterSchema / LoginSchema validation; return consistent JSON error envelope on failures
    - Set session cookie with `HttpOnly`, `Secure`, `SameSite=Strict` attributes
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6, 9.1, 9.2, 9.3, 11.2_

- [x] 5. Checkpoint — auth layer complete
  - Ensure all auth tests pass, ask the user if questions arise.

- [ ] 6. Product service and routes
  - [x] 6.1 Implement `app/services/product_service.py`
    - Write `list_active_products() -> List[Product]` and `get_product(product_id) -> Product` (raises `NotFoundError` if missing or inactive)
    - Write `get_product_images(product_id) -> List[ProductImage]`
    - _Requirements: 3.1, 4.1_

  - [x] 6.3 Implement `app/routes/product_routes.py`
    - Register Blueprint at `/api/v1/products`
    - Implement `GET /` (list active products) and `GET /<id>` (single product with images)
    - Return 404 with `NOT_FOUND` code for unknown or inactive product IDs
    - _Requirements: 3.1, 9.1, 9.2_

- [ ] 7. Order service and routes (cart + orders)
  - [x] 7.1 Implement `app/services/order_service.py`
    - Write `get_cart`, `add_to_cart`, `update_cart_item`, `remove_from_cart`, `place_order`, `buy_now`, `get_order_history` as specified in the design
    - `place_order` must snapshot unit prices at time of order creation and clear the cart atomically
    - `buy_now` creates an order with quantity 1 at the product's current price
    - `get_order_history` returns orders sorted descending by `created_at`
    - _Requirements: 5.2, 5.3, 6.1, 6.3, 6.4, 7.1, 7.3_

  - [x] 7.8 Implement `app/routes/cart_routes.py`
    - Register Blueprint at `/api/v1/cart`
    - Implement `GET /`, `POST /items`, `PUT /items/<id>`, `DELETE /items/<id>`
    - Require authentication on all endpoints; return 401 for unauthenticated requests
    - _Requirements: 6.1, 6.3, 6.4, 9.1, 9.2_

  - [x] 7.9 Implement `app/routes/order_routes.py`
    - Register Blueprint at `/api/v1/orders`
    - Implement `POST /` (place order from cart), `POST /buy-now`, `GET /`, `GET /<id>`
    - Require authentication; return 404 for unknown order IDs
    - _Requirements: 5.2, 7.1, 7.2, 7.3, 7.4, 9.1, 9.2_

- [ ] 8. CSRF protection and global error handling
  - [x] 8.1 Implement CSRF middleware in `app/middleware/csrf.py`
    - Generate a per-session CSRF token and expose it via a cookie or meta tag
    - Reject POST, PUT, DELETE requests missing or presenting an invalid token with 403 and `CSRF_INVALID` code
    - _Requirements: 11.3_

  - [x] 8.3 Implement global error handlers in `app/errors.py`
    - Register handlers for 400, 401, 403, 404, 409, 500 that return the standard JSON error envelope (`code`, `message`, `details`, `trace_id`)
    - Log 500 errors with full stack trace and `trace_id`
    - _Requirements: 7.5, 9.2, 9.3_



- [x] 9. Checkpoint — backend API complete
  - Ensure all backend tests pass (pytest), ask the user if questions arise.

- [x] 10. Frontend HTML pages and Tailwind CSS setup
  - Create `app/static/index.html` (product listing), `app/static/login.html`, `app/static/cart.html`, `app/static/orders.html`, `app/static/order-confirmation.html`
  - Configure Tailwind CSS (tailwind.config.js, input CSS file, build script in package.json)
  - Implement the Login_Page layout: full-viewport background image, centered semi-transparent card, brand name, submit button with 300ms hover transition
  - Implement the product listing page: responsive grid (1 col at 320px → 4 cols at 1280px+), Product_Card component with name, price, and action buttons
  - Implement the cart page: item list with image, name, unit price, quantity selector, line total, remove button, running total, and empty-cart state
  - Implement the order history page and order confirmation page layouts
  - Ensure all interactive elements have minimum 44×44 px touch targets and all text meets WCAG 2.1 AA contrast ratio ≥ 4.5:1
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.2, 3.4, 6.2, 6.5, 6.6, 7.2, 7.4, 12.1, 12.2, 12.3, 12.4_

- [x] 11. JavaScript module: `api.js`
  - Write `app/static/js/api.js` as a fetch wrapper that:
    - Reads the CSRF token from the cookie or meta tag and injects it as a request header on POST/PUT/DELETE
    - Handles 401 responses by redirecting to `/login?return_to=<current_path>`
    - Handles 403 CSRF errors by refreshing the token and retrying once
    - Handles network errors by displaying a toast notification with a retry option
    - Returns parsed JSON or throws a typed error object
  - _Requirements: 9.1, 11.3, 11.5_

- [-] 12. JavaScript module: `gallery.js`
  - [ ] 12.1 Implement `app/static/js/gallery.js`
    - Write `init(container, images)`, `advance()`, `goTo(index)`, `applyTransition()` as specified in the design
    - Auto-advance timer set to 15 000 ms; timer only started when `images.length > 1`
    - `goTo` cancels existing timer and starts a fresh one
    - Render navigation dots/arrows only when `images.length > 1`
    - Apply 500ms horizontal slide CSS transition on image change
    - Handle image load errors with a placeholder image
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_



- [ ] 13. JavaScript module: `cart.js`
  - Write `app/static/js/cart.js` that:
    - Fetches cart data from `GET /api/v1/cart` on page load
    - Renders each cart item with image, name, unit price, quantity input, line total, and remove button
    - Calls `PUT /api/v1/cart/items/<id>` on quantity change and recalculates the displayed total immediately
    - Calls `DELETE /api/v1/cart/items/<id>` on remove and removes the item from the DOM
    - Displays the running total formatted to two decimal places with currency symbol
    - Renders the empty-cart state with a CTA link when the cart is empty
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 14. JavaScript module: `auth.js`
  - Write `app/static/js/auth.js` that:
    - Handles login and registration form submission via `api.js`
    - Redirects to the product listing page after successful login
    - Redirects unauthenticated users to `/login?return_to=<current_path>` when they attempt cart or buy actions
    - Preserves the intended action (add-to-cart or buy) in `sessionStorage` and completes it after login
  - _Requirements: 1.4, 5.3, 5.4, 5.7_

- [ ] 15. JavaScript module: `notifications.js`
  - Write `app/static/js/notifications.js` that:
    - Exposes a `show(message, type)` function that injects a toast element into the DOM
    - Applies a slide-down CSS animation on show
    - Auto-dismisses the notification after 3 000 ms with a fade-out animation
    - Removes the element from the DOM after the fade-out completes
  - _Requirements: 5.3, 8.5_



- [-] 16. JavaScript module: `animations.js`
  - Write `app/static/js/animations.js` that:
    - Uses `IntersectionObserver` to apply fade-in or slide-up CSS animations to page sections when they first enter the viewport
    - Checks `window.matchMedia('(prefers-reduced-motion: reduce)')` and skips all non-essential animations when true
    - Applies hover transitions (150–300ms) to buttons, links, and Product_Cards via CSS classes
    - Applies underline slide-in animation to navigation links on hover
  - _Requirements: 8.1, 8.2, 8.3, 8.4_





- [x] 18. Flask application factory and static file serving
  - Write `app/__init__.py` as an application factory (`create_app(config)`) that:
    - Registers all Blueprints (auth, products, cart, orders)
    - Registers the CSRF middleware and global error handlers
    - Configures Flask-Session with the database or Redis backend
    - Serves static assets from `/static/` and routes all non-API paths to the appropriate HTML page
  - Write `config.py` with `DevelopmentConfig` and `ProductionConfig` classes (reads from environment variables)
  - Write `run.py` as the application entry point
  - _Requirements: 9.1, 9.5, 11.1, 11.2_



---

## Requirement 13 — Admin-Only Product Management

- [x] 21. Database migration: add `is_admin` flag and seed admin credentials
  - [x] 21.1 Write `migrations/002_add_is_admin.sql`
    - Add `is_admin BOOLEAN NOT NULL DEFAULT FALSE` column to the `users` table
    - _Requirements: 13.1, 10.1_

  - [x] 21.2 Update `app/models/user.py` to include `is_admin: bool` field
    - Add `is_admin: bool` to the `User` dataclass
    - _Requirements: 13.1_

  - [x] 21.3 Update `app/repositories/user_repository.py` to read/write `is_admin`
    - Update `_row_to_user` to map the `is_admin` column
    - Update `create_user` to accept and persist an optional `is_admin` parameter (default `False`)
    - Add `find_admin_by_email(email) -> Optional[User]` helper
    - _Requirements: 13.1, 13.4_

  - [x] 21.4 Seed admin user from environment variables on application startup
    - In `app/__init__.py` `create_app()`, after blueprints are registered, call a `seed_admin()` helper
    - `seed_admin()` reads `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `os.environ`; if the user does not exist, creates it with `is_admin=True`; if it exists but `is_admin` is `False`, updates the flag
    - _Requirements: 13.1_

- [x] 22. Admin route guard and `AdminService`
  - [x] 22.1 Implement `app/services/admin_service.py`
    - Write `is_admin_session(session: dict) -> bool` — returns `session.get("is_admin") is True`
    - Write `list_all_products() -> List[Product]` — delegates to `product_repository.list_all()`
    - Write `create_product(name, price, description) -> Product`
    - Write `update_product(product_id, **fields) -> Product` (raises `NotFoundError` if missing)
    - Write `delete_product(product_id) -> None` (raises `NotFoundError` if missing)
    - Write `add_product_image_file(product_id, file_data, extension) -> ProductImage` — validates extension (jpg/png/gif/webp) and size (≤ 10 MB), saves to `/static/uploads/`, delegates to `product_repository.add_image()`
    - Write `add_product_image_url(product_id, image_url) -> ProductImage`
    - Write `remove_product_image(product_id, image_id) -> None`
    - _Requirements: 13.3, 13.9, 13.10_

  - [x] 22.2 Add `require_admin` decorator in `app/routes/admin_routes.py`
    - Decorator checks `session.get("is_admin") is True`; returns 403 JSON with `FORBIDDEN` code if not
    - _Requirements: 13.3, 13.6_



- [x] 23. Admin REST endpoints for product management
  - [x] 23.1 Implement admin product routes in `app/routes/admin_routes.py`
    - Register Blueprint at `/api/v1/admin`
    - `GET /api/v1/admin/products` — list all products (active + inactive); requires admin session
    - `POST /api/v1/admin/products` — create product; validate name (required, non-empty) and price (required, ≥ 0); return 201 on success
    - `PUT /api/v1/admin/products/<id>` — update product fields; return 404 if not found
    - `DELETE /api/v1/admin/products/<id>` — delete product; return 404 if not found
    - `POST /api/v1/admin/products/<id>/images` — accept multipart file upload or JSON `image_url`; validate file type and size; save to `/static/uploads/`
    - `DELETE /api/v1/admin/products/<id>/images/<img_id>` — remove image; return 404 if not found
    - _Requirements: 13.3, 13.9, 13.10, 9.1, 9.2_



- [x] 24. Update `app/routes/auth_routes.py` to set `is_admin` in session on login
  - In the `POST /api/v1/auth/login` handler, after successful authentication, set `session["is_admin"] = user.is_admin`
  - In `GET /api/v1/auth/me`, include `is_admin` in the response JSON
  - _Requirements: 13.4, 13.5_

- [x] 25. Admin_Panel UI — Product_Tab
  - [x] 25.1 Create `app/static/js/admin.js`
    - Implement `openAdminPanel()` — show admin modal, activate Product_Tab by default, call `adminLoadProducts()`
    - Implement `closeAdminPanel()` — hide modal, reset state
    - Implement `switchTab(tabName)` — remove `active` class from all tab buttons and hide all panels, then add `active` class to the selected tab button and show its panel
    - Implement `adminLoadProducts()` — `GET /api/v1/admin/products`, render product list rows or empty-state; on fetch failure show inline error with retry button
    - Implement `adminSaveProduct()` — `POST` or `PUT` to admin products endpoint; show inline validation errors without closing the form on 400; refresh list on success
    - Implement `adminCancelEdit()` — clear edit state, reset form
    - Implement `openImageModal(productId)` — show image upload modal for the given product
    - Implement `adminAddImageUrl()` — `POST` image URL to `/api/v1/admin/products/<id>/images`
    - Implement `adminRemoveImage(productId, imageId)` — `DELETE` image, refresh image list
    - _Requirements: 13.5, 13.6, 13.7, 13.8, 13.9, 13.10, 13.11, 15.1, 15.2, 15.3, 15.4, 15.5_

  - [x] 25.2 Update `index.html` to conditionally render admin UI elements
    - Show the "⚙ Manage" nav link only when `currentUser.is_admin === true`
    - Show the admin modal only when `currentUser.is_admin === true`
    - _Requirements: 13.2, 13.6_

- [x] 26. Checkpoint — admin product management complete
  - Ensure all admin product management tests pass. Ask the user if questions arise.

---

## Requirement 14 — Customizable Font and Color Palette

- [x] 27. Database migration: `site_theme` table and `ThemeConfig` model
  - [x] 27.1 Write `migrations/003_add_site_theme.sql`
    - Create `site_theme` singleton table with `id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1)`, `accent_color`, `background_color`, `font_family`, `updated_at` columns and default values
    - _Requirements: 14.1, 14.2_

  - [x] 27.2 Add `ThemeConfig` dataclass to `app/models/` (e.g., `app/models/theme.py`)
    - Fields: `accent_color: str`, `background_color: str`, `font_family: str`, `updated_at: datetime`
    - _Requirements: 14.1_

  - [x] 27.3 Implement `app/repositories/theme_repository.py`
    - Write `get_theme() -> ThemeConfig` — reads the singleton row; inserts defaults if absent
    - Write `update_theme(accent_color, background_color, font_family) -> ThemeConfig`
    - Write `reset_theme() -> ThemeConfig` — restores defaults (`#D4AF37`, `#0A0E1A`, `Inter`)
    - _Requirements: 14.2, 14.4_

- [x] 28. `ThemeService` and theme REST endpoints
  - [x] 28.1 Implement `app/services/theme_service.py`
    - Write `get_theme() -> ThemeConfig`
    - Write `update_theme(accent_color, background_color, font_family) -> ThemeConfig` — validates each hex color against `^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$`; raises `ValidationError` on mismatch
    - Write `reset_theme() -> ThemeConfig`
    - _Requirements: 14.2, 14.4, 14.7_

  - [x] 28.2 Add theme routes to `app/routes/admin_routes.py`
    - `GET /api/v1/admin/theme` — retrieve active `ThemeConfig`; requires admin session
    - `PUT /api/v1/admin/theme` — update `ThemeConfig` (partial update supported); return 400 on invalid hex
    - `POST /api/v1/admin/theme/reset` — reset to defaults; requires admin session
    - `GET /api/v1/theme` — public read-only endpoint; no auth required
    - _Requirements: 14.2, 14.4, 14.7, 9.1, 9.2_



- [x] 29. `theme.js` frontend module
  - [x] 29.1 Create `app/static/js/theme.js`
    - Implement `loadAndApplyTheme()` — `GET /api/v1/theme`, call `applyTheme(config)`
    - Implement `applyTheme(config)` — set `--accent-color`, `--bg-color`, `--font-family` as CSS custom properties on `:root` synchronously
    - Call `loadAndApplyTheme()` on `DOMContentLoaded` in every HTML page
    - _Requirements: 14.3, 14.6_



- [x] 30. Theme settings section in Admin_Panel
  - [x] 30.1 Add theme settings UI to `index.html` admin modal and wire to `admin.js`
    - Add a "Theme" tab to the Admin_Panel tab bar
    - Render color pickers / text inputs for `accent_color`, `background_color`, `font_family` with live preview
    - Implement `saveTheme(config)` in `admin.js` — `PUT /api/v1/admin/theme`, call `theme.applyTheme()` on success
    - Implement `resetTheme()` in `admin.js` — `POST /api/v1/admin/theme/reset`, call `theme.applyTheme()` on success
    - _Requirements: 14.5, 14.6_

- [x] 31. Checkpoint — theme customization complete
  - Ensure theme endpoints respond correctly and `theme.js` applies CSS custom properties. Ask the user if questions arise.

---

## Requirement 15 — Product Tab Active State Bug Fix

- [x] 32. Fix tab switching logic in `admin.js`
  - [x] 32.1 Ensure `switchTab(tabName)` in `admin.js` correctly removes the active class from all tab buttons and hides all panels before activating the selected tab
    - Remove `active` CSS class from every tab button element
    - Hide every tab panel element (`display: none` or equivalent)
    - Add `active` CSS class to the clicked tab button
    - Show the clicked tab's panel
    - _Requirements: 15.1, 15.2_

  - [x] 32.2 Ensure `openAdminPanel()` always activates Product_Tab as the default on open
    - Call `switchTab('products')` inside `openAdminPanel()` before any other tab logic
    - Call `adminLoadProducts()` immediately after activating the Product_Tab
    - _Requirements: 15.3_

  - [x] 32.3 Ensure `adminLoadProducts()` shows an inline error with a retry button on fetch failure
    - On network or HTTP error, render an error message inside `#admin-products-list`
    - Render a "Retry" button that calls `adminLoadProducts()` again
    - _Requirements: 15.5_



---

## Requirement 16 — Admin Site Content Management

- [x] 33. Database migration: `site_content` table and `ContentConfig` model
  - [x] 33.1 Write `migrations/004_add_site_content.sql`
    - Create `site_content` singleton table with all content fields and their default values as specified in the design (site_title, brand_name, hero_headline, hero_subheadline, nav labels, footer fields, section headings, CTA labels, empty-state messages, updated_at)
    - _Requirements: 16.1, 16.3_

  - [x] 33.2 Add `ContentConfig` dataclass to `app/models/` (e.g., `app/models/content.py`)
    - Fields match the `site_content` table columns
    - _Requirements: 16.1_

  - [x] 33.3 Implement `app/repositories/content_repository.py`
    - Write `get_content() -> ContentConfig` — reads the singleton row; inserts defaults if absent
    - Write `update_content(fields: dict) -> ContentConfig`
    - Write `reset_content() -> ContentConfig` — restores all default values
    - _Requirements: 16.3, 16.5_

- [x] 34. `ContentService` and content REST endpoints
  - [x] 34.1 Implement `app/services/content_service.py`
    - Write `get_content() -> ContentConfig`
    - Write `update_content(fields: dict) -> ContentConfig` — validates that no required field is submitted as an empty string; raises `ValidationError` listing all empty required fields
    - Write `reset_content() -> ContentConfig`
    - _Requirements: 16.3, 16.5, 16.6_

  - [x] 34.2 Add content routes to `app/routes/admin_routes.py`
    - `GET /api/v1/admin/content` — retrieve active `ContentConfig`; requires admin session
    - `PUT /api/v1/admin/content` — update `ContentConfig`; return 400 listing all empty required fields
    - `POST /api/v1/admin/content/reset` — reset to defaults; requires admin session
    - `GET /api/v1/content` — public read-only endpoint; no auth required
    - _Requirements: 16.3, 16.5, 16.6, 9.1, 9.2_



- [x] 35. `content.js` frontend module
  - [x] 35.1 Create `app/static/js/content.js`
    - Implement `loadAndApplyContent()` — `GET /api/v1/content`, call `applyContent(config)`
    - Implement `applyContent(config)` — iterate over all `[data-content-key]` elements and set `textContent` to `config[key]`; update `document.title` if `site_title` changes
    - Call `loadAndApplyContent()` on `DOMContentLoaded` in every HTML page
    - _Requirements: 16.2, 16.4_



- [x] 36. Annotate HTML pages with `data-content-key` attributes
  - [x] 36.1 Annotate `app/static/index.html` with `data-content-key` attributes
    - Add `data-content-key` to: brand name spans, hero headline, hero subheadline, nav link labels, footer tagline, footer copyright, section heading, section subheading, "Shop Now" CTA, empty-state messages
    - _Requirements: 16.1, 16.2, 16.8_

  - [x] 36.2 Annotate `app/static/login.html`, `app/static/cart.html`, `app/static/orders.html`, `app/static/order-confirmation.html` with `data-content-key` attributes
    - Add `data-content-key` to all applicable static text nodes (brand name, CTA labels, empty-state messages, nav labels)
    - _Requirements: 16.1, 16.2, 16.8_

- [x] 37. Content management section in Admin_Panel
  - [x] 37.1 Add content management UI to `index.html` admin modal and wire to `admin.js`
    - Add a "Content" tab to the Admin_Panel tab bar
    - Render a form with labeled text inputs for every `ContentConfig` field
    - Show inline validation errors (listing all empty required fields) without closing the form on 400
    - Implement `saveContent(fields)` in `admin.js` — `PUT /api/v1/admin/content`, call `content.applyContent()` on success for immediate DOM update
    - Implement `resetContent()` in `admin.js` — `POST /api/v1/admin/content/reset`, call `content.applyContent()` on success
    - _Requirements: 16.4, 16.6, 16.7_

- [x] 38. Final checkpoint — Requirements 13–16 complete
  - Ensure all new backend tests pass (`pytest`), all new frontend tests pass (`vitest --run`), admin endpoints return correct status codes, theme and content are applied on page load, and tab switching works correctly. Ask the user if questions arise.

---

## Notes

- Each task references specific requirements for traceability
- Tasks 21–38 cover Requirements 13–16 only; tasks 1–20 cover Requirements 1–12
