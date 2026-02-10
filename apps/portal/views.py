from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.views import PasswordResetView
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
import re

from apps.profiles.models import ParentProfile, Child
from apps.catalog.models import Book
from apps.orders.models import Order, SubscriptionCycle, SubscriptionPlan
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .forms import ComplaintForm, RegisterForm
from .models import Complaint
from .reading_passages import get_passage_for_grade
from services.curation import get_curated_books
from functools import wraps

def onboarding_required(view_func):
    """Decorator to ensure user has completed onboarding."""
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            parent_profile = request.user.parent_profile
            if not parent_profile.onboarding_completed:
                return redirect('portal:onboarding')
        except ParentProfile.DoesNotExist:
            return redirect('portal:onboarding')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


class OnboardingRequiredMixin:
    """Mixin to ensure user has completed onboarding."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        try:
            parent_profile = request.user.parent_profile
            if not parent_profile.onboarding_completed:
                return redirect('portal:onboarding')
        except ParentProfile.DoesNotExist:
            return redirect('portal:onboarding')
            
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordResetView(PasswordResetView):
    """
    Custom PasswordResetView that generates password reset links 
    using the request's actual domain and protocol (HTTP/HTTPS).
    This ensures password reset links work correctly with dev tunnels.
    """
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.txt'
    html_email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url_name = 'portal:password_reset_done'
    
    def get_email_context(self, **kwargs):
        """
        Override to add protocol and domain from request.
        """
        context = super().get_email_context(**kwargs)
        
        # Use request's domain and protocol
        request = kwargs.get('request')
        if request:
            # Get protocol (http or https)
            protocol = 'https' if request.is_secure() else 'http'
            # Get domain from request (works with dev tunnels)
            domain = request.get_host()
            
            context['protocol'] = protocol
            context['domain'] = domain
        
        return context


class HomeView(TemplateView):
    """Home view that redirects to login page."""
    
    def get(self, request, *args, **kwargs):
        # Always redirect to login page
        return redirect('portal:login')


class RegisterView(TemplateView):
    """User registration view."""
    template_name = 'portal/register.html'

    def get(self, request, *args, **kwargs):
        form = RegisterForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            mobile_number = form.cleaned_data.get('mobile_number')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            # Create user
            user = User.objects.create_user(
                username=mobile_number, 
                email=email, 
                password=password
            )
            login(request, user)
            return redirect('portal:onboarding')
        
        return render(request, self.template_name, {'form': form})


def check_mobile_exists(request):
    """Check if mobile number is already registered."""
    mobile = request.GET.get('mobile', '')
    exists = User.objects.filter(username=mobile).exists()
    return JsonResponse({'exists': exists})


class OnboardingView(LoginRequiredMixin, TemplateView):
    """Multi-step onboarding with HTMX."""
    template_name = 'portal/onboarding.html'

    def get(self, request, *args, **kwargs):
        # Check if onboarding is complete
        try:
            parent_profile = request.user.parent_profile
            if parent_profile.onboarding_completed:
                # Onboarding is complete, redirect to dashboard
                return redirect('portal:dashboard')
        except ParentProfile.DoesNotExist:
            # No profile yet, show onboarding
            pass
        
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscription_plans'] = SubscriptionPlan.objects.filter(is_active=True)
        return context


@login_required
def onboarding_step2(request):
    """HTMX handler for step 2 - parent info."""
    if request.method == 'POST':
        # Update user names (capitalize first letter of each word)
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        if len(first_name) > 15:
            return HttpResponse('First name cannot exceed 15 characters', status=400)
        if last_name and len(last_name) > 15:
            return HttpResponse('Last name cannot exceed 15 characters', status=400)

        user = request.user
        user.first_name = first_name.title() if first_name else ''
        user.last_name = last_name.title() if last_name else ''
        user.save()

        # Create or update parent profile (capitalize city and state)
        phone_number = request.POST.get('phone_number', '')
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '')

        if address and not re.search(r'[a-zA-Z]', address):
            return HttpResponse('Address must contain at least one letter', status=400)

        parent_profile, created = ParentProfile.objects.update_or_create(
            user=user,
            defaults={
                'phone_number': phone_number,
                'address': address.title() if address else '',
                'city': city.title() if city else '',
                'state': state.title() if state else '',
                'pincode': pincode,
            }
        )

        # Return step 2 template (child info)
        return render(request, 'portal/onboarding_step2.html', {
            'parent_profile': parent_profile
        })

    return HttpResponse('Method not allowed', status=405)


@login_required
def onboarding_step3(request):
    """HTMX handler for step 3 - child info."""
    if request.method == 'POST':
        parent_profile = request.user.parent_profile

        # Get child data (all optional)
        name = request.POST.get('name', '').strip()
        age = request.POST.get('age', None)
        grade = request.POST.get('grade', '')
        reading_level = request.POST.get('reading_level', '')
        dob = request.POST.get('date_of_birth', None)

        # Only create child if at least name is provided (capitalize name)
        if name:
            if len(name) > 15:
                # For HTMX request, we might want to return an error, but let's keep it simple for now
                # and just truncate or redirect with error. Since it's a POST, let's redirect with message.
                messages.error(request, 'Child name cannot exceed 15 characters')
                return redirect('portal:onboarding')

            child = Child.objects.create(
                parent=parent_profile,
                name=name.title(),
                age=int(age) if age else None,
                grade=grade if grade else None,
                reading_difficulty_level=reading_level if reading_level else None,
                date_of_birth=dob if dob else None
            )

        # Mark onboarding as completed
        parent_profile.onboarding_completed = True
        parent_profile.save()

        # Redirect to fluency check if child was created, else dashboard
        if 'child' in locals():
            return redirect('portal:fluency_check', child_id=child.id)
        
        # Redirect to dashboard - onboarding complete
        return redirect('portal:dashboard')

    return HttpResponse('Method not allowed', status=405)


@login_required
def onboarding_complete(request):
    """HTMX handler for onboarding completion - handle subscription, purchase, or both."""
    if request.method == 'POST':
        plan_type = request.POST.get('plan_type')
        plan_id = request.POST.get('plan_id')
        child_id = request.POST.get('child_id')

        if not plan_type or not child_id:
            return HttpResponse('Missing required fields', status=400)

        try:
            parent_profile = request.user.parent_profile
            child = get_object_or_404(Child, id=child_id, parent=parent_profile)

            if plan_type in ['subscription', 'both']:
                # Subscription requires a plan selection
                if not plan_id:
                    return HttpResponse('Please select a subscription plan', status=400)
                
                plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)

                # Create subscription order
                order = Order.objects.create(
                    parent=parent_profile,
                    order_type='SUBSCRIPTION',
                    status='PENDING',
                    total_amount=plan.price_per_month
                )

                # Create subscription cycle (books will be assigned after payment)
                from datetime import date, timedelta
                issue_date = date.today()
                expected_return = issue_date + timedelta(days=30)

                SubscriptionCycle.objects.create(
                    parent=parent_profile,
                    child=child,
                    plan=plan,
                    order=order,
                    issue_date=issue_date,
                    expected_return_date=expected_return,
                    status='ACTIVE'
                )

                # Store order info for later payment and redirect to dashboard
                request.session['pending_payment_order_id'] = order.id
            
            elif plan_type == 'purchase':
                # For purchase-only, no order created yet
                pass
            
            else:
                return HttpResponse('Invalid plan type', status=400)

            # Store plan preference in user profile for later
            parent_profile.plan_preference = plan_type
            parent_profile.save()

            # Redirect to dashboard after setup completion
            return redirect('portal:dashboard')

        except ParentProfile.DoesNotExist:
            return HttpResponse('Parent profile not found', status=404)

    return HttpResponse('Method not allowed', status=405)


class DashboardView(LoginRequiredMixin, OnboardingRequiredMixin, TemplateView):
    """Main dashboard view."""
    template_name = 'portal/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        """Check if onboarding is complete before rendering dashboard."""
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        try:
            parent_profile = request.user.parent_profile
            # Check if onboarding is completed
            if not parent_profile.onboarding_completed:
                return redirect('portal:onboarding')
        except ParentProfile.DoesNotExist:
            # Redirect to onboarding if no profile
            return redirect('portal:onboarding')
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        parent_profile = self.request.user.parent_profile
        context['parent_profile'] = parent_profile
        
        # Get children and identify the active one
        children = parent_profile.children.all()
        active_child = children.filter(is_active=True).first()
        
        # fallback if none active
        if not active_child and children.exists():
            active_child = children.first()
            active_child.is_active = True
            active_child.save()
            
        context['children'] = children
        context['active_child'] = active_child
        context['has_children'] = children.exists()
        
        # Dashboard displays data for the ACTIVE child only
        if active_child:
            # Onboarding flags for active child
            context['all_tests_completed'] = active_child.reading_test_completed
            context['pending_test_child'] = active_child if not active_child.reading_test_completed else None
            
            # Active subscriptions for ACTIVE child
            active_subscriptions = SubscriptionCycle.objects.filter(
                parent=parent_profile,
                child=active_child,
                status__in=['ACTIVE', 'OVERDUE']
            ).select_related('child', 'plan').prefetch_related('physical_copies__book')
            
            context['active_subscriptions'] = active_subscriptions

            # Summary for active child highlight
            context['child_subscriptions_summary'] = [
                {'name': active_child.name, 'count': active_subscriptions.count()}
            ]

            # Calculate total books count for active child
            total_books = sum(
                cycle.books_count if cycle.books_count > 0 else cycle.plan.books_per_month 
                for cycle in active_subscriptions
            )
            context['total_books_count'] = total_books

            # Get borrowed books for active child
            borrowed_books = []
            for cycle in active_subscriptions:
                for physical_copy in cycle.physical_copies.all():
                    borrowed_books.append({
                        'book': physical_copy.book,
                        'child': active_child,
                        'due_date': cycle.expected_return_date,
                        'is_overdue': cycle.is_overdue,
                        'cycle': cycle
                    })
            context['borrowed_books'] = borrowed_books

            # Get recommended books for active child if test completed
            recommendations_by_child = []
            if active_child.reading_test_completed:
                recommendations_by_child.append({
                    'child': active_child,
                    'books': get_curated_books(active_child.id, limit=10)
                })
            context['recommendations_by_child'] = recommendations_by_child
            context['recommended_books'] = recommendations_by_child[0]['books'] if recommendations_by_child else Book.objects.none()

        # Global dashboard context
        context['all_subscription_plans'] = SubscriptionPlan.objects.filter(is_active=True).order_by('price_per_month')
        context['recent_orders'] = Order.objects.filter(
            parent=parent_profile
        ).order_by('-created_at')[:5]
        
        # Get random books from marketplace for explore section
        random_books = Book.objects.filter(
            is_active=True
        ).order_by('?')[:12]  # Get 12 random books
        
        context['recent_books'] = random_books

        return context


class FluencyCheckView(LoginRequiredMixin, OnboardingRequiredMixin, DetailView):
    """View for the multi-step fluency check."""
    model = Child
    template_name = 'portal/fluency_check.html'
    pk_url_kwarg = 'child_id'
    context_object_name = 'child'

    def get_queryset(self):
        return Child.objects.filter(parent__user=self.request.user)

    def get(self, request, *args, **kwargs):
        child = self.get_object()
        # If they are starting a test (even if it's the first one), 
        # we can consider the "Language Exploration" banner as seen/dismissed
        # since they are already in the test flow.
        if not child.has_tried_other_languages:
            child.has_tried_other_languages = True
            child.save()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        child = self.get_object()
        lang = self.request.GET.get('lang', 'EN').upper()
        if lang not in ['EN', 'HI', 'KN']:
            lang = 'EN'
            
        passage_idx = int(self.request.GET.get('p', 0))
        passage = get_passage_for_grade(child.grade, lang=lang, passage_idx=passage_idx)
        
        context['passage'] = passage
        context['current_lang'] = lang
        context['current_passage_idx'] = passage_idx
        return context


@login_required
def fluency_check_save(request, child_id):
    """Save results of the fluency check."""
    if request.method == 'POST':
        child = get_object_or_404(Child, id=child_id, parent__user=request.user)
        
        wpm = request.POST.get('wpm')
        accuracy = request.POST.get('accuracy')
        strengths = request.POST.get('strengths')
        gaps = request.POST.get('gaps')
        
        if wpm:
            child.reading_wpm = int(float(wpm))
            child.reading_test_completed = True
            
            if accuracy:
                child.reading_accuracy = float(accuracy)
            
            if strengths:
                child.reading_strengths = strengths
            
            if gaps:
                child.reading_gaps = gaps
            
            # Determine difficulty level based on WPM and Grade
            wpm_val = int(float(wpm))
            if wpm_val < 40:
                child.reading_difficulty_level = 'BEGINNER'
            elif wpm_val < 80:
                child.reading_difficulty_level = 'INTERMEDIATE'
            else:
                child.reading_difficulty_level = 'ADVANCED'
            
            child.save()
            
            return JsonResponse({
                'status': 'success',
                'wpm': child.reading_wpm,
                'level': child.get_reading_difficulty_level_display()
            })
            
    return JsonResponse({'status': 'error'}, status=400)


class CuratedBoxView(LoginRequiredMixin, OnboardingRequiredMixin, DetailView):
    """View curated books for a specific child."""
    template_name = 'portal/curated_box.html'
    context_object_name = 'child'

    def get_object(self):
        child = get_object_or_404(Child, id=self.kwargs['child_id'])

        # Ensure child belongs to current user
        if child.parent.user != self.request.user:
            raise PermissionError("You don't have access to this child's profile")

        return child

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        child = self.get_object()

        # Check if child has an active subscription
        from apps.orders.models import SubscriptionCycle
        active_subscription = SubscriptionCycle.objects.filter(
            child=child,
            status__in=['ACTIVE', 'OVERDUE']
        ).first()

        # Get curated books only if test is completed AND has active subscription
        if child.reading_test_completed and active_subscription:
            context['curated_books'] = get_curated_books(child.id, limit=20)
            context['active_subscription'] = active_subscription
        elif child.reading_test_completed and not active_subscription:
            # Reading test completed but no active subscription
            context['curated_books'] = Book.objects.none()
            context['no_subscription_message'] = f'{child.name} has completed the reading test! Subscribe to a plan to access curated book recommendations.'
        else:
            # Reading test not completed
            context['curated_books'] = Book.objects.none()
            context['active_subscription'] = None

        return context


class MarketplaceView(LoginRequiredMixin, OnboardingRequiredMixin, ListView):
    """Marketplace view with all purchasable books."""
    template_name = 'portal/marketplace.html'
    context_object_name = 'books'
    paginate_by = 12

    def get_queryset(self):
        queryset = Book.objects.filter(
            is_purchase_eligible=True,
            is_active=True,
            stock_count__gt=0
        )

        # Filter by difficulty if specified
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_rating=difficulty)

        # Filter by grade if specified
        grade = self.request.GET.get('grade')
        if grade:
            queryset = queryset.filter(
                Q(recommended_grade_min=grade) | Q(recommended_grade_max=grade)
            )

        return queryset.order_by('title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent_profile = self.request.user.parent_profile
        children = parent_profile.children.all()
        active_child = children.filter(is_active=True).first()
        
        context['difficulty_levels'] = Book.DIFFICULTY_RATING_CHOICES
        context['grades'] = Book.GRADE_CHOICES
        context['difficulty_groups'] = get_marketplace_groups()
        
        # Onboarding flags focused on ACTIVE child
        context['has_children'] = children.exists()
        if active_child:
            context['all_tests_completed'] = active_child.reading_test_completed
            context['pending_test_child'] = active_child if not active_child.reading_test_completed else None
        else:
            context['all_tests_completed'] = False
            context['pending_test_child'] = children.first() if children.exists() else None
        
        return context

def get_marketplace_groups(difficulty=None):
    """Helper to get sectioned book groups for marketplace."""
    difficulty_groups = []
    
    # If difficulty is specified, we only show that group
    if difficulty:
        choices = [(val, label) for val, label in Book.DIFFICULTY_RATING_CHOICES if val == difficulty]
    else:
        choices = Book.DIFFICULTY_RATING_CHOICES
        
    for val, label in choices:
        group_books = Book.objects.filter(
            is_purchase_eligible=True,
            is_active=True,
            stock_count__gt=0,
            difficulty_rating=val
        ).order_by('?')[:10]
        
        if group_books.exists():
            # Split "Beginner (Ages 3-6)" into "Beginner" and "Ages 3-6"
            name = label
            age = ""
            if " (" in label:
                name, age = label.split(" (", 1)
                age = age.replace("(", "").replace(")", "").strip()

            difficulty_groups.append({
                'value': val,
                'name': name,
                'age': age,
                'books': group_books
            })
    return difficulty_groups


@login_required
def marketplace_search(request):
    """HTMX handler for live marketplace search with filters and sorting."""
    query = request.GET.get('q', '').strip()
    difficulty = request.GET.get('difficulty', '').strip()
    grade = request.GET.get('grade', '').strip()
    sort = request.GET.get('sort', 'title').strip()

    books = Book.objects.filter(
        is_purchase_eligible=True,
        is_active=True,
        stock_count__gt=0
    )

    # If all primary search/filter fields are empty and we are using default sort, return the sectioned view
    # If a specific sort is applied (like New Arrivals or Popular), we want the grid view
    if not query and not difficulty and not grade and sort == 'title':
        return render(request, 'portal/components/marketplace_sectioned.html', {
            'difficulty_groups': get_marketplace_groups(),
            'difficulty_levels': Book.DIFFICULTY_RATING_CHOICES
        })

    # Apply search query
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(description__icontains=query) |
            Q(publisher__name__icontains=query) |
            Q(isbn__icontains=query)
        ).distinct()

    # Apply difficulty filter
    if difficulty:
        books = books.filter(difficulty_rating=difficulty)

    # Apply grade filter
    if grade:
        books = books.filter(
            Q(recommended_grade_min=grade) | Q(recommended_grade_max=grade)
        )

    # Apply sorting
    if sort:
        books = books.order_by(sort)
    else:
        books = books.order_by('title')

    return render(request, 'portal/components/book_results_grid.html', {
        'books': books,
        'difficulty_levels': Book.DIFFICULTY_RATING_CHOICES,
        'grades': Book.GRADE_CHOICES
    })


class BookDetailView(LoginRequiredMixin, OnboardingRequiredMixin, DetailView):
    """Book detail view."""
    model = Book
    template_name = 'portal/book_detail.html'
    pk_url_kwarg = 'book_id'
    context_object_name = 'book'


class OrdersView(LoginRequiredMixin, OnboardingRequiredMixin, TemplateView):
    """Orders history view with tabs for subscriptions and purchases."""
    template_name = 'portal/orders.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the active tab from query parameter
        tab = self.request.GET.get('tab', 'subscriptions')
        context['tab'] = tab
        
        parent_profile = self.request.user.parent_profile
        
        if tab == 'purchases':
            # Get purchase orders only
            context['orders'] = Order.objects.filter(
                parent=parent_profile,
                order_type='PURCHASE'
            ).order_by('-created_at')
        else:
            # Get subscription cycles
            context['subscription_cycles'] = SubscriptionCycle.objects.filter(
                parent=parent_profile
            ).select_related('child', 'plan', 'order').order_by('-created_at')
        
        return context


class OrderDetailView(LoginRequiredMixin, OnboardingRequiredMixin, DetailView):
    """Order detail view."""
    template_name = 'portal/order_detail.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'

    def get_queryset(self):
        return Order.objects.filter(parent__user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        
        # Add subscription cycle data for subscription orders
        if order.order_type == 'SUBSCRIPTION':
            try:
                subscription_cycle = SubscriptionCycle.objects.select_related(
                    'child', 'plan'
                ).prefetch_related(
                    'physical_copies__book'
                ).get(order=order)
                context['subscription_cycle'] = subscription_cycle
                context['subscription_books'] = subscription_cycle.physical_copies.all()
            except SubscriptionCycle.DoesNotExist:
                context['subscription_cycle'] = None
                context['subscription_books'] = []
        
        return context


class ProfileView(LoginRequiredMixin, OnboardingRequiredMixin, TemplateView):
    """User profile view."""
    template_name = 'portal/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent_profile = self.request.user.parent_profile
        context['parent_profile'] = parent_profile
        context['children'] = parent_profile.children.all()
        
        # Calculate completion percentage
        user = self.request.user
        fields = [
            user.first_name,
            user.email,
            parent_profile.phone_number,
            parent_profile.address,
            parent_profile.city,
            parent_profile.state,
            parent_profile.pincode,
            parent_profile.children.exists()
        ]
        completed = sum(1 for f in fields if f)
        context['profile_completion'] = int((completed / len(fields)) * 100)
        
        return context


@onboarding_required
def update_profile_name(request):
    """Update parent's core information."""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        
        # Standard validation for name
        if not first_name or len(first_name) < 2:
            messages.error(request, 'First name is required.')
            return redirect('portal:profile')
        
        user = request.user
        parent_profile = user.parent_profile
        
        # Update User model
        user.first_name = first_name.title()
        user.last_name = last_name.title() if last_name else ''
        if email:
            user.email = email
        user.save()
        
        # Update ParentProfile model
        if phone:
            parent_profile.phone_number = phone
        if address:
            parent_profile.address = address
        if city:
            parent_profile.city = city
        if state:
            parent_profile.state = state
        if pincode:
            parent_profile.pincode = pincode
            
        parent_profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('portal:profile')
    
    return redirect('portal:profile')


