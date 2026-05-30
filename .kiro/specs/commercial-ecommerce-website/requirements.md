# Requirements Document

## Introduction

A professional commercial e-commerce website built with a Flask backend, PostgreSQL database, and a modern frontend using HTML, CSS, Tailwind CSS, and JavaScript. The platform allows customers to browse products with an engaging sliding image gallery, manage a shopping cart, place orders, and authenticate via a professionally designed login page. The system emphasizes visual appeal through animations, hover effects, and a polished UI to maximize customer engagement and conversion.

The platform also includes a hidden admin capability for product management, a customizable theme system for fonts and color palettes, a corrected product tab interaction in the admin panel, and a site content management system that allows the Admin to edit all written text on the website exclusively from the Admin_Panel without modifying source code or redeploying the application.

---

## Glossary

- **System**: The e-commerce web application as a whole.
- **Frontend**: The HTML/CSS/Tailwind CSS/JavaScript layer rendered in the user's browser.
- **Backend**: The Flask application server handling API requests and business logic.
- **Database**: The PostgreSQL instance storing user credentials, product data, and orders.
- **User**: An unauthenticated visitor browsing the website.
- **Customer**: An authenticated user who has logged in.
- **Admin**: A privileged user account with exclusive access to product management features. The existence of the Admin account is not disclosed on any public-facing page.
- **Admin_Panel**: A modal or dedicated page accessible only to the Admin, containing product management tools including the Product_Tab.
- **Product_Tab**: The tab within the Admin_Panel that displays the product list and the add/edit product form.
- **Product_Gallery**: The image slideshow component displayed on a product card or product detail page.
- **Cart**: The in-session and persisted collection of products a Customer intends to purchase.
- **Order**: A confirmed purchase record associated with a Customer.
- **Auth_Service**: The backend component responsible for authentication and session management.
- **Product_Service**: The backend component responsible for product data retrieval and management.
- **Admin_Service**: The backend component responsible for admin authentication and privileged product management operations.
- **Order_Service**: The backend component responsible for cart and order management.
- **Theme_Service**: The backend or frontend component responsible for storing and applying customizable font and color palette settings.
- **Login_Page**: The dedicated authentication page featuring a background photo and login form.
- **Product_Card**: A UI component displaying a product's image gallery, name, price, and action buttons.
- **Action_Button**: One of the four interactive buttons on a Product_Card: Buy, Add to Cart, Product Info, and Shipping Location.
- **Shipping_Location**: A modal or panel displaying available shipping regions and estimated delivery times for a product.
- **Theme_Config**: A persisted configuration object containing the site's active font family and color palette values.
- **Content_Config**: A persisted configuration object containing all editable text content for the website, including labels, headings, messages, and other static copy.
- **Content_Service**: The backend component responsible for storing, retrieving, and applying site content values from the Content_Config.

---

## Requirements

### Requirement 1: User Authentication

**User Story:** As a User, I want to register and log in to the website, so that I can access personalized shopping features and track my orders.

#### Acceptance Criteria

1. THE Auth_Service SHALL store user credentials (email and hashed password) in the Database using bcrypt hashing with a minimum cost factor of 12.
2. WHEN a User submits a registration form with a valid email and a password of at least 8 characters, THE Auth_Service SHALL create a new account and redirect the User to the Login_Page.
3. IF a User submits a registration form with an email that already exists in the Database, THEN THE Auth_Service SHALL return a 409 Conflict response with a descriptive error message.
4. WHEN a User submits valid login credentials, THE Auth_Service SHALL create a server-side session and redirect the Customer to the product listing page.
5. IF a User submits invalid login credentials, THEN THE Auth_Service SHALL return a 401 Unauthorized response and display an error message on the Login_Page without revealing which field is incorrect.
6. WHEN a Customer clicks the logout action, THE Auth_Service SHALL invalidate the server-side session and redirect the User to the Login_Page.
7. WHILE a Customer's session is active, THE System SHALL maintain authentication state across page navigations without requiring re-login.

---

### Requirement 2: Professional Login Page Design

**User Story:** As a User, I want a visually appealing login page, so that I feel confident in the professionalism of the platform before entering my credentials.

#### Acceptance Criteria

