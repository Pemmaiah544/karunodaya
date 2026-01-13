# Karunodaya Platform - Development Progress

## Phase 1: Foundation ✅ COMPLETED

### Completed Tasks:
- [x] Install Django 5.x and all dependencies (using uv pip)
- [x] Create Django project structure (karunodaya_project)
- [x] Create all Django apps (profiles, catalog, inventory, orders, payments, portal)
- [x] Configure django-unfold admin UI
- [x] Setup HTMX integration
- [x] Configure Tailwind CSS (CDN for now, npm setup available)
- [x] Create base template structure
  - Base template
  - Portal base template with mobile-first design
  - Login template
- [x] Configure settings.py with:
  - Environment variables support (python-decouple)
  - All apps registered
  - HTMX middleware
  - Debug toolbar (for development)
  - Static and media file handling
  - Razorpay configuration placeholders
  - Django Unfold configuration
- [x] Run initial migrations successfully
- [x] Create .env.example and .gitignore

### Files Created:
- `requirements.txt` - All project dependencies
- `.env.example` - Environment variable template
- `.gitignore` - Git ignore patterns
- `package.json` - npm/Tailwind configuration
- `tailwind.config.js` - Tailwind CSS configuration
- `static/css/input.css` - Tailwind source
- `static/js/htmx.min.js` - HTMX library
- `templates/base.html` - Base template
- `templates/portal/base.html` - Mobile-first portal base
- `templates/registration/login.html` - Login page
- `karunodaya_project/settings.py` - Configured Django settings
- `karunodaya_project/urls.py` - URL configuration

### Directory Structure:
```
karunodaya/
├── apps/
│   ├── profiles/
│   ├── catalog/
│   ├── inventory/
│   ├── orders/
│   ├── payments/
│   └── portal/
├── services/
├── templates/
├── static/
├── media/
├── karunodaya_project/
├── manage.py
└── db.sqlite3
```

---

## Phase 2: Core Models ✅ COMPLETED

### Completed Tasks:
- [x] Create ParentProfile model (profiles app)
  - Fields: user, phone_number, address, city, state, pincode
  - Validates max 5 children per parent
- [x] Create Child model (profiles app)
  - Fields: parent, name, age, grade, reading_difficulty_level, date_of_birth
  - Grade choices: Pre-K to Grade 8
  - Difficulty: BEGINNER, INTERMEDIATE, ADVANCED
- [x] Create Publisher model (catalog app)
  - Fields: name, email, phone, address
- [x] Create Book model (catalog app)
  - Fields: title, author, publisher, isbn, mrp, description, cover_image
  - Curation: difficulty_rating, recommended_grade_min/max
  - Flags: is_subscription_eligible, is_purchase_eligible
  - Inventory: stock_count
  - Properties: available_for_subscription, available_for_purchase, low_stock, critical_stock
- [x] Create PhysicalCopy model (inventory app)
  - Fields: book, barcode (unique), status, condition_notes, purchased_date
  - Status: AVAILABLE, ISSUED, DAMAGED, LOST
- [x] Create InventoryLog model (inventory app)
  - Fields: physical_copy, action, performed_by, notes, timestamp
  - Actions: ADDED, ISSUED, RETURNED, DAMAGED, LOST, REPAIRED
- [x] Create SubscriptionPlan model (orders app)
  - Fields: name, books_per_month, price_per_month, age_group_min/max
  - Plans: Little Readers, Young Explorers, Teen Scholars
- [x] Create Order model (orders app)
  - Fields: parent, order_type, status, total_amount
  - Types: SUBSCRIPTION, PURCHASE
  - Status: PENDING, PAID, DISPATCHED, DELIVERED, CANCELLED
- [x] Create SubscriptionCycle model (orders app)
  - Fields: parent, child, plan, order, physical_copies (M2M)
  - Dates: issue_date, expected_return_date, actual_return_date
  - Status: ACTIVE, RETURNED, OVERDUE, LOST
  - Fields: late_fee (₹50/day)
- [x] Create Transaction model (payments app)
  - Fields: order, razorpay_order_id, razorpay_payment_id, razorpay_signature
  - Fields: amount, status, provider_response (JSONField)
  - Status: INITIATED, PENDING, SUCCESS, FAILED
- [x] Register all models in django-unfold admin
  - Created ModelAdmin classes for all models
  - Added inlines, list_filters, search_fields
  - Added custom admin action: "Mark as Returned" for SubscriptionCycle
- [x] Create and run migrations successfully
  - All models migrated to database
  - Indexes created for performance

