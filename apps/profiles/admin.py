from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import User
from unfold.admin import ModelAdmin, TabularInline
from .models import ParentProfile, Child


# Custom User Admin to override the default Django User admin
admin.site.unregister(User)
@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('get_phone_number', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'groups', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'parent_profile__phone_number')
    ordering = ('username',)
    
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


@admin.register(ParentProfile)
class ParentProfileAdmin(ModelAdmin):
    list_display = ('user', 'phone_number', 'user__email', 'user__first_name', 'user__last_name', 'is_staff_status', 'city', 'children_count', 'created_at')
    list_filter = ('city', 'state', 'created_at', 'user__is_staff')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ChildInline]

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
class ChildAdmin(ModelAdmin):
    list_display = ('name', 'parent', 'age', 'grade', 'reading_difficulty_level', 'created_at')
    list_filter = ('grade', 'reading_difficulty_level', 'age')
    search_fields = ('name', 'parent__user__username')
    readonly_fields = ('created_at', 'updated_at')

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