1. THE Frontend SHALL render the Login_Page with a full-viewport background image that covers the entire screen without distortion.
2. THE Frontend SHALL display the login form in a centered card with a semi-transparent overlay to ensure text legibility against the background image.
3. WHEN a User hovers over the login submit button, THE Frontend SHALL apply a smooth CSS transition of 300ms or less to the button's background color and scale.
4. THE Login_Page SHALL display the platform's logo or brand name prominently above the login form.
5. THE Frontend SHALL render the Login_Page responsively, maintaining usability on viewport widths from 320px to 1920px.

---

### Requirement 3: Product Listing Page

**User Story:** As a User, I want to browse a catalog of products, so that I can discover items I wish to purchase.

#### Acceptance Criteria

1. WHEN a User navigates to the product listing page, THE Product_Service SHALL retrieve all active products from the Database and return them to the Frontend.
2. THE Frontend SHALL render each product as a Product_Card within a responsive grid layout that displays a minimum of 1 column on mobile (320px) and a maximum of 4 columns on desktop (1280px and above).
3. WHEN a User hovers over a Product_Card, THE Frontend SHALL apply a CSS elevation animation (box-shadow increase and slight upward translate) with a transition duration of 200ms or less.
4. THE Frontend SHALL display the product name, price formatted to two decimal places, and currency symbol on each Product_Card.
5. WHEN a User hovers over an Action_Button on a Product_Card, THE Frontend SHALL apply a smooth scale and color transition of 200ms or less to that button.

---

### Requirement 4: Product Image Sliding Gallery

**User Story:** As a User, I want to see multiple images of a product in an auto-advancing slideshow, so that I can evaluate the product from different angles without manual interaction.

#### Acceptance Criteria

1. THE Product_Gallery SHALL display one product image at a time within a fixed-aspect-ratio container.
2. WHEN the Product_Gallery is rendered and contains more than one image, THE Product_Gallery SHALL automatically advance to the next image every 15 seconds.
3. WHEN the Product_Gallery advances to the next image, THE Frontend SHALL apply a horizontal sliding CSS transition of 500ms or less between the outgoing and incoming images.
4. WHEN the Product_Gallery reaches the last image in the sequence, THE Product_Gallery SHALL advance to the first image on the next 15-second interval (circular navigation).
5. THE Frontend SHALL render navigation dots or arrows on the Product_Gallery, allowing a User to manually advance to any image at any time.
6. WHEN a User manually selects an image via navigation controls, THE Product_Gallery SHALL reset the 15-second auto-advance timer.
7. IF a product has only one image, THEN THE Product_Gallery SHALL display that image statically without auto-advance or navigation controls.

---

### Requirement 5: Product Action Buttons

**User Story:** As a User, I want clear action buttons on each product, so that I can quickly buy, add to cart, view details, or check shipping options.

#### Acceptance Criteria

1. THE Frontend SHALL render four Action_Buttons on each Product_Card: "Buy", "Add to Cart", "Product Info", and "Shipping Location".
2. WHEN a Customer clicks the "Buy" button, THE Order_Service SHALL create a new Order containing that single product with a quantity of 1 and redirect the Customer to the checkout page.
3. WHEN a Customer clicks the "Add to Cart" button, THE Order_Service SHALL add the product to the Customer's Cart and display a confirmation notification within 500ms.
4. WHEN a User clicks the "Add to Cart" button without being authenticated, THE Frontend SHALL redirect the User to the Login_Page and preserve the intended cart action for completion after login.
5. WHEN a User clicks the "Product Info" button, THE Frontend SHALL display a modal or expanded panel containing the full product description, specifications, and all available images.
6. WHEN a User clicks the "Shipping Location" button, THE Frontend SHALL display the Shipping_Location panel containing available shipping regions and estimated delivery time ranges.
7. IF a Customer clicks the "Buy" button without being authenticated, THEN THE Frontend SHALL redirect the Customer to the Login_Page and preserve the intended purchase action for completion after login.

---

### Requirement 6: Shopping Cart Management

**User Story:** As a Customer, I want to manage items in my cart, so that I can review and adjust my selections before placing an order.

#### Acceptance Criteria

