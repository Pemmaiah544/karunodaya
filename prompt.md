Master Prompt: Karunodaya Digital Platform (MVP)

Role: Senior Django Architect. Objective: Build a mobile-first Django application for a book subscription and marketplace service using SQLite/Turso.
1. Core Technical Constraints

    Framework: Django 5.x.

    Database: SQLite (Production-ready via libsql for Turso).

    Frontend: No heavy JS frameworks. Use Tailwind CSS for styling and HTMX for all dynamic updates (modals, filters, form submissions).

    Admin: Use django-unfold or django-admin-interface for a polished, mobile-responsive management UI. Do not build a custom dashboard if the Django Admin can do it.

    Mobile-First: The end-user portal must mimic a native app experience (fixed headers, bottom nav on mobile).

2. Domain Models & Schema

Build the following models with strict ForeignKey relationships:

    Profiles: ParentProfile (linked to User), Child (linked to Parent, fields: age, grade, reading_difficulty_level).

    Catalog: Publisher, Book (fields: is_subscription_eligible, is_purchase_eligible, difficulty_rating, stock_count).

    Inventory Tracking: PhysicalCopy (for subscription items with unique IDs/Barcodes), InventoryLog (tracking 'Available', 'Issued', 'Damaged', 'Lost').

    Orders & Workflow: * Order (Parent, Total, OrderType: [Subscription/Purchase], Status).

        SubscriptionCycle (Tracks which books are currently with which child and their return status).

    Payments: Transaction (Reference ID, Status, Provider Response).

3. Specific Feature Logic (The "How-To")
A. The "Rule-Based" Curation Engine

Create a service module services/curation.py.

    Function: get_curated_books(child_id)

    Logic: Filter Books where is_subscription_eligible=True, Book.grade == Child.grade, and Book.difficulty_rating matches the Child.reading_difficulty_level.

    Usage: This should populate the "Your Curated Box" view for parents.

B. HTMX Patterns for Portal Experience

    Onboarding: Use a single-page view with HTMX hx-post to swap form steps (Step 1: Parent Info -> Step 2: Child Info -> Step 3: Plan Selection).

    Live Search: Implement a search bar in the marketplace using hx-trigger="keyup changed delay:500ms" to filter the book list.

    Cart/Summary: Updates to the order summary should use HTMX triggers to refresh only the total/price partials.

C. Admin Customization (The "Back-Office")

    Dashboard: Use django-admin with custom template overrides for the index page to show four "Stats Cards": Active Subscriptions, Total Revenue, Books Out, and Low Inventory Alerts.

    Actions: Add a custom admin action "Mark as Returned" for Subscription Orders that automatically updates the PhysicalCopy status back to 'Available'.

4. Operational Workflows

    Subscription Workflow: Order Created -> Inventory Checked -> PhysicalCopy Assigned -> Dispatched -> Returned.

    Marketplace Workflow: Order Created -> Publisher Notified (via email/flag) -> Shipped by Publisher -> Delivered.

5. Security & Stability

    Payment Safety: Implement a webhook view for the payment gateway. Only update Order.status to 'Paid' upon verified signature from the provider.

    Access Control: Use LoginRequiredMixin for all portal views. Ensure a Parent can only see their own Children and Orders using get_queryset overrides.

Step-by-Step Execution Plan for the Agent:

    Phase 1: Setup Django, Tailwind, and the User/Profile models.

    Phase 2: Implement the Book Catalog and the Curation Logic service.

    Phase 3: Build the HTMX-powered Mobile Web Portal (Onboarding + Subscription flow).

    Phase 4: Configure the Django Admin with the custom Operations Dashboard and Inventory logs.

    Phase 5: Implement the Mock Payment Gateway and Order fulfillment status tracking.
