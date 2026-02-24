from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from unfold.admin import ModelAdmin, TabularInline
from apps.core.admin_mixins import AdminPaginationMixin
from .models import ParentProfile, Child, ChildProfileExtra, ParentProfileExtra, ReadingAssessment


# Custom User Admin to override the default Django User admin
admin.site.unregister(User)

class MyUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'unfold-input border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-primary-500',
                'style': 'visibility: visible !important; width: 300px !important;'
            })

@admin.register(User)
class UserAdmin(AdminPaginationMixin, DefaultUserAdmin, ModelAdmin):
    add_form = MyUserCreationForm
    add_form_template = 'admin/auth/user/add_form.html'
    
    list_display = ('first_name_link', 'last_name', 'get_phone_number', 'email', 'is_active')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'groups', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'parent_profile__phone_number')
    ordering = ('username',)
    
    def first_name_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:auth_user_change', args=[obj.pk])
        display_name = obj.first_name if obj.first_name else obj.username
        return format_html(
            '<a href="{}" style="color: #000000 !important; font-weight: 400; font-size: 13px;">{}</a>',
            url,
            display_name
        )
    first_name_link.short_description = 'First Name'
    first_name_link.admin_order_field = 'first_name'

    def get_phone_number(self, obj):
        try:
            return obj.parent_profile.phone_number
        except ParentProfile.DoesNotExist:
            return 'N/A'
    get_phone_number.short_description = 'Phone Number'
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )




class ChildInline(TabularInline):
    model = Child
    extra = 0
    fields = ('name', 'age', 'grade', 'reading_difficulty_level', 'date_of_birth')
    readonly_fields = []


class ParentProfileExtraInline(TabularInline):
    model = ParentProfileExtra
    extra = 0
    max_num = 1
    can_delete = False
    verbose_name = "Reading Support Info"
    verbose_name_plural = "Reading Support Info"
    fields = (
        'reading_frequency', 'provides_assistance', 'books_at_home',
        'preferred_reading_time', 'reading_duration_minutes', 'profile_completed'
    )


class ChildProfileExtraInline(TabularInline):
    model = ChildProfileExtra
    extra = 0
    max_num = 1
    can_delete = False
    verbose_name = "Extended Profile"
    verbose_name_plural = "Extended Profile"
    fields = (
        'medium', 'primary_language', 'other_languages', 'comprehension_level',
        'reads_aloud', 'skips_words', 'reading_speed_perception', 'avg_screen_time_hours'
    )


class ReadingAssessmentInline(TabularInline):
    model = ReadingAssessment
    extra = 0
    can_delete = False
    verbose_name = "Assessment History"
    verbose_name_plural = "Assessment History"
    readonly_fields = ('assessed_at', 'wpm', 'accuracy', 'level', 'language', 'strengths', 'gaps')
    fields = ('assessed_at', 'wpm', 'accuracy', 'level', 'language', 'strengths', 'gaps')
    ordering = ('-assessed_at',)


@admin.register(ParentProfile)
class ParentProfileAdmin(AdminPaginationMixin, ModelAdmin):
    list_display = ('first_name_link', 'user__last_name', 'phone_number', 'user__email', 'is_staff_status', 'city', 'created_at')
    list_filter = ('city', 'state', 'created_at', 'user__is_staff')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ChildInline, ParentProfileExtraInline]
    
    def first_name_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:profiles_parentprofile_change', args=[obj.pk])
        display_name = obj.user.first_name if obj.user.first_name else obj.user.username
        return format_html(
            '<a href="{}" style="color: #4b5563 !important; font-weight: 600; font-size: 14px;">{}</a>',
            url,
            display_name
        )
    first_name_link.short_description = 'User First Name'
    first_name_link.admin_order_field = 'user__first_name'

    def is_staff_status(self, obj):
        return obj.user.is_staff
    is_staff_status.boolean = True
    is_staff_status.short_description = 'Staff Status'

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Contact Details', {
            'fields': ('phone_number', 'address', 'city', 'state', 'pincode')
        }),
        ('Plan Preference', {
            'fields': ('plan_preference',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Child)
class ChildAdmin(AdminPaginationMixin, ModelAdmin):
    list_display = ('name_link', 'parent', 'age', 'grade', 'reading_difficulty_level', 'created_at')
    list_filter = ('grade', 'reading_difficulty_level', 'age')
    search_fields = ('name', 'parent__user__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ChildProfileExtraInline, ReadingAssessmentInline]

    def name_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:profiles_child_change', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color: #4b5563 !important; font-weight: 600; font-size: 14px;">{}</a>',
            url,
            obj.name
        )
    name_link.short_description = 'Name'
    name_link.admin_order_field = 'name'

    fieldsets = (
        ('Basic Information', {
            'fields': ('parent', 'name', 'date_of_birth', 'age')
        }),
        ('Education Details', {
            'fields': ('grade', 'reading_difficulty_level')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReadingAssessment)
class ReadingAssessmentAdmin(AdminPaginationMixin, ModelAdmin):
    list_display = ('child_name_link', 'wpm', 'accuracy', 'level', 'language', 'assessed_at')
    list_filter = ('level', 'language', 'assessed_at')
    search_fields = ('child__name', 'child__parent__user__username')
    readonly_fields = ('child', 'passage', 'wpm', 'accuracy', 'level', 'strengths', 'gaps', 'language', 'assessed_at')
    ordering = ('-assessed_at',)

    def child_name_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:profiles_child_change', args=[obj.child.pk])
        return format_html(
            '<a href="{}" style="color: #4b5563 !important; font-weight: 600; font-size: 14px;">{}</a>',
            url, obj.child.name
        )
    child_name_link.short_description = 'Child'
    child_name_link.admin_order_field = 'child__name'

    fieldsets = (
        ('Assessment Record', {
            'fields': ('child', 'passage', 'language', 'assessed_at')
        }),
        ('Results', {
            'fields': ('wpm', 'accuracy', 'level')
        }),
        ('Feedback', {
            'fields': ('strengths', 'gaps'),
            'classes': ('collapse',)
        }),
    )