1. WHILE a Customer is authenticated, THE Order_Service SHALL persist the Customer's Cart contents in the Database so that Cart items are retained across sessions.
2. WHEN a Customer navigates to the Cart page, THE Frontend SHALL display each Cart item with its product image, name, unit price, quantity selector, line total, and a remove button.
3. WHEN a Customer changes the quantity of a Cart item to a positive integer, THE Order_Service SHALL update the Cart item quantity in the Database within 1 second and recalculate the Cart total.
4. WHEN a Customer clicks the remove button on a Cart item, THE Order_Service SHALL delete that item from the Cart in the Database and update the displayed Cart total.
5. THE Frontend SHALL display the Cart's running total price, formatted to two decimal places with currency symbol, and update it immediately upon any quantity or item change.
6. IF the Cart is empty, THEN THE Frontend SHALL display an empty-cart message and a call-to-action link directing the Customer to the product listing page.

---

### Requirement 7: Order Placement and History

**User Story:** As a Customer, I want to place orders and view my order history, so that I can track my purchases.

#### Acceptance Criteria

1. WHEN a Customer confirms a checkout, THE Order_Service SHALL create an Order record in the Database containing the Customer's ID, ordered items, quantities, unit prices, total amount, and a UTC timestamp.
2. WHEN an Order is successfully created, THE System SHALL display an order confirmation page with the Order ID and a summary of purchased items.
3. WHEN a Customer navigates to the order history page, THE Order_Service SHALL retrieve all Orders associated with that Customer from the Database and return them sorted by creation timestamp in descending order.
4. THE Frontend SHALL display each Order in the order history with the Order ID, creation date, item count, and total amount.
5. IF the Order_Service encounters a Database error during Order creation, THEN THE Order_Service SHALL return a 500 Internal Server Error response, log the error with a unique trace ID, and display a user-friendly error message without exposing internal details.

---

### Requirement 8: Animations and Hover Interactions

**User Story:** As a User, I want smooth animations and hover effects throughout the site, so that the browsing experience feels modern and engaging.

#### Acceptance Criteria

1. WHEN a User hovers over any interactive element (buttons, links, Product_Cards), THE Frontend SHALL apply a CSS transition with a duration between 150ms and 300ms.
2. THE Frontend SHALL animate page-level content sections into view using a fade-in or slide-up CSS animation when they enter the viewport for the first time during a session.
3. WHEN a User hovers over a navigation link, THE Frontend SHALL apply an underline slide-in animation originating from the left edge of the link text.
4. THE Frontend SHALL respect the `prefers-reduced-motion` media query by disabling or reducing all non-essential animations for Users who have enabled reduced-motion accessibility settings in their operating system.
5. WHEN a confirmation notification is displayed (e.g., after "Add to Cart"), THE Frontend SHALL animate the notification into view with a slide-down effect and automatically dismiss it after 3 seconds with a fade-out animation.

---

### Requirement 9: Backend API Design

**User Story:** As a developer, I want a well-structured Flask REST API, so that the frontend and backend are cleanly decoupled and maintainable.

#### Acceptance Criteria

1. THE Backend SHALL expose all data endpoints as JSON REST API routes under the `/api/v1/` path prefix.
2. THE Backend SHALL return HTTP status codes consistent with REST conventions: 200 for success, 201 for resource creation, 400 for validation errors, 401 for authentication failures, 404 for missing resources, and 500 for server errors.
3. WHEN the Backend receives a request with a malformed JSON body, THE Backend SHALL return a 400 Bad Request response with a descriptive error message.
4. THE Backend SHALL validate all incoming request data against defined schemas before processing, and return a 400 response listing all validation errors if validation fails.
5. THE Backend SHALL serve the Frontend's static assets (HTML, CSS, JS) from a dedicated `/static/` directory.

---

### Requirement 10: Database Schema and Integrity

**User Story:** As a developer, I want a well-structured PostgreSQL schema, so that data is stored reliably and relationships are enforced.

#### Acceptance Criteria

