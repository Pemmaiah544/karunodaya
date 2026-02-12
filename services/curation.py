"""
Book Curation Service

Provides rule-based book recommendations for children
based on their reading level, grade, and subscription plan.
"""

from django.db.models import Q, Count
from apps.catalog.models import Book
from apps.profiles.models import Child
from apps.inventory.models import PhysicalCopy
from apps.orders.models import SubscriptionCycle
from datetime import date, timedelta

# Grade ordering for range checking
GRADE_ORDER = {
    'PRE_K': 0,
    'KINDERGARTEN': 1,
    'GRADE_1': 2,
    'GRADE_2': 3,
    'GRADE_3': 4,
    'GRADE_4': 5,
    'GRADE_5': 6,
    'GRADE_6': 7,
    'GRADE_7': 8,
    'GRADE_8': 9,
}


def get_curated_books(child_id, limit=20, exclude_currently_issued=True):
    """
    Get curated book recommendations for a child.
    """
    try:
        child = Child.objects.get(id=child_id)
    except Child.DoesNotExist:
        return Book.objects.none()

    # Base queryset: subscription-eligible and active books
    books = Book.objects.filter(
        is_subscription_eligible=True,
        is_active=True
    )

    # 1. Start with high-quality matching
    # Filter by difficulty rating matching child's reading level (if set)
    if child.reading_difficulty_level:
        difficulty_books = books.filter(difficulty_rating=child.reading_difficulty_level)
        if difficulty_books.exists():
            books = difficulty_books

    # 2. Filter by grade range (if set)
    child_grade_value = GRADE_ORDER.get(child.grade)
    if child_grade_value is not None:
        matching_books = []
        # Optimization: filter only from current candidates
        for book in books:
            book_min_value = GRADE_ORDER.get(book.recommended_grade_min, 0)
            book_max_value = GRADE_ORDER.get(book.recommended_grade_max, 9)

            if book_min_value <= child_grade_value <= book_max_value:
                matching_books.append(book.id)
        
        # Only apply if it doesn't empty our candidates completely
        if matching_books:
            books = books.filter(id__in=matching_books)

    # 3. Exclude books currently issued to this child
    if exclude_currently_issued:
        currently_issued_book_ids = list(SubscriptionCycle.objects.filter(
            child=child,
            status__in=['ACTIVE', 'OVERDUE']
        ).values_list('physical_copies__book_id', flat=True))
        
        if currently_issued_book_ids:
            books = books.exclude(id__in=currently_issued_book_ids)

    # 4. Handle availability & Ordering
    # Annotate with available copy count
    books = books.annotate(
        available_copies_count=Count(
            'physical_copies',
            filter=Q(physical_copies__status='AVAILABLE')
        )
    )

    # Note: We don't strictly filter available_copies_count > 0 here 
    # so we can always return something for display.
    # But we prioritize available books in the ordering.
    
    # Order by: availability first, then newest/title
    books = books.order_by('-available_copies_count', '-created_at', 'title')

    return books[:limit]


def assign_subscription_books(subscription_cycle, auto_select=True):
    """
    Assign physical book copies to a subscription cycle.

    Logic:
    1. Get curated books for the child
    2. Select required number of books based on plan
    3. Assign specific physical copies (with barcode)
    4. Update copy status to ISSUED
    5. Create inventory log entries

    Args:
        subscription_cycle: SubscriptionCycle instance
        auto_select: Automatically select books (default: True)
                    If False, admin must manually select books

    Returns:
        tuple: (success: bool, message: str, assigned_copies: list)
    """
    if not subscription_cycle.plan:
        return (False, "No subscription plan associated with this cycle", [])

    required_books = subscription_cycle.plan.books_per_month

    # Check if books already assigned
    if subscription_cycle.physical_copies.count() >= required_books:
        return (
            False,
            f"Already has {subscription_cycle.physical_copies.count()} books assigned",
            []
        )

    if not auto_select:
        return (
            True,
            "Please manually select books from the admin interface",
            []
        )

    # Get curated books for this child
    curated_books = get_curated_books(subscription_cycle.child.id)

    if not curated_books.exists():
        return (False, "No suitable books found for this child's profile", [])

    # Select required number of books
    selected_books = curated_books[:required_books]
    assigned_copies = []

    for book in selected_books:
        # Get first available physical copy
        available_copy = PhysicalCopy.objects.filter(
            book=book,
            status='AVAILABLE'
        ).first()

        if available_copy:
            # Assign the copy
            subscription_cycle.physical_copies.add(available_copy)

            # Update copy status
            available_copy.status = 'ISSUED'
            available_copy.save()

            # Create inventory log
            from apps.inventory.models import InventoryLog
            InventoryLog.objects.create(
                physical_copy=available_copy,
                action='ISSUED',
                performed_by=None,  # System-assigned
                notes=f"Auto-assigned to {subscription_cycle.child.name} (Cycle {subscription_cycle.id})"
            )

            assigned_copies.append(available_copy)

    if not assigned_copies:
        return (False, "Could not find available physical copies", [])

    success_count = len(assigned_copies)
    message = f"Successfully assigned {success_count} of {required_books} books"

    if success_count < required_books:
        message += f" (Could not find enough available copies)"

    return (True, message, assigned_copies)