@onboarding_required
@login_required
def edit_child(request, child_id):
    """Display edit child form."""
    try:
        parent_profile = request.user.parent_profile
        child = get_object_or_404(Child, id=child_id, parent=parent_profile)
        
        if request.method == 'POST':
            # Handle form submission
            child.name = request.POST.get('name')
            child.grade = request.POST.get('grade')
            child.reading_wpm = request.POST.get('reading_wpm')
            child.reading_accuracy = request.POST.get('reading_accuracy')
            
            child.save()
            messages.success(request, f'{child.name}\'s details updated successfully!')
            return redirect('portal:profile')
        
        # GET request - show edit form
        return render(request, 'portal/edit_child.html', {
            'child': child,
            'grades': Child.GRADE_CHOICES,
        })
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('portal:profile')

@login_required
def update_child(request, child_id):
    """Update child details via AJAX or form submission."""
    if request.method == 'POST':
        try:
            parent_profile = request.user.parent_profile
            child = get_object_or_404(Child, id=child_id, parent=parent_profile)
            
            # Update child details
            child.name = request.POST.get('name')
            child.grade = request.POST.get('grade')
            if request.POST.get('reading_wpm'):
                child.reading_wpm = int(request.POST.get('reading_wpm'))
            if request.POST.get('reading_accuracy'):
                child.reading_accuracy = float(request.POST.get('reading_accuracy'))
            
            child.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX request - return JSON response
                return JsonResponse({
                    'success': True,
                    'message': f'{child.name} updated successfully!'
                })
            else:
                # Regular form submission - redirect with success message
                messages.success(request, f'{child.name}\'s details updated successfully!')
                return redirect('portal:profile')
                
        except Child.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Child not found'}, status=404)
            else:
                messages.error(request, 'Child not found')
                return redirect('portal:profile')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            else:
                messages.error(request, f'Error updating child: {str(e)}')
                return redirect('portal:profile')