1. THE Database SHALL contain a `users` table with columns: `id` (UUID primary key), `email` (unique, not null), `password_hash` (not null), and `created_at` (UTC timestamp, not null).
2. THE Database SHALL contain a `products` table with columns: `id` (UUID primary key), `name` (not null), `description`, `price` (numeric, not null), `is_active` (boolean, default true), and `created_at` (UTC timestamp, not null).
3. THE Database SHALL contain a `product_images` table with columns: `id` (UUID primary key), `product_id` (foreign key referencing `products.id`), `image_url` (not null), and `display_order` (integer, not null).
4. THE Database SHALL contain a `cart_items` table with columns: `id` (UUID primary key), `user_id` (foreign key referencing `users.id`), `product_id` (foreign key referencing `products.id`), `quantity` (integer, not null, minimum 1), and `updated_at` (UTC timestamp, not null).
5. THE Database SHALL contain an `orders` table with columns: `id` (UUID primary key), `user_id` (foreign key referencing `users.id`), `total_amount` (numeric, not null), `status` (varchar, not null), and `created_at` (UTC timestamp, not null).
6. THE Database SHALL contain an `order_items` table with columns: `id` (UUID primary key), `order_id` (foreign key referencing `orders.id`), `product_id` (foreign key referencing `products.id`), `quantity` (integer, not null), and `unit_price` (numeric, not null).
7. IF a referenced `user_id` or `product_id` is deleted, THEN THE Database SHALL enforce referential integrity by restricting the deletion or cascading as appropriate per foreign key constraints.

---

### Requirement 11: Security

**User Story:** As a Customer, I want my personal data and credentials to be protected, so that I can shop with confidence.

#### Acceptance Criteria

1. THE Auth_Service SHALL use HTTPS for all communication between the Frontend and Backend in production deployments.
2. THE Backend SHALL set session cookies with the `HttpOnly`, `Secure`, and `SameSite=Strict` attributes.
3. THE Backend SHALL implement CSRF protection on all state-changing endpoints (POST, PUT, DELETE).
4. THE Backend SHALL sanitize and parameterize all Database queries to prevent SQL injection.
5. WHEN a User submits a form, THE Frontend SHALL validate input client-side before submission, and THE Backend SHALL independently validate the same input server-side.

---

### Requirement 12: Responsive Design

**User Story:** As a User, I want the website to work well on any device, so that I can shop from my phone, tablet, or desktop.

#### Acceptance Criteria

1. THE Frontend SHALL use Tailwind CSS responsive utility classes to adapt layouts across breakpoints: mobile (< 640px), tablet (640px–1023px), and desktop (≥ 1024px).
2. THE Frontend SHALL render the navigation bar as a collapsible hamburger menu on viewport widths below 640px.
3. THE Frontend SHALL ensure all text maintains a minimum contrast ratio of 4.5:1 against its background, in compliance with WCAG 2.1 AA standards.
4. THE Frontend SHALL ensure all interactive elements have a minimum touch target size of 44×44 CSS pixels on mobile viewports.

---

### Requirement 13: Admin-Only Product Management

**User Story:** As the store owner, I want a hidden admin account that can add and manage products, so that product management is restricted to authorized personnel and the admin's existence is not visible to regular users or visitors.

#### Acceptance Criteria

1. THE System SHALL designate exactly one Admin account, identified by a role flag stored in the Database, whose credentials are configured via environment variables and are never exposed in source code or public-facing pages.
2. THE Frontend SHALL NOT render any hint of an admin account, admin login option, or admin-specific navigation element on any page visible to unauthenticated Users or authenticated Customers.
3. WHEN a request is made to any admin endpoint under `/api/v1/admin/` without a valid Admin session, THE Backend SHALL return a 403 Forbidden response.
4. WHEN the Admin authenticates via the standard login endpoint with valid Admin credentials, THE Auth_Service SHALL create a session that grants access to admin-only endpoints.
5. WHILE the Admin is authenticated, THE Frontend SHALL display the Admin_Panel, which contains a Product_Tab for managing products.
6. THE Admin_Panel SHALL be accessible only when the current session belongs to the Admin user, and SHALL NOT be rendered or linked in any publicly visible navigation.
7. WHEN the Admin opens the Admin_Panel and selects the Product_Tab, THE Frontend SHALL set the Product_Tab to the active state and display the product list.
8. THE Product_Tab SHALL display a form allowing the Admin to enter a product name (required), price (required, non-negative), and description (optional).
9. WHEN the Admin submits a valid product form, THE Admin_Service SHALL create the product in the Database and display it in the product list within the Product_Tab.
10. WHEN the Admin selects a product in the product list and clicks the image management control, THE Admin_Panel SHALL allow the Admin to upload image files (JPG, PNG, GIF, WebP, max 10 MB each) or provide external image URLs for that product.
11. IF the Admin submits a product form with a missing name or an invalid price, THEN THE Admin_Panel SHALL display a descriptive inline error message without closing the form.

