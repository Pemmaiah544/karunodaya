# Karunodaya Digital Platform - Codebase Summary

**Last Updated:** 2026-01-13

## Project Overview
A mobile-first Django application for a book subscription and marketplace service.

## Technical Stack
- **Framework:** Django 5.0.9 ✅ Installed
- **Database:** SQLite (production-ready via libsql/Turso)
- **Frontend:** HTMX 2.0.4 + Tailwind CSS (CDN)
- **Admin:** django-unfold 0.38.0 ✅ Configured
- **Python:** 3.10.12
- **Payment:** Razorpay (configured, integration pending)

## Current Status
- **Phase:** Phase 3 Complete - Curation Service ✅
- **Progress:** 3 of 9 phases complete (33%)
- **Virtual Environment:** Active at `.venv/` with all dependencies
- **Database:** SQLite with 10 models migrated
- **Test Data:** Seeded with 9 books, 45 physical copies, 3 plans

## Completed Phases
✅ **Phase 1:** Django Foundation (project structure, settings, templates)
✅ **Phase 2:** Core Models (10 models with full admin integration)
✅ **Phase 3:** Curation Service (smart book matching & business logic)

## Next Phases
🔜 **Phase 4:** Admin Dashboard (stats cards, custom actions)
⏳ **Phase 5:** Mobile Portal (HTMX views, onboarding)
⏳ **Phase 6:** Payment Integration (Razorpay webhook)
⏳ **Phase 7:** Workflows (subscription, purchase, returns)
⏳ **Phase 8:** Testing & Polish
⏳ **Phase 9:** Deployment Prep

## Architecture Decisions
✅ **Admin UI:** django-unfold (modern, mobile-responsive)
✅ **Payment Gateway:** Razorpay (India-focused, subscription-friendly)
✅ **Subscription Model:** Fixed monthly box (3-5 books per plan)
✅ **Platform Scope:** Web-only MVP (mobile-web optimized, no native app)
✅ **API:** Not included in MVP (future enhancement)

## Domain Models Structure

### 1. User & Profiles (`apps/profiles/`)
- `User` (Django built-in with custom registration)
- `ParentProfile` (OneToOne with User)
  - Fields: phone_number, address, city, state, pincode
- `Child` (ForeignKey to ParentProfile)
  - Fields: name, age, grade, reading_difficulty_level, date_of_birth
  - Max 5 children per parent

### 2. Catalog (`apps/catalog/`)
- `Publisher`
  - Fields: name, email, phone, address
- `Book`
  - Fields: title, author, isbn, mrp, description, cover_image
  - Fields: difficulty_rating (BEGINNER/INTERMEDIATE/ADVANCED)
  - Fields: recommended_grade_min, recommended_grade_max
  - Flags: is_subscription_eligible, is_purchase_eligible
  - Inventory: stock_count (for purchases)

### 3. Inventory Management (`apps/inventory/`)
- `PhysicalCopy` (subscription books with unique barcodes)
  - Fields: book, barcode (unique), status, condition_notes
  - Status choices: AVAILABLE, ISSUED, DAMAGED, LOST
- `InventoryLog` (audit trail for all inventory actions)
  - Fields: physical_copy, action, performed_by, notes, timestamp

### 4. Orders & Subscriptions (`apps/orders/`)
- `SubscriptionPlan`
  - Fields: name, books_per_month, price_per_month, age_group
  - Examples: Little Readers (3 books/₹499), Young Explorers (4/₹699)
- `Order`
  - Fields: parent, order_type (SUBSCRIPTION/PURCHASE), status, total_amount
  - Status flow: PENDING → PAID → DISPATCHED → DELIVERED
- `SubscriptionCycle`
  - Fields: parent, child, plan, physical_copies (M2M)
  - Fields: issue_date, expected_return_date, actual_return_date
  - Fields: status (ACTIVE/RETURNED/OVERDUE/LOST), late_fee
  - Business Rule: 30-day return window + 7-day grace period

### 5. Payments (`apps/payments/`)
- `Transaction`
  - Fields: order, razorpay_order_id, razorpay_payment_id, razorpay_signature
  - Fields: amount, status (INITIATED/PENDING/SUCCESS/FAILED)
  - Fields: provider_response (JSONField for debugging)

## Key Features & Services

### A. Curation Engine (`services/curation.py`) ✅ IMPLEMENTED
Core Functions:
- `get_curated_books(child_id, limit=20)`: Rule-based book recommendations
  - Matches difficulty_rating with child's reading level
  - Matches grade ranges with child's current grade
  - Excludes currently issued books
  - Returns books with available physical copies
- `assign_subscription_books(subscription_cycle)`: Auto-assign books
  - Selects from curated list based on plan
  - Assigns specific physical copies with barcodes
  - Updates inventory status to ISSUED
  - Creates audit log entries