def toggle_child_status(request, child_id):
    """Set a child as the active profile and deactivate others."""
    if request.method == 'POST':
        try:
            child = get_object_or_404(Child, id=child_id, parent__user=request.user)
            
            # Deactivate all other children
            Child.objects.filter(parent=child.parent).exclude(id=child.id).update(is_active=False)
            
            # Activate this child
            child.is_active = True
            child.save()
            
            message = f"{child.name} is now the active profile."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
                return JsonResponse({'status': 'success', 'message': message})
                
            messages.success(request, message)
            return redirect('portal:profile')
        except Child.DoesNotExist:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
                return JsonResponse({'status': 'error', 'message': 'Child not found'}, status=404)
            else:
                messages.error(request, 'Child not found')
                return redirect('portal:profile')
        except Exception as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            else:
                messages.error(request, f'Error updating child: {str(e)}')
                return redirect('portal:profile')
    
    return HttpResponse('Method not allowed', status=405)


@login_required
def dismiss_language_banner(request, child_id):
    """API endpoint to dismiss the language exploration banner for a child."""
    if request.method == 'POST':
        child = get_object_or_404(Child, id=child_id, parent__user=request.user)
        child.has_tried_other_languages = True
        child.save()
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)



class AddChildView(LoginRequiredMixin, OnboardingRequiredMixin, TemplateView):
    """Add child profile view."""
    template_name = 'portal/add_child.html'

    def post(self, request):
        parent_profile = request.user.parent_profile

        # Check limit
        if parent_profile.children.count() >= 5:
            return render(request, self.template_name, {
                'error': 'Maximum 5 children allowed per parent'
            })

        # Create child
        name = request.POST.get('name', '').strip()
        if len(name) > 15:
            return render(request, self.template_name, {
                'error': 'Child name cannot exceed 15 characters'
            })

        age = request.POST.get('age')
        grade = request.POST.get('grade')
        reading_level = request.POST.get('reading_level')
        dob = request.POST.get('date_of_birth')

        Child.objects.create(
            parent=parent_profile,
            name=name.title(),
            age=age,
            grade=grade,
            reading_difficulty_level=reading_level,
            date_of_birth=dob
        )

        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)

        return redirect('portal:profile')


