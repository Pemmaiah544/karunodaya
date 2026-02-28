import json
import logging
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseBadRequest
from django.contrib import messages

from apps.feedback.models import AppFeedback, CycleFeedback
from apps.orders.models import SubscriptionCycle


def onboarding_required(view_func):
    """Decorator to check if user has completed onboarding."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('portal:login')
        try:
            parent_profile = request.user.parent_profile
            if not parent_profile.onboarding_completed:
                return redirect('portal:onboarding')
        except AttributeError:
            return redirect('portal:onboarding')
        return view_func(request, *args, **kwargs)
    return wrapper

logger = logging.getLogger(__name__)


@login_required
@onboarding_required
@require_http_methods(["GET", "POST"])
def app_feedback(request):
    """
    General app feedback form view.
    GET: Render the feedback form
    POST: Process feedback submission
    """
    parent = request.user.parent_profile

    if request.method == "POST":
        rating = request.POST.get("rating")
        going_well = request.POST.getlist("going_well")
        needs_improvement = request.POST.getlist("needs_improvement")
        comments = request.POST.get("comments", "").strip()

        # Validate required field
        if not rating:
            messages.error(request, "Please provide a rating.")
            return render(request, "feedback/app_feedback.html")

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError("Invalid rating")
        except (ValueError, TypeError):
            messages.error(request, "Invalid rating provided.")
            return render(request, "feedback/app_feedback.html")

        # Create feedback
        try:
            AppFeedback.objects.create(
                parent=parent,
                rating=rating,
                going_well=going_well,
                needs_improvement=needs_improvement,
                comments=comments,
            )
            messages.success(request, "Thank you! Your feedback has been submitted.")
            return redirect("portal:dashboard")
        except Exception as e:
            logger.error(f"Error creating feedback: {e}")
            messages.error(request, "An error occurred while submitting feedback.")
            return render(request, "feedback/app_feedback.html")

    # GET: Render form
    context = {
        "going_well_choices": AppFeedback.GOING_WELL_CHOICES,
        "needs_improvement_choices": AppFeedback.NEEDS_IMPROVEMENT_CHOICES,
    }
    return render(request, "feedback/app_feedback.html", context)


@login_required
@onboarding_required
@require_http_methods(["GET", "POST"])
def cycle_feedback(request, cycle_id):
    """
    Feedback for a specific subscription cycle after return.
    GET: Render the feedback form
    POST: Process feedback submission
    """
    try:
        cycle = SubscriptionCycle.objects.get(id=cycle_id)
    except SubscriptionCycle.DoesNotExist:
        messages.error(request, "Subscription cycle not found.")
        return redirect("portal:my_books")

    # Check if parent owns this cycle
    parent = request.user.parent_profile
    if cycle.parent != parent:
        messages.error(request, "You don't have permission to access this cycle.")
        return redirect("portal:my_books")

    # Check if feedback already exists
    if CycleFeedback.objects.filter(cycle=cycle).exists():
        messages.info(
            request, "You've already provided feedback for this cycle."
        )
        return redirect("portal:my_books")

    if request.method == "POST":
        rating = request.POST.get("rating")
        enjoyed = request.POST.getlist("enjoyed")
        needs_improvement = request.POST.getlist("needs_improvement")
        comments = request.POST.get("comments", "").strip()

        # Validate required field
        if not rating:
            messages.error(request, "Please provide a rating.")
            return render(
                request,
                "feedback/cycle_feedback.html",
                {
                    "cycle": cycle,
                    "enjoyed_choices": CycleFeedback.ENJOYED_CHOICES,
                    "needs_improvement_choices": CycleFeedback.NEEDS_IMPROVEMENT_CHOICES,
                },
            )

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError("Invalid rating")
        except (ValueError, TypeError):
            messages.error(request, "Invalid rating provided.")
            return render(
                request,
                "feedback/cycle_feedback.html",
                {
                    "cycle": cycle,
                    "enjoyed_choices": CycleFeedback.ENJOYED_CHOICES,
                    "needs_improvement_choices": CycleFeedback.NEEDS_IMPROVEMENT_CHOICES,
                },
            )

        # Create feedback
        try:
            CycleFeedback.objects.create(
                cycle=cycle,
                parent=parent,
                child=cycle.child,
                rating=rating,
                enjoyed=enjoyed,
                needs_improvement=needs_improvement,
                comments=comments,
            )
            messages.success(request, "Thank you! Your feedback has been submitted.")
            return redirect("portal:my_books")
        except Exception as e:
            logger.error(f"Error creating cycle feedback: {e}")
            messages.error(request, "An error occurred while submitting feedback.")
            return render(
                request,
                "feedback/cycle_feedback.html",
                {
                    "cycle": cycle,
                    "enjoyed_choices": CycleFeedback.ENJOYED_CHOICES,
                    "needs_improvement_choices": CycleFeedback.NEEDS_IMPROVEMENT_CHOICES,
                },
            )

    # GET: Render form
    context = {
        "cycle": cycle,
        "enjoyed_choices": CycleFeedback.ENJOYED_CHOICES,
        "needs_improvement_choices": CycleFeedback.NEEDS_IMPROVEMENT_CHOICES,
    }
    return render(request, "feedback/cycle_feedback.html", context)
