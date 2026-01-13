# Karunodaya Platform - Implementation Plan

## Project Setup Decisions
✅ **Admin UI:** django-unfold
✅ **Payment Gateway:** Razorpay
✅ **Subscription Model:** Fixed monthly box (3-5 books per plan)
✅ **Platform:** Web-only MVP (mobile-web optimized)
✅ **Starting Fresh:** In karunodaya/ directory

---

## Phase 1: Foundation (Days 1-2)

### 1.1 Django Project Setup
```bash
pip install django==5.0 django-unfold
django-admin startproject karunodaya_project .
python manage.py startapp profiles
python manage.py startapp catalog
python manage.py startapp inventory
python manage.py startapp orders
python manage.py startapp payments
python manage.py startapp portal
mkdir services
```

### 1.2 Frontend Stack
```bash
pip install django-htmx
npm install -D tailwindcss
npx tailwindcss init
```

### 1.3 Base Configuration
- Configure `settings.py` with all apps
- Setup django-unfold in INSTALLED_APPS
- Configure HTMX middleware
- Setup static files and media handling
- Create base templates structure

### 1.4 User Authentication
- Extend Django User model
- Create custom user registration
- Setup login/logout views
- Create mobile-first auth templates

**Deliverable:** Working Django project with auth system

---

## Phase 2: Core Models (Days 3-4)

### 2.1 Profiles App
**Models:**
```python
ParentProfile
  - user (OneToOne)
  - phone_number
  - address
  - city, state, pincode
  - created_at

Child
  - parent (ForeignKey to ParentProfile)
  - name
  - age
  - grade (choices: PRE_K to GRADE_8)
  - reading_difficulty_level (choices: BEGINNER, INTERMEDIATE, ADVANCED)
  - date_of_birth
```

### 2.2 Catalog App
**Models:**
```python
Publisher
  - name
  - email
  - phone
  - address

Book
  - title
  - author
  - publisher (ForeignKey)
  - isbn
  - mrp
  - description
  - cover_image
  - difficulty_rating (choices)
  - recommended_grade_min, recommended_grade_max
  - is_subscription_eligible (Boolean)
  - is_purchase_eligible (Boolean)
  - stock_count (for purchases)
  - created_at
```

### 2.3 Inventory App
**Models:**
```python
PhysicalCopy
  - book (ForeignKey)
  - barcode (unique)
  - status (choices: AVAILABLE, ISSUED, DAMAGED, LOST)
  - condition_notes
  - purchased_date

InventoryLog
  - physical_copy (ForeignKey)
  - action (choices: ADDED, ISSUED, RETURNED, DAMAGED, LOST)
  - performed_by (ForeignKey to User)
  - notes
  - timestamp
```

### 2.4 Orders App
**Models:**
```python
SubscriptionPlan
  - name
  - books_per_month
  - price_per_month
  - age_group_min, age_group_max
  - description

Order
  - parent (ForeignKey)
  - order_type (choices: SUBSCRIPTION, PURCHASE)
  - status (choices: PENDING, PAID, DISPATCHED, DELIVERED, CANCELLED)
  - total_amount
  - created_at
  - updated_at

SubscriptionCycle
  - parent (ForeignKey)
  - child (ForeignKey)
  - plan (ForeignKey to SubscriptionPlan)
  - physical_copies (ManyToMany to PhysicalCopy)
  - issue_date
  - expected_return_date
  - actual_return_date
  - status (choices: ACTIVE, RETURNED, OVERDUE, LOST)
  - late_fee
```

### 2.5 Payments App
**Models:**
```python
Transaction
  - order (ForeignKey)
  - razorpay_order_id
  - razorpay_payment_id
  - razorpay_signature
  - amount
  - status (choices: INITIATED, PENDING, SUCCESS, FAILED)
  - provider_response (JSONField)
  - created_at
```

**Deliverable:** All models created, migrated, registered in admin

---

## Phase 3: Curation Service (Day 5)

### 3.1 Create services/curation.py
```python
def get_curated_books(child_id, limit=10):
    """
    Returns curated book recommendations for a child
    - Matches difficulty_rating with child.reading_difficulty_level
    - Matches grade range with child.grade
    - Only subscription_eligible books
    - Excludes books currently with the child
    - Returns available books with physical copies
    """
    pass

def assign_subscription_books(subscription_cycle):
    """
    Assigns physical copies to a subscription cycle
    - Uses curation logic
    - Marks copies as ISSUED
    - Creates InventoryLog entries
    """
    pass
```