class EditChildView(LoginRequiredMixin, OnboardingRequiredMixin, DetailView):
    """Edit child profile view."""
    template_name = 'portal/edit_child.html'
    context_object_name = 'child'
    pk_url_kwarg = 'child_id'

    def get_queryset(self):
        return Child.objects.filter(parent__user=self.request.user)

    def post(self, request, child_id):
        child = self.get_object()

        # Update child (capitalize name)
        name = request.POST.get('name', '').strip()
        if len(name) > 15:
            return render(request, self.template_name, {
                'error': 'Child name cannot exceed 15 characters',
                'child': child
            })
        
        child.name = name.title()
        interests = request.POST.get('interests', '').strip()
        child.interests = interests.title() if interests else ''
        child.age = request.POST.get('age')
        child.grade = request.POST.get('grade')
        child.reading_difficulty_level = request.POST.get('reading_level')
        child.date_of_birth = request.POST.get('date_of_birth')
        child.save()

        return redirect('portal:profile')


# ===========================
# Subscription Management
# ===========================

def is_address_complete(parent_profile):
    """Check if parent profile has complete delivery address."""
    required_fields = [
        parent_profile.phone_number,
        parent_profile.address,
        parent_profile.city,
        parent_profile.state,
        parent_profile.pincode
    ]
    return all(field and str(field).strip() for field in required_fields)