### Models Summary:
- **Profiles:** 2 models (ParentProfile, Child)
- **Catalog:** 2 models (Publisher, Book)
- **Inventory:** 2 models (PhysicalCopy, InventoryLog)
- **Orders:** 3 models (SubscriptionPlan, Order, SubscriptionCycle)
- **Payments:** 1 model (Transaction)
- **Total:** 10 models with full admin integration

---

## Phase 3: Curation Service ✅ COMPLETED

### Completed Tasks:
- [x] Create services/curation.py module
- [x] Implement get_curated_books(child_id, limit=20)
  - Matches book difficulty_rating with child's reading_difficulty_level
  - Matches book grade range with child's current grade
  - Only subscription-eligible and active books
  - Excludes books currently issued to the child
  - Annotates with available copy count
  - Orders by availability
- [x] Implement assign_subscription_books(subscription_cycle)
  - Auto-selects curated books based on plan
  - Assigns specific physical copies with barcodes
  - Updates copy status to ISSUED
  - Creates inventory log entries
  - Returns success/failure with message
- [x] Implement return_subscription_books(subscription_cycle)
  - Updates physical copy status to AVAILABLE
  - Creates inventory log for returns
  - Updates subscription cycle status
- [x] Implement calculate_late_fee(subscription_cycle)
  - 30-day return window
  - 7-day grace period
  - ₹50/day after grace (max ₹500)
- [x] Implement check_and_update_overdue_cycles()
  - Marks cycles as OVERDUE after grace period
  - Calculates and updates late fees
  - Returns statistics
- [x] Create management command: check_overdue_subscriptions
  - Should be run daily via cron
  - Updates all overdue cycles and fees
- [x] Create management command: seed_data
  - Creates 3 publishers
  - Creates 9 sample books (3 per difficulty level)
  - Creates 45 physical copies (5 per book)
  - Creates 3 subscription plans
  - Tested successfully ✓

### Curation Functions:
1. **get_curated_books()** - Smart book recommendations
2. **assign_subscription_books()** - Automated book assignment
3. **return_subscription_books()** - Process returns
4. **calculate_late_fee()** - Fee calculation with grace period
5. **check_and_update_overdue_cycles()** - Daily maintenance task

### Test Data Created:
- Publishers: 3 (Penguin, Scholastic, Tulika)
- Books: 9 across all difficulty levels
- Physical Copies: 45 with unique barcodes
- Subscription Plans: 3 (Little Readers, Young Explorers, Teen Scholars)

---

## Phase 4: Admin Dashboard ✅ COMPLETED

### Completed Tasks:
- [x] Configure Django Unfold theme
  - Custom purple color scheme
  - Environment badge (Development/Production)
  - Mobile-responsive layout
- [x] Create custom admin index with stats cards (templates/admin/index.html)
  - **Stats Cards:**
    * Active Subscriptions (with overdue count)
    * Total Revenue (with monthly breakdown)
    * Books Out (with available count)
    * Low Inventory Alerts (with critical count)
  - **Recent Activity:**
    * Recent Orders (last 5)
    * Low Stock Books (with severity indicators)
  - **Quick Actions:**
    * Add Book, View Children, Subscriptions, Inventory Logs
- [x] Implement dashboard_callback() in settings.py
  - Real-time stats calculation
  - Efficient queries with annotations
  - Monthly revenue tracking
  - Low inventory detection (<5 copies)
  - Critical inventory alerts (<2 copies)
- [x] Add custom admin actions:
  - **PhysicalCopy:**
    * Mark as Damaged (creates inventory log)
    * Mark as Lost (creates inventory log)
    * Mark as Available/Repaired
  - **Order:**
    * Mark as Dispatched
    * Mark as Delivered
  - **SubscriptionCycle:**
    * Mark as Returned (uses curation service)
- [x] Enhanced list filters and search across all models
- [x] Created superuser (username: admin)

### Dashboard Features:
- **4 Stats Cards** with real-time data
- **Color-coded alerts** (green, yellow, red)
- **Recent activity feeds**
- **Low stock warnings** with severity levels
- **Quick action buttons** to common tasks
- **Fully responsive** mobile design

### Admin Actions Summary:
- Inventory management (3 actions for PhysicalCopy)
- Order fulfillment (2 actions for Order)
- Returns processing (1 action for SubscriptionCycle)
- All actions create audit logs

---

## Phase 5: Mobile Portal ✅ COMPLETED