**Deliverable:** Working curation logic with tests

---

## Phase 4: Admin Dashboard (Days 6-7)

### 4.1 Django-Unfold Configuration
- Custom admin theme settings
- Color scheme and branding
- Mobile-responsive tweaks

### 4.2 Custom Admin Index
Create `templates/admin/index.html` with stats cards:
- Active Subscriptions count
- Total Revenue (this month)
- Books Currently Out
- Low Inventory Alerts

### 4.3 Custom Admin Actions
- **For SubscriptionCycle:** "Mark as Returned"
  - Updates physical_copies status to AVAILABLE
  - Sets actual_return_date
  - Creates InventoryLog entries

- **For Order:** "Mark as Dispatched"
- **For PhysicalCopy:** "Mark as Damaged/Lost"

### 4.4 Admin List Filters
- Books: by difficulty, publisher, stock status
- Orders: by status, type, date range
- Subscription Cycles: by status, overdue

**Deliverable:** Fully functional admin with custom dashboard

---

## Phase 5: Mobile-First Portal (Days 8-10)

### 5.1 Base Templates
```
templates/portal/
├── base.html (fixed header + bottom nav)
├── components/
│   ├── header.html
│   ├── bottom_nav.html
│   └── book_card.html
```

### 5.2 HTMX-Powered Onboarding
**URL:** `/onboarding/`

**Flow:**
```
Step 1: Parent Info (hx-post to /onboarding/step2/)
  ↓
Step 2: Child Info (hx-post to /onboarding/step3/)
  ↓
Step 3: Plan Selection (hx-post to /onboarding/complete/)
  ↓
Redirect to Dashboard
```

### 5.3 Dashboard Views
- `/dashboard/` - Overview with active subscriptions, curated box preview
- `/curated-box/<child_id>/` - Full curated book list for child
- `/marketplace/` - All purchasable books with live search
- `/orders/` - Order history
- `/profile/` - Edit parent and child profiles

### 5.4 HTMX Features
- **Live Search:**
  ```html
  <input hx-get="/marketplace/search/"
         hx-trigger="keyup changed delay:500ms"
         hx-target="#book-results">
  ```

- **Cart Updates:**
  ```html
  <button hx-post="/cart/add/{{ book.id }}/"
          hx-target="#cart-summary"
          hx-swap="outerHTML">
  ```

- **Filter Updates:**
  ```html
  <select hx-get="/marketplace/"
          hx-trigger="change"
          hx-target="#book-grid">
  ```

**Deliverable:** Full user portal with HTMX interactions

---

## Phase 6: Payment Integration (Days 11-12)

### 6.1 Razorpay Setup
```bash
pip install razorpay
```

### 6.2 Payment Flow
**Subscription:**
1. User selects plan → Create Order (status=PENDING)
2. Generate Razorpay order_id
3. Show Razorpay checkout modal
4. On success → Redirect to webhook handler
5. Webhook verifies signature → Update order (status=PAID)
6. Create SubscriptionCycle, assign books

**Purchase:**
1. Add to cart → Checkout
2. Create Order with cart items
3. Same Razorpay flow as above

### 6.3 Webhook Handler
```python
@csrf_exempt
def razorpay_webhook(request):
    # Verify signature
    # Update Transaction and Order status
    # Trigger fulfillment workflow
    pass
```

### 6.4 Security
- Store Razorpay keys in environment variables
- Signature verification on all webhooks
- HTTPS enforcement (production)

**Deliverable:** Working payment flow with Razorpay

---

## Phase 7: Workflows & Business Logic (Days 13-14)

### 7.1 Subscription Workflow
```python
# On payment success:
1. Create SubscriptionCycle
2. Call assign_subscription_books()
3. Mark physical copies as ISSUED
4. Update Order status to DISPATCHED
5. (Future: Send email notification)
```

### 7.2 Return Workflow
```python
# Via admin action:
1. Mark SubscriptionCycle as RETURNED
2. Update physical_copies status to AVAILABLE
3. Calculate late fees if applicable
4. Create InventoryLog entries
```