class PlansView(LoginRequiredMixin, OnboardingRequiredMixin, TemplateView):
    """View to display all available subscription plans in an appealing way."""
    template_name = 'portal/plans.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_subscription_plans'] = SubscriptionPlan.objects.filter(is_active=True).order_by('price_per_month')
        return context


class SubscribeView(LoginRequiredMixin, TemplateView):
    """Subscribe to a plan for a child."""
    template_name = 'portal/subscribe.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        child_id = self.kwargs.get('child_id')

        if child_id:
            child = get_object_or_404(Child, id=child_id, parent__user=self.request.user)
            context['child'] = child
            
            # Get active subscription for this child
            active_subscription = SubscriptionCycle.objects.filter(
                child=child,
                status__in=['ACTIVE', 'OVERDUE']
            ).select_related('plan').first()
            
            context['active_subscription'] = active_subscription
            
            # If child already has an active subscription, redirect to dashboard
            if active_subscription:
                from django.contrib import messages
                messages.warning(self.request, f'{child.name} already has an active subscription. Each child can only have one subscription at a time.')
                return context

        context['children'] = Child.objects.filter(parent__user=self.request.user)
        
        # Check if a specific plan was selected from the plans page
        selected_plan_id = self.request.GET.get('plan')
        if selected_plan_id:
            try:
                selected_plan = SubscriptionPlan.objects.get(id=selected_plan_id, is_active=True)
                # Show only the selected plan
                context['subscription_plans'] = [selected_plan]
                context['selected_plan_id'] = selected_plan_id
            except SubscriptionPlan.DoesNotExist:
                # If plan doesn't exist, show all plans
                context['subscription_plans'] = SubscriptionPlan.objects.filter(is_active=True)
        else:
            # Show all active plans
            context['subscription_plans'] = SubscriptionPlan.objects.filter(is_active=True)
            
        # Check if address is complete
        context['address_complete'] = is_address_complete(self.request.user.parent_profile)
        
        return context

    def post(self, request, child_id=None):
        """Create subscription order and redirect to COD confirmation."""
        plan_id = request.POST.get('plan_id')
        child_id = request.POST.get('child_id', child_id)
        payment_method = request.POST.get('payment_method', 'COD')

        if not plan_id or not child_id:
            return render(request, self.template_name, {
                'error': 'Please select both a child and a plan',
                'children': Child.objects.filter(parent__user=request.user),
                'subscription_plans': SubscriptionPlan.objects.filter(is_active=True)
            })

        parent_profile = request.user.parent_profile
        plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
        child = get_object_or_404(Child, id=child_id, parent=parent_profile)

        # Check for existing active subscription
        existing_subscription = SubscriptionCycle.objects.filter(
            child=child,
            status__in=['ACTIVE', 'OVERDUE']
        ).select_related('plan').first()

        if existing_subscription:
            return render(request, self.template_name, {
                'error': f'{child.name} already has an active subscription ({existing_subscription.plan.name}). Each child can only have one subscription at a time. Please wait until it expires or contact support.',
                'child': child,
                'children': Child.objects.filter(parent__user=request.user),
                'subscription_plans': SubscriptionPlan.objects.filter(is_active=True),
                'active_subscription': existing_subscription
            })
        

        # Create subscription order with payment method
        # Get delivery address from form (not from profile)
        delivery_phone = request.POST.get('delivery_phone', '').strip()
        delivery_address = request.POST.get('delivery_address', '').strip()
        delivery_city = request.POST.get('delivery_city', '').strip()
        delivery_state = request.POST.get('delivery_state', '').strip()
        delivery_pincode = request.POST.get('delivery_pincode', '').strip()
        
        # Validate delivery address
        if not all([delivery_phone, delivery_address, delivery_city, delivery_state, delivery_pincode]):
            return render(request, self.template_name, {
                'error': 'Please provide complete delivery address.',
                'child': child,
                'children': Child.objects.filter(parent__user=request.user),
                'subscription_plans': SubscriptionPlan.objects.filter(is_active=True)
            })
        
        order = Order.objects.create(
            parent=parent_profile,
            order_type='SUBSCRIPTION',
            status='PENDING',
            payment_method=payment_method,
            total_amount=plan.price_per_month,
            # Save delivery address from form
            delivery_name=request.user.get_full_name() or request.user.username,
            delivery_phone=delivery_phone,
            delivery_address=delivery_address.title(),
            delivery_city=delivery_city.title(),
            delivery_state=delivery_state.title(),
            delivery_pincode=delivery_pincode
        )

        # Create subscription cycle (books will be assigned after payment)
        from datetime import date, timedelta
        issue_date = date.today()
        expected_return = issue_date + timedelta(days=30)

        SubscriptionCycle.objects.create(
            parent=parent_profile,
            child=child,
            plan=plan,
            order=order,
            issue_date=issue_date,
            expected_return_date=expected_return,
            status='ACTIVE'
        )

        # Redirect to order detail page (same as book purchase flow)
        return redirect('portal:order_detail', order_id=order.id)