### Completed Tasks:
- [x] Create portal URLs configuration (apps/portal/urls.py)
  - 18 URL patterns including authentication, onboarding, dashboard, marketplace, orders, profile
  - App namespace: 'portal'
- [x] Create all portal views (apps/portal/views.py)
  - RegisterView - User registration
  - OnboardingView - Multi-step onboarding with HTMX
  - onboarding_step2, onboarding_step3, onboarding_complete - HTMX handlers
  - DashboardView - Main dashboard with children and subscriptions
  - CuratedBoxView - Shows curated books for specific child
  - MarketplaceView - Book marketplace with filtering
  - marketplace_search - HTMX live search handler
  - BookDetailView - Individual book details
  - OrdersView, OrderDetailView - Order management
  - ProfileView, AddChildView, EditChildView - Profile management
- [x] Create authentication templates
  - templates/portal/register.html - User registration form
  - templates/registration/login.html - Already created in Phase 1
- [x] Create onboarding templates with HTMX
  - templates/portal/onboarding.html - Step 1: Parent info
  - templates/portal/onboarding_step2.html - Step 2: Child info
  - templates/portal/onboarding_step3.html - Step 3: Plan selection
  - Progress indicator showing 3-step flow
  - HTMX swapping for seamless UX
- [x] Create dashboard template
  - templates/portal/dashboard.html - Shows children and active subscriptions
  - Responsive grid layout
  - Links to curated books
- [x] Create marketplace templates
  - templates/portal/marketplace.html - Main marketplace view
  - templates/portal/components/book_grid.html - Reusable HTMX partial
  - Live search with 500ms debounce
  - Book cards with cover images and pricing
- [x] Create additional portal templates
  - templates/portal/curated_box.html - Shows curated books for a child
  - templates/portal/book_detail.html - Detailed book view with purchase option
  - templates/portal/orders.html - Order history with tabs (subscriptions/purchases)
  - templates/portal/order_detail.html - Individual order details with book list
  - templates/portal/profile.html - User profile and children management
  - templates/portal/add_child.html - Add new child form
  - templates/portal/edit_child.html - Edit child information
- [x] Implement HTMX features
  - Live search with keyup trigger and debouncing
  - Multi-step form without page reloads
  - Dynamic content swapping
- [x] Test portal functionality
  - Django check: No issues detected
  - Server startup: Successful
  - All templates created and linked properly

### Portal Features:
- **Registration & Authentication:**
  - User registration with auto-login
  - Login/logout functionality
  - Protected views with @login_required
- **Onboarding Flow:**
  - 3-step HTMX onboarding
  - Parent info → Child info → Plan selection
  - Seamless UX without page reloads
- **Dashboard:**
  - Children overview with quick access to curated books
  - Active subscriptions display with status badges
  - Welcome message
- **Marketplace:**
  - Live search with HTMX (500ms debounce)
  - Book grid with cover images
  - Filtering by difficulty and grade
  - Book detail pages with purchase option
- **Curated Books:**
  - Personalized book recommendations per child
  - Uses curation service logic
  - Difficulty and grade matching
- **Orders:**
  - Tab navigation (subscriptions/purchases)
  - Order history with status tracking
  - Detailed order view with book lists
  - Overdue warnings and late fee display
- **Profile Management:**
  - User and parent profile information
  - Children list (max 5)
  - Add/edit child functionality
  - Logout option

### Templates Created (Total: 11):
1. templates/portal/register.html
2. templates/portal/onboarding.html
3. templates/portal/onboarding_step2.html
4. templates/portal/onboarding_step3.html
5. templates/portal/dashboard.html
6. templates/portal/marketplace.html
7. templates/portal/curated_box.html
8. templates/portal/book_detail.html
9. templates/portal/orders.html
10. templates/portal/order_detail.html
11. templates/portal/profile.html
12. templates/portal/add_child.html
13. templates/portal/edit_child.html
14. templates/portal/components/book_grid.html (HTMX partial)

### Views Summary:
- **Total Views:** 14 (8 class-based, 6 function-based)
- **Security:** All views protected with LoginRequiredMixin or @login_required
- **Data Isolation:** Views filter by request.user to ensure parents only see their own data

---

## Phase 6: Payment Integration ✅ COMPLETED

### Completed Tasks:
- [x] Setup Razorpay integration
  - Installed razorpay==1.4.2 and setuptools==80.9.0
  - Configured RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET in settings
  - Added payment URLs to main URLconf
  - Created apps/payments/urls.py with 5 URL patterns