### 7.3 Purchase Workflow
```python
# On payment success:
1. Decrement Book.stock_count
2. Update Order status to PAID
3. (Admin manually marks DISPATCHED)
```

### 7.4 Overdue Detection
```python
# Cron job / management command:
python manage.py check_overdue_subscriptions
- Find cycles past expected_return_date + grace period
- Calculate late fees
- Update status to OVERDUE
```

**Deliverable:** All workflows implemented and tested

---

## Phase 8: Testing & Polish (Days 15-16)

### 8.1 Create Seed Data
```bash
python manage.py seed_data
```
- Sample publishers
- 50+ sample books across difficulty levels
- Physical copies for each book
- Test parent accounts
- Sample subscription plans

### 8.2 Manual Testing Checklist
- [ ] Parent registration and login
- [ ] Child profile creation
- [ ] Subscription plan selection and payment
- [ ] Curated book recommendations accuracy
- [ ] Marketplace search and filters
- [ ] Purchase flow
- [ ] Admin dashboard stats
- [ ] Mark as Returned action
- [ ] Inventory tracking
- [ ] Payment webhook handling

### 8.3 Mobile Responsiveness
- Test on various screen sizes
- Bottom nav on mobile
- Touch-friendly buttons
- Fast page loads

### 8.4 Security Audit
- [ ] CSRF protection on forms
- [ ] User data isolation (get_queryset)
- [ ] Payment webhook signature verification
- [ ] SQL injection prevention (use ORM)
- [ ] XSS prevention (template escaping)

**Deliverable:** Production-ready MVP

---

## Phase 9: Deployment Prep (Days 17-18)

### 9.1 Environment Configuration
- Create `.env.example`
- Move secrets to environment variables
- Setup different settings for dev/prod

### 9.2 Static Files
```bash
python manage.py collectstatic
```

### 9.3 Database Migration to Turso
```bash
pip install libsql-experimental
```
- Configure Turso connection
- Test migrations
- Backup strategy

### 9.4 Documentation
- Update README.md with setup instructions
- API documentation (if needed)
- Admin user guide
- Deployment guide

**Deliverable:** Deployment-ready application

---

## File Structure (Final)

```
karunodaya/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── CODEBASE_SUMMARY.md
├── BUSINESS_RULES.md
├── IMPLEMENTATION_PLAN.md
│
├── karunodaya_project/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── profiles/
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── views.py
│   │   └── forms.py
│   ├── catalog/
│   ├── inventory/
│   ├── orders/
│   ├── payments/
│   └── portal/
│
├── services/
│   ├── __init__.py
│   ├── curation.py
│   └── payment.py
│
├── templates/
│   ├── admin/
│   │   └── index.html
│   ├── portal/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── onboarding.html
│   │   ├── marketplace.html
│   │   └── components/
│   └── registration/
│       ├── login.html
│       └── register.html
│
├── static/
│   ├── css/
│   │   └── tailwind.css
│   ├── js/
│   │   └── htmx.min.js
│   └── images/
│
└── media/
    ├── book_covers/
    └── user_uploads/
```

---

## Dependencies (requirements.txt)

```txt
Django==5.0
django-unfold
django-htmx
razorpay
Pillow
python-decouple
libsql-experimental
```

---

## Development Timeline

**Total Estimated Time:** 18 days

- Phase 1: 2 days
- Phase 2: 2 days
- Phase 3: 1 day
- Phase 4: 2 days
- Phase 5: 3 days
- Phase 6: 2 days
- Phase 7: 2 days
- Phase 8: 2 days
- Phase 9: 2 days

---

## Success Metrics (MVP)

- [ ] Parent can register and add child profiles
- [ ] Subscription plans are selectable and payable
- [ ] Books are curated based on child's profile
- [ ] Marketplace search and purchase works
- [ ] Admin can manage inventory and mark returns
- [ ] Payment integration is secure and functional
- [ ] Mobile experience is smooth and app-like
- [ ] All business rules are enforced

---

## Next Steps After MVP

1. Email notifications
2. Publisher self-service portal
3. REST API for mobile app
4. Book reviews and ratings
5. Recommendation engine improvements
6. Analytics dashboard
7. Referral program
8. Multi-language support