# ===========================
# Return Workflow
# ===========================

class NotificationsView(LoginRequiredMixin, OnboardingRequiredMixin, TemplateView):
    template_name = 'portal/notifications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mark as seen for this session
        self.request.session['notifications_seen'] = True
        return context


class MyBooksView(LoginRequiredMixin, OnboardingRequiredMixin, TemplateView):
    """View all borrowed books and their return status."""
    template_name = 'portal/my_books.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent_profile = self.request.user.parent_profile

        # Get all active and overdue subscriptions
        context['active_cycles'] = SubscriptionCycle.objects.filter(
            parent=parent_profile,
            status__in=['ACTIVE', 'OVERDUE']
        ).select_related('child', 'plan').prefetch_related('physical_copies')

        # Get returned cycles (last 5)
        context['returned_cycles'] = SubscriptionCycle.objects.filter(
            parent=parent_profile,
            status='RETURNED'
        ).select_related('child', 'plan').prefetch_related('physical_copies')[:5]

        return context


@onboarding_required
def initiate_return(request, cycle_id):
    """Initiate return request for a subscription cycle."""
    if request.method == 'POST':
        parent_profile = request.user.parent_profile
        cycle = get_object_or_404(
            SubscriptionCycle,
            id=cycle_id,
            parent=parent_profile,
            status__in=['ACTIVE', 'OVERDUE']
        )

        # Get condition notes from form
        condition_notes = request.POST.get('condition_notes', '')

        # Process return using curation service
        from services.curation import return_subscription_books
        success, message = return_subscription_books(cycle, condition_notes)

        if success:
            return redirect('portal:my_books')
        else:
            return render(request, 'portal/my_books.html', {
                'error': message,
                'active_cycles': SubscriptionCycle.objects.filter(
                    parent=parent_profile,
                    status__in=['ACTIVE', 'OVERDUE']
                )
            })

    return HttpResponse('Method not allowed', status=405)


