from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.http import HttpResponse
from django.db.models import Q

from apps.profiles.models import ParentProfile, Child
from apps.catalog.models import Book
from apps.orders.models import Order, SubscriptionCycle, SubscriptionPlan
from services.curation import get_curated_books


class RegisterView(TemplateView):
    """User registration view."""
    template_name = 'portal/register.html'

    def post(self, request):
        # Simple registration (can be enhanced with forms)
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            return render(request, self.template_name, {'error': 'Passwords do not match'})

        if User.objects.filter(username=username).exists():
            return render(request, self.template_name, {'error': 'Username already exists'})

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)

        return redirect('portal:onboarding')


class OnboardingView(LoginRequiredMixin, TemplateView):
    """Multi-step onboarding with HTMX."""
    template_name = 'portal/onboarding.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if parent profile exists
        try:
            context['parent_profile'] = self.request.user.parent_profile
        except ParentProfile.DoesNotExist:
            context['parent_profile'] = None

        context['subscription_plans'] = SubscriptionPlan.objects.filter(is_active=True)
        return context


@login_required
def onboarding_step2(request):
    """HTMX handler for step 2 - parent info."""
    if request.method == 'POST':
        # Create or update parent profile
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')

        parent_profile, created = ParentProfile.objects.update_or_create(
            user=request.user,
            defaults={
                'phone_number': phone_number,
                'address': address,
                'city': city,
                'state': state,
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

        # Create child
        name = request.POST.get('name')
        age = request.POST.get('age')
        grade = request.POST.get('grade')
        reading_level = request.POST.get('reading_level')
        dob = request.POST.get('date_of_birth')

        child = Child.objects.create(
            parent=parent_profile,
            name=name,
            age=age,
            grade=grade,
            reading_difficulty_level=reading_level,
            date_of_birth=dob
        )

        # Return step 3 template (plan selection)
        subscription_plans = SubscriptionPlan.objects.filter(is_active=True)
        return render(request, 'portal/onboarding_step3.html', {
            'child': child,
            'subscription_plans': subscription_plans
        })

    return HttpResponse('Method not allowed', status=405)


@login_required
def onboarding_complete(request):
    """HTMX handler for onboarding completion."""
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')

        # In a real app, would create order and redirect to payment
        # For now, just redirect to dashboard
        return redirect('portal:dashboard')

    return HttpResponse('Method not allowed', status=405)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view."""
    template_name = 'portal/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            parent_profile = self.request.user.parent_profile
            context['parent_profile'] = parent_profile
            context['children'] = parent_profile.children.all()

            # Get active subscriptions
            context['active_subscriptions'] = SubscriptionCycle.objects.filter(
                parent=parent_profile,
                status__in=['ACTIVE', 'OVERDUE']
            ).select_related('child', 'plan')

            # Get recent orders
            context['recent_orders'] = Order.objects.filter(
                parent=parent_profile
            ).order_by('-created_at')[:5]

        except ParentProfile.DoesNotExist:
            # Redirect to onboarding if no profile
            return redirect('portal:onboarding')

        return context


class CuratedBoxView(LoginRequiredMixin, DetailView):
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

        # Get curated books
        context['curated_books'] = get_curated_books(child.id, limit=12)

        return context


class MarketplaceView(LoginRequiredMixin, ListView):
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
        context['difficulty_levels'] = Book.DIFFICULTY_RATING_CHOICES
        context['grades'] = Book.GRADE_CHOICES
        return context


@login_required
def marketplace_search(request):
    """HTMX handler for live marketplace search."""
    query = request.GET.get('q', '')

    books = Book.objects.filter(
        is_purchase_eligible=True,
        is_active=True,
        stock_count__gt=0
    )

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(description__icontains=query)
        )

    books = books.order_by('title')[:12]

    return render(request, 'portal/components/book_grid.html', {'books': books})


class BookDetailView(LoginRequiredMixin, DetailView):
    """Book detail view."""
    model = Book
    template_name = 'portal/book_detail.html'
    pk_url_kwarg = 'book_id'
    context_object_name = 'book'


class OrdersView(LoginRequiredMixin, ListView):
    """Orders history view."""
    template_name = 'portal/orders.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(
            parent__user=self.request.user
        ).order_by('-created_at')


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Order detail view."""
    template_name = 'portal/order_detail.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'

    def get_queryset(self):
        return Order.objects.filter(parent__user=self.request.user)


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view."""
    template_name = 'portal/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_profile'] = self.request.user.parent_profile
        context['children'] = self.request.user.parent_profile.children.all()
        return context


class AddChildView(LoginRequiredMixin, TemplateView):
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
        name = request.POST.get('name')
        age = request.POST.get('age')
        grade = request.POST.get('grade')
        reading_level = request.POST.get('reading_level')
        dob = request.POST.get('date_of_birth')

        Child.objects.create(
            parent=parent_profile,
            name=name,
            age=age,
            grade=grade,
            reading_difficulty_level=reading_level,
            date_of_birth=dob
        )

        return redirect('portal:profile')


class EditChildView(LoginRequiredMixin, DetailView):
    """Edit child profile view."""
    template_name = 'portal/edit_child.html'
    context_object_name = 'child'
    pk_url_kwarg = 'child_id'

    def get_queryset(self):
        return Child.objects.filter(parent__user=self.request.user)

    def post(self, request, child_id):
        child = self.get_object()

        # Update child
        child.name = request.POST.get('name')
        child.age = request.POST.get('age')
        child.grade = request.POST.get('grade')
        child.reading_difficulty_level = request.POST.get('reading_level')
        child.date_of_birth = request.POST.get('date_of_birth')
        child.save()

        return redirect('portal:profile')