- [x] Create payment flow views (apps/payments/views.py)
  - initiate_payment - Creates Razorpay order and Transaction record
  - payment_callback - Handles payment success/failure with signature verification
  - payment_success - Success page with transaction details
  - payment_failure - Failure page with retry option
  - verify_razorpay_signature - HMAC SHA256 signature verification
- [x] Implement webhook handler
  - razorpay_webhook - Handles Razorpay webhook events (payment.captured, payment.failed)
  - handle_payment_captured - Updates order and assigns books on successful payment
  - handle_payment_failed - Updates transaction status on payment failure
  - Webhook signature verification with HMAC SHA256
- [x] Add signature verification
  - verify_razorpay_signature function using hmac.compare_digest
  - Webhook signature verification
  - Protects against payment tampering and replay attacks
- [x] Create payment templates
  - templates/payments/payment_page.html - Razorpay checkout integration
  - templates/payments/payment_success.html - Success page with order details
  - templates/payments/payment_failure.html - Failure page with retry
- [x] Add payment_method field to Transaction model
  - Tracks payment method (card, netbanking, UPI, etc.)
  - Created and applied migration 0002_transaction_payment_method
- [x] Integrate with subscription workflow
  - Auto-assigns books on successful subscription payment
  - Uses assign_subscription_books from curation service

### Payment Features:
- **Razorpay Checkout Integration:**
  - Embedded checkout modal
  - Auto-capture payment
  - Prefilled user details (name, email, phone)
  - Custom purple theme matching portal
- **Security:**
  - HMAC SHA256 signature verification
  - CSRF protection on callbacks
  - Webhook signature verification
  - Amount validation in paise (Indian currency)
- **Transaction Tracking:**
  - Unique razorpay_order_id and razorpay_payment_id
  - Payment method capture
  - Full provider response stored for debugging
  - Transaction status: INITIATED → PENDING → SUCCESS/FAILED
- **User Experience:**
  - Mobile-responsive payment page
  - Clear success/failure messages
  - Order details on success page
  - Retry option on failure page
  - Next steps guidance (subscription book assignment, dispatch timeline)
- **Subscription Integration:**
  - Automatic book assignment on payment success
  - Order status update to PAID
  - SubscriptionCycle activation
  - Graceful error handling if book assignment fails

### Payment Flow:
1. User initiates payment from order detail page
2. System creates Razorpay order and Transaction record (status: INITIATED)
3. Razorpay checkout modal opens
4. User completes payment
5. Razorpay sends callback with payment_id, order_id, signature
6. System verifies signature using HMAC SHA256
7. On success:
   - Transaction status → SUCCESS
   - Order status → PAID
   - Books assigned to subscription (if applicable)
   - User redirected to success page
8. On failure:
   - Transaction status → FAILED
   - User redirected to failure page with retry option
9. Webhook receives async confirmation from Razorpay
10. Webhook verifies signature and updates records if needed

### Webhook Events Handled:
- **payment.captured** - Updates transaction and order, assigns books
- **payment.failed** - Updates transaction status

### URLs Created:
- `/payments/initiate/<order_id>/` - Start payment flow
- `/payments/callback/` - Handle Razorpay callback
- `/payments/success/<transaction_id>/` - Success page
- `/payments/failure/<transaction_id>/` - Failure page
- `/payments/webhook/` - Razorpay webhook endpoint (CSRF exempt)

---

## Phase 7: Workflows ✅ COMPLETED

### Completed Tasks:
- [x] Create OrderItem model for purchase orders
  - Fields: order, book, quantity, price_per_unit
  - Tracks individual items in purchase orders
  - Includes subtotal property
  - Added to Order admin as inline
- [x] Create and run migration for OrderItem
  - Migration: apps/orders/migrations/0002_orderitem.py
  - Applied successfully
- [x] Update curation service for condition notes
  - return_subscription_books() now accepts condition_notes parameter
  - Condition notes logged in inventory log
  - Admin action updated accordingly
- [x] Implement subscription workflow views
  - Updated onboarding_complete() to create Order and SubscriptionCycle
  - Redirects to payment after subscription creation
  - Created SubscribeView for existing users to add subscriptions
  - Plan selection with radio buttons
- [x] Implement return workflow views
  - MyBooksView shows all borrowed books with status
  - Shows active/overdue cycles with late fees
  - initiate_return() processes book returns
  - Integrates with curation service
  - Shows recently returned cycles