- `return_subscription_books(subscription_cycle)`: Process returns
  - Updates copy status to AVAILABLE
  - Creates return log entries
- `calculate_late_fee(subscription_cycle)`: Fee calculation
  - 30-day return + 7-day grace period
  - ₹50/day after grace (max ₹500)
- `check_and_update_overdue_cycles()`: Daily maintenance
  - Marks overdue cycles
  - Updates late fees

### B. HTMX Patterns (Pending - Phase 5)
- **Onboarding:** Multi-step form with HTMX swaps
- **Live Search:** Marketplace search with debounced keyup
- **Cart Updates:** Partial refreshes for order summary

### C. Admin Customization ✅ PARTIALLY COMPLETE
- Django Unfold configured with custom purple theme
- All 10 models registered with ModelAdmin
- Custom Action: "Mark as Returned" for SubscriptionCycle
- Inlines: ChildInline, InventoryLogInline
- List filters, search fields on all models
- Read-only audit fields (timestamps, logs)
- Stats Dashboard: Pending Phase 4

## Workflows

### Subscription Workflow
Order Created → Inventory Checked → PhysicalCopy Assigned → Dispatched → Returned

### Marketplace Workflow
Order Created → Publisher Notified → Shipped by Publisher → Delivered

## Security
- LoginRequiredMixin for all portal views
- Parent can only see their own children and orders
- Payment webhook verification before status updates

## Directory Structure
```
karunodaya/
├── manage.py
├── requirements.txt
├── .env.example
├── CODEBASE_SUMMARY.md (this file)
├── BUSINESS_RULES.md
├── IMPLEMENTATION_PLAN.md
├── TASK_BREAKDOWN.md
│
├── karunodaya_project/     # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                   # Django applications
│   ├── profiles/           # ParentProfile & Child
│   ├── catalog/            # Publisher & Book
│   ├── inventory/          # PhysicalCopy & InventoryLog
│   ├── orders/             # SubscriptionPlan, Order, SubscriptionCycle
│   ├── payments/           # Transaction & Razorpay integration
│   └── portal/             # User-facing views (HTMX-powered)
│
├── services/               # Business logic layer
│   ├── curation.py         # get_curated_books(), assign_subscription_books()
│   └── payment.py          # Razorpay helpers
│
├── templates/
│   ├── admin/
│   │   └── index.html      # Custom stats dashboard
│   ├── portal/
│   │   ├── base.html       # Mobile-first base with bottom nav
│   │   ├── onboarding.html # HTMX multi-step form
│   │   ├── dashboard.html
│   │   ├── marketplace.html
│   │   └── components/     # Reusable HTMX partials
│   └── registration/
│       ├── login.html
│       └── register.html
│
├── static/
│   ├── css/
│   │   └── tailwind.css    # Compiled Tailwind
│   ├── js/
│   │   └── htmx.min.js
│   └── images/
│
└── media/
    ├── book_covers/
    └── user_uploads/
```

## Management Commands
- `python manage.py seed_data` - Creates test data (3 publishers, 9 books, 45 copies)
- `python manage.py check_overdue_subscriptions` - Daily cron for late fees

## Database Statistics (Current)
- **Total Models:** 10 (across 5 apps)
- **Migrations:** All applied successfully
- **Indexes:** Performance indexes on key fields
- **Test Data:**
  - Publishers: 3
  - Books: 9 (3 BEGINNER, 3 INTERMEDIATE, 3 ADVANCED)
  - Physical Copies: 45 (5 per book)
  - Subscription Plans: 3 (₹499, ₹699, ₹899)

## File Structure (Current)
```
karunodaya/
├── apps/
│   ├── profiles/       ✅ Models + Admin
│   ├── catalog/        ✅ Models + Admin + seed_data command
│   ├── inventory/      ✅ Models + Admin
│   ├── orders/         ✅ Models + Admin + check_overdue command
│   ├── payments/       ✅ Models + Admin
│   └── portal/         ⏳ Pending Phase 5
├── services/
│   └── curation.py     ✅ Complete with all business logic
├── templates/
│   ├── base.html       ✅ Created
│   ├── portal/         ✅ Base template ready
│   └── registration/   ✅ Login template ready
├── static/
│   ├── css/           ✅ Tailwind configured (CDN)
│   └── js/            ✅ HTMX 2.0.4 downloaded
├── karunodaya_project/
│   ├── settings.py    ✅ Fully configured
│   └── urls.py        ✅ Basic routing ready
└── manage.py          ✅ Working

## Notes
- Mobile-first design: fixed headers, bottom nav on mobile
- Use Django Admin where possible, avoid custom dashboards
- HTMX for all dynamic updates (no React/Vue)
- All business rules documented in BUSINESS_RULES.md
- Progress tracked in PROGRESS.md
- Using uv pip for all package installations