# ===========================
# Purchase Workflow (Cart)
# ===========================

@login_required
@onboarding_required
def add_to_cart(request, book_id):
    """Add a book to the shopping cart (session-based)."""
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id, is_purchase_eligible=True, is_active=True)

        # Get or create cart in session
        cart = request.session.get('cart', {})

        # Add book to cart (or increment quantity)
        book_id_str = str(book_id)
        if book_id_str in cart:
            # Check stock before incrementing
            if cart[book_id_str]['quantity'] < book.stock_count:
                cart[book_id_str]['quantity'] += 1
        else:
            cart[book_id_str] = {
                'quantity': 1,
                'title': book.title,
                'price': float(book.mrp),
                'cover_image': book.cover_image.url if book.cover_image else None
            }

        request.session['cart'] = cart
        request.session.modified = True

        # Return HTMX response or redirect
        if request.headers.get('HX-Request'):
            return HttpResponse(f'<div class="text-green-600">Added to cart!</div>')
        else:
            return redirect('portal:cart')

    return HttpResponse('Method not allowed', status=405)


@onboarding_required
def remove_from_cart(request, book_id):
    """Remove a book from the cart."""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        book_id_str = str(book_id)

        if book_id_str in cart:
            del cart[book_id_str]
            request.session['cart'] = cart
            request.session.modified = True

        return redirect('portal:cart')

    return HttpResponse('Method not allowed', status=405)


@onboarding_required
def update_cart_quantity(request, book_id):
    """Update quantity of a book in cart."""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        book_id_str = str(book_id)
        quantity = int(request.POST.get('quantity', 1))

        if book_id_str in cart and quantity > 0:
            book = get_object_or_404(Book, id=book_id)
            # Check stock
            if quantity <= book.stock_count:
                cart[book_id_str]['quantity'] = quantity
                request.session['cart'] = cart
                request.session.modified = True

        return redirect('portal:cart')

    return HttpResponse('Method not allowed', status=405)


class CartView(LoginRequiredMixin, OnboardingRequiredMixin, TemplateView):
    """Shopping cart view."""
    template_name = 'portal/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.request.session.get('cart', {})

        # Calculate totals
        cart_items = []
        total = 0
        for book_id, item in cart.items():
            subtotal = item['price'] * item['quantity']
            cart_items.append({
                'book_id': book_id,
                'title': item['title'],
                'price': item['price'],
                'quantity': item['quantity'],
                'subtotal': subtotal,
                'cover_image': item.get('cover_image')
            })
            total += subtotal

        context['cart_items'] = cart_items
        context['cart_total'] = total
        context['cart_count'] = sum(item['quantity'] for item in cart.values())
        
        # Check if address is complete
        parent_profile = self.request.user.parent_profile
        address_complete = all([
            parent_profile.phone_number,
            parent_profile.address,
            parent_profile.city,
            parent_profile.state,
            parent_profile.pincode
        ])
        context['address_complete'] = address_complete

        return context


