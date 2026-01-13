# Karunodaya Platform - Business Rules & Assumptions

## 1. Book Difficulty Levels
**Decision:** Use a simple 3-tier system mapped to child's reading level

```
- BEGINNER: Ages 3-6, Grades Pre-K to 1
- INTERMEDIATE: Ages 7-10, Grades 2-5
- ADVANCED: Ages 11-14, Grades 6-8
```

Each `Book` has a `difficulty_rating` field (choices: BEGINNER, INTERMEDIATE, ADVANCED)
Each `Child` has a `reading_difficulty_level` field (same choices)
Curation matches these levels + grade range

## 2. Subscription Plans
**Fixed Monthly Box Model:**

```
Plan Name         | Books/Month | Age Group      | Price/Month
------------------|-------------|----------------|-------------
Little Readers    | 3 books     | 3-6 years      | ₹499
Young Explorers   | 4 books     | 7-10 years     | ₹699
Teen Scholars     | 5 books     | 11-14 years    | ₹899
```

- Parent subscribes per child
- Auto-renewal monthly via Razorpay
- Books curated automatically based on child's profile
- Ships within 2-3 days of subscription/renewal

## 3. Subscription Return Window
**30-Day Flexible Return:**

- Books issued on 1st of month (or subscription start date)
- Expected return: Before next cycle (28-30 days)
- Grace period: +7 days (no penalty)
- After grace period: ₹50/day late fee (max ₹500)
- If not returned by day 45: Marked as "Lost" and charged full replacement cost

## 4. Damaged/Lost Book Policy

### Damage Assessment:
- **Minor Damage** (torn pages, cover wear): No charge, logged for inventory
- **Major Damage** (missing pages, water damage): 50% of book MRP
- **Lost/Unreturned**: 100% of book MRP + shipping (₹100)

### Implementation:
- Security deposit NOT required for MVP
- Charges added to parent's account
- Must clear dues before next cycle ships
- 3 major damages/lost books → Subscription review/suspension

## 5. Marketplace (Purchase) Workflow

### Publisher Integration:
- **For MVP:** We manage all inventory (both subscription & purchase)
- Publishers upload books via admin
- When purchase order received:
  1. Stock automatically decremented
  2. Email notification to admin (manual fulfillment for now)
  3. Publisher/admin marks as "Shipped" with tracking
  4. No auto-notification to publisher (future enhancement)

### Purchase Rules:
- All books available for purchase (even subscription-eligible ones)
- One-time payment via Razorpay
- Shipping: ₹40 flat (free above ₹500)
- No returns on purchased books (policy decision)

## 6. Inventory Management

### Physical Copy Tracking:
Each book has multiple physical copies with unique barcodes:

```
Book: "The Hungry Caterpillar"
├── Copy #1 (Barcode: HCC-001) → Status: Available
├── Copy #2 (Barcode: HCC-002) → Status: Issued (SubscriptionCycle #42)
├── Copy #3 (Barcode: HCC-003) → Status: Damaged
└── Copy #4 (Barcode: HCC-004) → Status: Available
```

### Stock Alerts:
- **Low Stock Warning:** Available copies < 5
- **Critical Stock Alert:** Available copies < 2
- Admin dashboard shows these alerts prominently

### Subscription vs Purchase Inventory:
- Subscription uses PhysicalCopy tracking (for returns)
- Purchase decrements stock_count only (no specific copy tracking)

## 7. Payment & Transaction Rules

### Razorpay Integration:
- **Subscriptions:** Recurring payment setup
  - First payment: Immediate on plan selection
  - Subsequent: Auto-charged on renewal date

- **Purchases:** One-time payment
  - Cart checkout → Razorpay payment page
  - Webhook confirms payment → Order marked "Paid"

### Webhook Security:
- Verify Razorpay signature before updating order status
- Log all webhook calls for debugging
- Handle failures gracefully (retry mechanism)

### Transaction States:
```
INITIATED → PENDING → SUCCESS/FAILED
```

## 8. User Access Control

### Parent Portal Rules:
- Parent can only view/edit their own profile
- Parent can only view/manage their own children
- Parent can only view their own orders and subscription cycles
- No cross-parent data visibility

### Admin Access:
- Full access to all data
- Custom actions for common tasks (Mark as Returned, etc.)
- Read-only views for sensitive payment data

## 9. Email Notifications (Future Phase)

For MVP, we'll skip email notifications and use admin flags:
- [ ] Welcome email
- [ ] Subscription confirmation
- [ ] Dispatch notification
- [ ] Return reminder
- [ ] Late fee warning
- [ ] Payment receipt

Admin will manually track these via status flags.

## 10. Child Profile Limits

- Minimum: 1 child required for subscription
- Maximum: 5 children per parent account
- Each child can have independent subscription plan
- Shared parent account/login

## MVP Scope Exclusions (Future Enhancements)

- Mobile native app (Web-only for now)
- REST API
- Email notifications (admin manual process)
- Auto-publisher notifications
- Book reviews/ratings
- Wishlist feature
- Referral program
- Multi-language support
- Book previews/sample pages