- [x] Implement purchase workflow (shopping cart)
  - Session-based cart implementation
  - add_to_cart() adds books to cart
  - remove_from_cart() removes items
  - update_cart_quantity() updates quantities
  - CartView shows cart with totals
  - checkout() creates purchase Order and OrderItems
- [x] Create templates for all workflows
  - templates/portal/subscribe.html - Plan selection page
  - templates/portal/my_books.html - Borrowed books & returns
  - templates/portal/cart.html - Shopping cart
  - Updated templates/portal/onboarding_step3.html with child_id
  - Updated templates/portal/book_detail.html with Add to Cart
- [x] Update portal URLs with new views
  - /subscribe/ - Subscribe view
  - /subscribe/<child_id>/ - Subscribe for specific child
  - /my-books/ - Borrowed books view
  - /return/<cycle_id>/ - Initiate return
  - /cart/ - Shopping cart
  - /cart/add/<book_id>/ - Add to cart
  - /cart/remove/<book_id>/ - Remove from cart
  - /cart/update/<book_id>/ - Update quantity
  - /checkout/ - Process checkout
- [x] Test all workflows
  - Django check: No issues detected
  - All models, views, and templates validated

### Models Created:
- **OrderItem** (apps/orders/models.py)
  - Links Order to Books with quantities and prices
  - Subtotal calculation
  - Registered in admin with inline display

### Views Summary:
**Subscription Management:**
- SubscribeView - Plan selection (class-based)
- onboarding_complete - Create subscription order (function)

**Return Workflow:**
- MyBooksView - View borrowed books (class-based)
- initiate_return - Process return request (function)

**Purchase Workflow (Cart):**
- add_to_cart - Add book to cart (function)
- remove_from_cart - Remove from cart (function)
- update_cart_quantity - Update quantity (function)
- CartView - Display cart (class-based)
- checkout - Create purchase order (function)

**Total New Views:** 8 (3 class-based, 5 function-based)

### Templates Created:
1. templates/portal/subscribe.html - Subscription plan selection
2. templates/portal/my_books.html - Borrowed books & return interface
3. templates/portal/cart.html - Shopping cart with totals

### Templates Updated:
1. templates/portal/onboarding_step3.html - Added child_id, radio button plan selection
2. templates/portal/book_detail.html - Added Add to Cart button

### Features Implemented:

**1. Subscription Workflow:**
- Users can subscribe to plans during onboarding
- Existing users can add new subscriptions for their children
- Plan selection with visual feedback (radio buttons)
- Creates Order and SubscriptionCycle
- Redirects to payment gateway
- Books auto-assigned after payment (Phase 6 integration)

**2. Return Workflow:**
- View all currently borrowed books
- See overdue status and late fees
- Add condition notes when returning
- Process returns through portal (not just admin)
- View recently returned books history
- Color-coded status badges (Active/Overdue/Returned)

**3. Purchase Workflow:**
- Session-based shopping cart
- Add/remove items dynamically
- Update quantities with stock validation
- View cart totals and item counts
- Checkout creates Order with OrderItems
- Stock validation before adding to cart
- Redirects to payment gateway
- "View Cart" link on book detail pages

**4. Overdue Detection:**
- Management command already exists from Phase 3
- Runs: `python manage.py check_overdue_subscriptions`
- Should be run daily via cron
- Updates cycle status to OVERDUE
- Calculates and updates late fees

### Workflow Integration:
All three workflows integrate seamlessly with:
- **Payment Integration** (Phase 6) - Orders redirect to Razorpay
- **Curation Service** (Phase 3) - Returns use return_subscription_books()
- **Admin Dashboard** (Phase 4) - OrderItem inline, updated admin actions
- **Mobile Portal** (Phase 5) - All templates mobile-responsive

### Business Logic:
- **Subscription**: Plan → Order → Payment → Books Assigned → Dispatch
- **Return**: My Books → Return Request → Inventory Update → Late Fee (if applicable)
- **Purchase**: Browse → Add to Cart → Checkout → Payment → Dispatch

---

## Phase 8: Testing & Polish

### Tasks:
- [ ] Create seed data
- [ ] Manual testing checklist
- [ ] Mobile responsiveness testing
- [ ] Security audit

---

## Phase 9: Deployment Prep

### Tasks:
- [ ] Environment configuration
- [ ] Static files collection
- [ ] Turso database migration
- [ ] Documentation

---

## Notes:
- Using Tailwind CSS CDN for development (can compile later with npm)
- HTMX 2.0.4 integrated
- Django Unfold admin configured with custom purple theme
- All apps use 'apps.' prefix for proper module resolution