---

### Requirement 14: Customizable Font and Color Palette

**User Story:** As the store owner, I want to customize the site's fonts and color palette, so that the visual identity of the store can be adjusted without modifying source code.

#### Acceptance Criteria

1. THE System SHALL provide a Theme_Config that stores at minimum: a primary accent color (hex value), a background color (hex value), and a font family name.
2. WHEN the Admin updates the Theme_Config via the Admin_Panel or a dedicated settings interface, THE Theme_Service SHALL persist the updated Theme_Config to the Database or a configuration file.
3. WHEN a User loads any page, THE Frontend SHALL apply the active Theme_Config values as CSS custom properties or equivalent, so that the site's accent color, background color, and font family reflect the stored configuration.
4. THE Theme_Service SHALL provide a reset function that restores the Theme_Config to the default values (gold accent `#D4AF37`, navy background `#0A0E1A`, Inter font family).
5. WHILE the Admin is authenticated and the Admin_Panel is open, THE Frontend SHALL display a theme settings section where the Admin can preview and apply font and color changes before saving.
6. WHEN the Admin saves a Theme_Config update, THE Frontend SHALL apply the new theme to the current page immediately without requiring a full page reload.
7. IF the Admin provides an invalid hex color value (not matching the pattern `#RRGGBB` or `#RGB`), THEN THE Theme_Service SHALL reject the update and return a descriptive validation error.

---

### Requirement 15: Product Tab Active State and Display Bug Fix

**User Story:** As the Admin, I want the Product_Tab in the Admin_Panel to correctly activate and display the product list when clicked, so that I can manage products without encountering a broken UI.

#### Acceptance Criteria

1. WHEN the Admin clicks the Product_Tab within the Admin_Panel, THE Frontend SHALL add the active CSS class to the Product_Tab button and remove it from all other tab buttons in the Admin_Panel.
2. WHEN the Product_Tab is set to active, THE Frontend SHALL make the product list panel visible and hide all other tab panels within the Admin_Panel.
3. WHEN the Admin_Panel is first opened, THE Frontend SHALL automatically activate the Product_Tab and display the product list as the default view.
4. WHEN the product list panel is visible, THE Frontend SHALL fetch and render the current list of products from the Backend, or display an appropriate empty-state message if no products exist.
5. IF the product list fetch fails, THEN THE Frontend SHALL display an inline error message within the product list panel and provide a retry control.

---

### Requirement 16: Admin Site Content Management

**User Story:** As the store owner, I want to edit all written text on the website exclusively from the Admin_Panel, so that I can update site copy without modifying source code or redeploying the application.

#### Acceptance Criteria

1. THE Content_Service SHALL maintain a Content_Config that stores editable text values for: site title/brand name, hero section headline and subheadline, navigation link labels, footer text (copyright notice, tagline, and link labels), product listing page section headings and promotional banner text, call-to-action button labels (e.g., "Shop Now", "View Cart"), and empty-state messages (e.g., empty cart message, no orders message).
2. WHEN a User loads any page, THE Frontend SHALL retrieve the active Content_Config from the Content_Service and render all applicable text fields using the stored values.
3. WHEN the Admin updates a content field via the Admin_Panel, THE Content_Service SHALL persist the updated value to the Database or a configuration file within 1 second.
4. WHEN the Admin saves a content update, THE Frontend SHALL apply the new content values to the current page immediately without requiring a full page reload.
5. THE Content_Service SHALL provide a reset function that restores all Content_Config fields to their original default values.
6. IF the Admin submits a content update with a required field left empty, THEN THE Admin_Panel SHALL display a descriptive inline validation error and reject the update without saving.
7. WHILE the Admin is authenticated and the Admin_Panel is open, THE Frontend SHALL display a content management section where the Admin can view and edit all Content_Config fields.
8. THE System SHALL NOT require source code modification or application redeployment for any content change managed through the Content_Config.
