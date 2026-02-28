from django.contrib import admin
from django.contrib.admin.filters import ChoicesFieldListFilter
from django.db.models import Avg, Count
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from apps.core.admin_mixins import AdminPaginationMixin
from apps.feedback.models import AppFeedback, CycleFeedback


def render_stars(rating):
    """Render star rating as HTML."""
    filled = "★" * rating
    empty = "☆" * (5 - rating)
    return f"{filled}{empty}"


class AppFeedbackChoiceMapping:
    """Map choice keys to labels for display."""

    GOING_WELL_MAP = dict(AppFeedback.GOING_WELL_CHOICES)
    NEEDS_IMPROVEMENT_MAP = dict(AppFeedback.NEEDS_IMPROVEMENT_CHOICES)


class CycleFeedbackChoiceMapping:
    """Map choice keys to labels for display."""

    ENJOYED_MAP = dict(CycleFeedback.ENJOYED_CHOICES)
    NEEDS_IMPROVEMENT_MAP = dict(CycleFeedback.NEEDS_IMPROVEMENT_CHOICES)


@admin.register(AppFeedback)
class AppFeedbackAdmin(AdminPaginationMixin, ModelAdmin):
    admin_section = 'portal'
    list_display = [
        'created_at', 'parent_name', 'rating_stars',
        'going_well_tags', 'needs_improvement_tags', 'short_comments'
    ]
    list_filter = ['rating', 'created_at']
    search_fields = ['parent__user__email', 'parent__user__first_name', 'comments']
    readonly_fields = [
        'parent', 'rating', 'going_well', 'needs_improvement',
        'comments', 'created_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('parent', 'rating', 'created_at')
        }),
        ('Feedback', {
            'fields': ('going_well', 'needs_improvement', 'comments')
        }),
    )

    def parent_name(self, obj):
        if obj.parent:
            return obj.parent.user.get_full_name() or obj.parent.user.email
        return "—"
    parent_name.short_description = 'Parent'
    parent_name.admin_order_field = 'parent__user__first_name'

    def rating_stars(self, obj):
        return format_html(render_stars(obj.rating))
    rating_stars.short_description = 'Rating'
    rating_stars.admin_order_field = 'rating'

    def going_well_tags(self, obj):
        if not obj.going_well:
            return "—"
        labels = [
            AppFeedbackChoiceMapping.GOING_WELL_MAP.get(k, k)
            for k in obj.going_well
        ]
        return ", ".join(labels)
    going_well_tags.short_description = 'What\'s Working'

    def needs_improvement_tags(self, obj):
        if not obj.needs_improvement:
            return "—"
        labels = [
            AppFeedbackChoiceMapping.NEEDS_IMPROVEMENT_MAP.get(k, k)
            for k in obj.needs_improvement
        ]
        return ", ".join(labels)
    needs_improvement_tags.short_description = 'Needs Improvement'

    def short_comments(self, obj):
        if not obj.comments:
            return "—"
        return obj.comments[:80] + "..." if len(obj.comments) > 80 else obj.comments
    short_comments.short_description = 'Comments'
    short_comments.admin_order_field = 'comments'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        stats = AppFeedback.objects.aggregate(avg_rating=Avg('rating'))
        extra_context['stats'] = {
            'avg_rating': round(stats.get('avg_rating') or 0, 2),
            'total_count': AppFeedback.objects.count(),
            'low_rating_count': AppFeedback.objects.filter(rating__lte=2).count(),
        }
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(CycleFeedback)
class CycleFeedbackAdmin(AdminPaginationMixin, ModelAdmin):
    admin_section = 'portal'
    list_display = [
        'created_at', 'child_name', 'parent_email', 'rating_stars',
        'enjoyed_tags', 'needs_improvement_tags', 'short_comments'
    ]
    list_filter = ['rating', 'created_at', ('child__grade', ChoicesFieldListFilter)]
    search_fields = ['child__name', 'parent__user__email', 'comments']
    readonly_fields = [
        'cycle', 'parent', 'child', 'rating', 'enjoyed',
        'needs_improvement', 'comments', 'created_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('cycle', 'parent', 'child', 'rating', 'created_at')
        }),
        ('Feedback', {
            'fields': ('enjoyed', 'needs_improvement', 'comments')
        }),
    )

    def child_name(self, obj):
        return obj.child.name if obj.child else "—"
    child_name.short_description = 'Child'
    child_name.admin_order_field = 'child__name'

    def parent_email(self, obj):
        if obj.parent:
            return obj.parent.user.email
        return "—"
    parent_email.short_description = 'Parent Email'

    def rating_stars(self, obj):
        return format_html(render_stars(obj.rating))
    rating_stars.short_description = 'Rating'
    rating_stars.admin_order_field = 'rating'

    def enjoyed_tags(self, obj):
        if not obj.enjoyed:
            return "—"
        labels = [
            CycleFeedbackChoiceMapping.ENJOYED_MAP.get(k, k)
            for k in obj.enjoyed
        ]
        return ", ".join(labels)
    enjoyed_tags.short_description = 'Enjoyed'

    def needs_improvement_tags(self, obj):
        if not obj.needs_improvement:
            return "—"
        labels = [
            CycleFeedbackChoiceMapping.NEEDS_IMPROVEMENT_MAP.get(k, k)
            for k in obj.needs_improvement
        ]
        return ", ".join(labels)
    needs_improvement_tags.short_description = 'Needs Improvement'

    def short_comments(self, obj):
        if not obj.comments:
            return "—"
        return obj.comments[:80] + "..." if len(obj.comments) > 80 else obj.comments
    short_comments.short_description = 'Comments'
    short_comments.admin_order_field = 'comments'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        stats = CycleFeedback.objects.aggregate(
            avg_rating=Avg('rating')
        )
        extra_context['stats'] = {
            'avg_rating': round(stats.get('avg_rating') or 0, 2),
            'total_count': CycleFeedback.objects.count(),
            'low_rating_count': CycleFeedback.objects.filter(rating__lte=2).count(),
        }
        return super().changelist_view(request, extra_context=extra_context)
