# Karunodaya Platform - Task Breakdown

## Phase 1: Django Setup & Foundation
- [ ] Install Django 5.x and core dependencies
- [ ] Create Django project structure
- [ ] Install and configure Tailwind CSS
- [ ] Install django-unfold or django-admin-interface
- [ ] Setup HTMX integration
- [ ] Configure SQLite database
- [ ] Create User authentication system
- [ ] Create ParentProfile model
- [ ] Create Child model with profile fields
- [ ] Setup initial migrations

## Phase 2: Book Catalog & Curation Logic
- [ ] Create catalog app
- [ ] Implement Publisher model
- [ ] Implement Book model with all required fields
- [ ] Create services/curation.py module
- [ ] Implement get_curated_books(child_id) function
- [ ] Create admin interfaces for Publisher and Book
- [ ] Add book catalog views
- [ ] Implement book search/filter functionality

## Phase 3: HTMX-Powered Mobile Web Portal
- [ ] Design mobile-first base template
- [ ] Implement fixed header and bottom navigation
- [ ] Create multi-step onboarding flow with HTMX
  - [ ] Step 1: Parent Info
  - [ ] Step 2: Child Info
  - [ ] Step 3: Plan Selection
- [ ] Build "Your Curated Box" view
- [ ] Implement live search for marketplace
- [ ] Create cart/order summary with HTMX updates
- [ ] Add subscription flow UI
- [ ] Add marketplace purchase flow UI

## Phase 4: Inventory & Admin Operations
- [ ] Create inventory app
- [ ] Implement PhysicalCopy model
- [ ] Implement InventoryLog model
- [ ] Create custom admin dashboard template
- [ ] Add Stats Cards to admin index
  - [ ] Active Subscriptions counter
  - [ ] Total Revenue display
  - [ ] Books Out tracker
  - [ ] Low Inventory Alerts
- [ ] Add "Mark as Returned" custom admin action
- [ ] Create inventory management views
- [ ] Implement barcode/ID tracking

## Phase 5: Orders & Payments
- [ ] Create orders app
- [ ] Implement Order model
- [ ] Implement SubscriptionCycle model
- [ ] Create payments app
- [ ] Implement Transaction model
- [ ] Setup mock payment gateway
- [ ] Implement payment webhook view
- [ ] Add webhook signature verification
- [ ] Create order status tracking
- [ ] Implement subscription workflow logic
- [ ] Implement marketplace workflow logic
- [ ] Add email notifications for publishers

## Phase 6: Security & Access Control
- [ ] Add LoginRequiredMixin to all portal views
- [ ] Implement get_queryset overrides for data isolation
- [ ] Add CSRF protection
- [ ] Setup environment variables for secrets
- [ ] Implement payment webhook security
- [ ] Add rate limiting for API endpoints

## Phase 7: Testing & Deployment
- [ ] Write unit tests for models
- [ ] Write tests for curation logic
- [ ] Write integration tests for workflows
- [ ] Test HTMX interactions
- [ ] Setup Turso/libsql for production
- [ ] Create deployment guide
- [ ] Setup static file serving
- [ ] Configure production settings

## Additional Tasks
- [ ] Create seed data for development
- [ ] Add data fixtures for testing
- [ ] Write API documentation
- [ ] Create user documentation
- [ ] Setup logging and monitoring