def return_subscription_books(subscription_cycle, condition_notes='', returned_by=None):
    """
    Process return of all books in a subscription cycle.

    Args:
        subscription_cycle: SubscriptionCycle instance
        condition_notes: Optional notes about book condition on return
        returned_by: User who processed the return (for audit log)

    Returns:
        tuple: (success: bool, message: str)
    """
    if subscription_cycle.status not in ['ACTIVE', 'OVERDUE']:
        return (False, f"Cycle is {subscription_cycle.get_status_display()}, cannot be returned")

    returned_count = 0

    for copy in subscription_cycle.physical_copies.all():
        if copy.status == 'ISSUED':
            copy.status = 'AVAILABLE'
            copy.save()

            # Create inventory log
            from apps.inventory.models import InventoryLog
            notes = f"Returned from {subscription_cycle.child.name} (Cycle {subscription_cycle.id})"
            if condition_notes:
                notes += f" - Condition: {condition_notes}"

            InventoryLog.objects.create(
                physical_copy=copy,
                action='RETURNED',
                performed_by=returned_by,
                notes=notes
            )
            returned_count += 1

    # Update subscription cycle
    subscription_cycle.status = 'RETURNED'
    subscription_cycle.actual_return_date = date.today()
    subscription_cycle.save()

    return (True, f"Successfully returned {returned_count} books")


def calculate_late_fee(subscription_cycle):
    """
    Calculate late fee for an overdue subscription cycle.

    Business Rule:
    - 30-day return window
    - 7-day grace period (days 31-37)
    - ₹50/day after grace period
    - Max ₹500 late fee

    Args:
        subscription_cycle: SubscriptionCycle instance

    Returns:
        Decimal: Late fee amount
    """
    if subscription_cycle.status != 'ACTIVE':
        return subscription_cycle.late_fee

    today = date.today()
    expected_return = subscription_cycle.expected_return_date

    if today <= expected_return:
        return 0  # Not overdue

    grace_period_end = expected_return + timedelta(days=7)

    if today <= grace_period_end:
        return 0  # Within grace period

    # Calculate days overdue (after grace period)
    days_overdue = (today - grace_period_end).days

    # ₹50 per day, max ₹500
    late_fee = min(days_overdue * 50, 500)

    return late_fee


def check_and_update_overdue_cycles():
    """
    Management command helper to check and update overdue subscription cycles.

    Should be run daily via cron job.

    Returns:
        dict: Statistics about updated cycles
    """
    from decimal import Decimal

    active_cycles = SubscriptionCycle.objects.filter(status='ACTIVE')
    today = date.today()

    stats = {
        'total_active': active_cycles.count(),
        'now_overdue': 0,
        'late_fees_updated': 0
    }

    for cycle in active_cycles:
        # Check if overdue
        if today > cycle.expected_return_date:
            grace_period_end = cycle.expected_return_date + timedelta(days=7)

            # Mark as overdue if past grace period
            if today > grace_period_end and cycle.status == 'ACTIVE':
                cycle.status = 'OVERDUE'
                stats['now_overdue'] += 1

            # Calculate and update late fee
            late_fee = calculate_late_fee(cycle)
            if late_fee != cycle.late_fee:
                cycle.late_fee = Decimal(str(late_fee))
                stats['late_fees_updated'] += 1

            cycle.save()

    return stats