@login_required
@onboarding_required
def checkout(request):
    """Process checkout and create purchase order."""
    if request.method == 'POST':
        cart = request.session.get('cart', {})

        if not cart:
            return redirect('portal:cart')

        parent_profile = request.user.parent_profile
        payment_method = request.POST.get('payment_method', 'ONLINE')
        
        # Get delivery address from form (not from profile)
        delivery_phone = request.POST.get('delivery_phone', '').strip()
        delivery_address = request.POST.get('delivery_address', '').strip()
        delivery_city = request.POST.get('delivery_city', '').strip()
        delivery_state = request.POST.get('delivery_state', '').strip()
        delivery_pincode = request.POST.get('delivery_pincode', '').strip()
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Checkout Debug - Phone: [{delivery_phone}], Address: [{delivery_address}], City: [{delivery_city}], State: [{delivery_state}], Pincode: [{delivery_pincode}]")
        
        # Validate delivery address
        if not all([delivery_phone, delivery_address, delivery_city, delivery_state, delivery_pincode]):
            logger.error(f"Validation failed - Missing fields")
            messages.error(request, 'Please provide complete delivery address.')
            return redirect('portal:cart')

        # Calculate total
        total = sum(item['price'] * item['quantity'] for item in cart.values())

        # Create purchase order with payment method
        order = Order.objects.create(
            parent=parent_profile,
            order_type='PURCHASE',
            status='PENDING',
            payment_method=payment_method,
            total_amount=total,
            # Save delivery address from form
            delivery_name=request.user.get_full_name() or request.user.username,
            delivery_phone=delivery_phone,
            delivery_address=delivery_address.title(),
            delivery_city=delivery_city.title(),
            delivery_state=delivery_state.title(),
            delivery_pincode=delivery_pincode
        )

        # Create order items (we'll need to create OrderItem model)
        from apps.orders.models import OrderItem
        for book_id, item in cart.items():
            book = Book.objects.get(id=book_id)
            OrderItem.objects.create(
                order=order,
                book=book,
                quantity=item['quantity'],
                price_per_unit=item['price']
            )

        # Clear cart
        request.session['cart'] = {}
        request.session.modified = True

        # Redirect to payment
        return redirect('payments:initiate_payment', order_id=order.id)

    return HttpResponse('Method not allowed', status=405)


class SupportView(LoginRequiredMixin, OnboardingRequiredMixin, TemplateView):
    """View for logging complaints and issues."""
    template_name = 'portal/support.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent_profile = self.request.user.parent_profile
        context['form'] = ComplaintForm(parent=parent_profile)
        context['my_complaints'] = Complaint.objects.filter(parent=parent_profile).order_by('-created_at')
        return context

    def post(self, request, *args, **kwargs):
        parent_profile = request.user.parent_profile
        form = ComplaintForm(request.POST, parent=parent_profile)

        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.parent = parent_profile
            complaint.save()

            # Prepare email notification to admin
            admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
            subject = f"New Complaint: {complaint.get_category_display()} - {complaint.subject}"
            
            # Simple text message for email
            message = f"""
New complaint received from {request.user.get_full_name() or request.user.username}.

Category: {complaint.get_category_display()}
Subject: {complaint.subject}
Description:
{complaint.description}

Order Reference: {complaint.order if complaint.order else 'N/A'}

View in Admin: {request.build_absolute_uri('/admin/portal/complaint/' + str(complaint.id) + '/change/')}
            """

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [admin_email],
                    fail_silently=False,
                )
            except Exception as e:
                # Log error or notify user that email failed but complaint saved
                pass

            messages.success(request, "Your complaint has been submitted successfully. Our team will review it and get back to you shortly.")
            return redirect('portal:support')

        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


class UpdateDeliveryAddressView(LoginRequiredMixin, OnboardingRequiredMixin, TemplateView):
    """View to update delivery address before payment."""
    template_name = 'portal/update_delivery_address.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_profile'] = self.request.user.parent_profile
        return context

    def post(self, request):
        parent_profile = request.user.parent_profile
        
        # Update delivery address
        phone_number = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        
        # Validate required fields
        if not all([phone_number, address, city, state, pincode]):
            messages.error(request, 'All address fields are required.')
            return redirect('portal:update_delivery_address')
        
        # Update parent profile
        parent_profile.phone_number = phone_number
        parent_profile.address = address.title()
        parent_profile.city = city.title()
        parent_profile.state = state.title()
        parent_profile.pincode = pincode
        parent_profile.save()
        
        messages.success(request, 'Delivery address updated successfully!')
        
        # Check if there's a pending subscription - redirect back to subscribe page
        pending_subscription = request.session.get('pending_subscription')
        if pending_subscription:
            child_id = pending_subscription['child_id']
            # Keep the session data so the form remembers the selection
            return redirect('portal:subscribe_child', child_id=child_id)
        
        # Check if there's a pending checkout - redirect back to cart
        pending_checkout = request.session.get('pending_checkout')
        if pending_checkout:
            # Keep the session data
            return redirect('portal:cart')
        
        # Default redirect to profile
        return redirect('portal:profile')

