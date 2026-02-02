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
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .forms import ComplaintForm, RegisterForm
from .models import Complaint
from services.curation import get_curated_books


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


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view."""
    template_name = 'portal/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        """Check if onboarding is complete before rendering dashboard."""
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
        context['children'] = parent_profile.children.all()

        # Get active subscriptions
        context['active_subscriptions'] = SubscriptionCycle.objects.filter(
            parent=parent_profile,
            status__in=['ACTIVE', 'OVERDUE']
        ).select_related('child', 'plan').prefetch_related('physical_copies__book')

        # Get borrowed books (from active subscriptions)
        borrowed_books = []
        for cycle in context['active_subscriptions']:
            for physical_copy in cycle.physical_copies.all():
                borrowed_books.append({
                    'book': physical_copy.book,
                    'child': cycle.child,
                    'due_date': cycle.expected_return_date,
                    'is_overdue': cycle.is_overdue,
                    'cycle': cycle
                })
        context['borrowed_books'] = borrowed_books

        # Get recent orders
        context['recent_orders'] = Order.objects.filter(
            parent=parent_profile
        ).order_by('-created_at')[:5]

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

    return render(request, 'portal/components/book_grid.html', {'books': books})


class BookDetailView(LoginRequiredMixin, DetailView):
    """Book detail view."""
    model = Book
    template_name = 'portal/book_detail.html'
    pk_url_kwarg = 'book_id'
    context_object_name = 'book'


class OrdersView(LoginRequiredMixin, TemplateView):
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


class OrderDetailView(LoginRequiredMixin, DetailView):
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


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view."""
    template_name = 'portal/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_profile'] = self.request.user.parent_profile
        context['children'] = self.request.user.parent_profile.children.all()
        return context


@login_required
def update_profile_name(request):
    """Update user's first and last name."""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        # Validate first name (required)
        if not first_name or len(first_name) < 2 or len(first_name) > 50:
            messages.error(request, 'First name must be between 2 and 50 characters.')
            return redirect('portal:profile')
        
        # Check if first name contains at least one letter
        if not any(c.isalpha() for c in first_name):
            messages.error(request, 'First name must contain at least one letter.')
            return redirect('portal:profile')
        
        # Check if first name contains only letters and spaces
        if not all(c.isalpha() or c.isspace() for c in first_name):
            messages.error(request, 'First name can only contain letters and spaces.')
            return redirect('portal:profile')
        
        # Validate last name (optional, but if provided must be valid)
        if last_name:
            if len(last_name) < 2 or len(last_name) > 50:
                messages.error(request, 'Last name must be between 2 and 50 characters.')
                return redirect('portal:profile')
            
            if not any(c.isalpha() for c in last_name):
                messages.error(request, 'Last name must contain at least one letter.')
                return redirect('portal:profile')
            
            if not all(c.isalpha() or c.isspace() for c in last_name):
                messages.error(request, 'Last name can only contain letters and spaces.')
                return redirect('portal:profile')
        
        # Update user's name (capitalize first letter of each word)
        user = request.user
        user.first_name = first_name.title()
        user.last_name = last_name.title() if last_name else ''
        user.save()
        
        messages.success(request, 'Your name has been updated successfully!')
        return redirect('portal:profile')
    
    return redirect('portal:profile')



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

        # Update child (capitalize name)
        child.name = request.POST.get('name', '').strip().title()
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

class SubscribeView(LoginRequiredMixin, TemplateView):
    """Subscribe to a plan for a child."""
    template_name = 'portal/subscribe.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        child_id = self.kwargs.get('child_id')

        if child_id:
            child = get_object_or_404(Child, id=child_id, parent__user=self.request.user)
            context['child'] = child

        context['children'] = Child.objects.filter(parent__user=self.request.user)
        context['subscription_plans'] = SubscriptionPlan.objects.filter(is_active=True)
        return context

    def post(self, request, child_id=None):
        """Create subscription order and redirect to payment."""
        plan_id = request.POST.get('plan_id')
        child_id = request.POST.get('child_id', child_id)
        payment_method = request.POST.get('payment_method', 'ONLINE')  # Get payment method

        if not plan_id or not child_id:
            return render(request, self.template_name, {
                'error': 'Please select both a child and a plan',
                'children': Child.objects.filter(parent__user=request.user),
                'subscription_plans': SubscriptionPlan.objects.filter(is_active=True)
            })

        parent_profile = request.user.parent_profile
        plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
        child = get_object_or_404(Child, id=child_id, parent=parent_profile)

        # Create subscription order with payment method
        order = Order.objects.create(
            parent=parent_profile,
            order_type='SUBSCRIPTION',
            status='PENDING',
            payment_method=payment_method,
            total_amount=plan.price_per_month,
            # Save delivery address snapshot
            delivery_name=request.user.get_full_name() or request.user.username,
            delivery_phone=parent_profile.phone_number,
            delivery_address=parent_profile.address,
            delivery_city=parent_profile.city,
            delivery_state=parent_profile.state,
            delivery_pincode=parent_profile.pincode
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

        # Redirect to payment
        return redirect('payments:initiate_payment', order_id=order.id)



# ===========================
# Return Workflow
# ===========================

class MyBooksView(LoginRequiredMixin, TemplateView):
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


@login_required
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


@login_required
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


@login_required
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


class CartView(LoginRequiredMixin, TemplateView):
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

        return context


@login_required
def checkout(request):
    """Process checkout and create purchase order."""
    if request.method == 'POST':
        cart = request.session.get('cart', {})

        if not cart:
            return redirect('portal:cart')

        parent_profile = request.user.parent_profile
        payment_method = request.POST.get('payment_method', 'ONLINE')  # Get payment method

        # Calculate total
        total = sum(item['price'] * item['quantity'] for item in cart.values())

        # Create purchase order with payment method
        order = Order.objects.create(
            parent=parent_profile,
            order_type='PURCHASE',
            status='PENDING',
            payment_method=payment_method,
            total_amount=total,
            # Save delivery address snapshot
            delivery_name=request.user.get_full_name() or request.user.username,
            delivery_phone=parent_profile.phone_number,
            delivery_address=parent_profile.address,
            delivery_city=parent_profile.city,
            delivery_state=parent_profile.state,
            delivery_pincode=parent_profile.pincode
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


class SupportView(LoginRequiredMixin, TemplateView):
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

