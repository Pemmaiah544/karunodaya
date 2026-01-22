from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import ParentProfile, Child


class ChildInline(TabularInline):
    model = Child
    extra = 0
    fields = ('name', 'age', 'grade', 'reading_difficulty_level', 'date_of_birth')
    readonly_fields = []


@admin.register(ParentProfile)
class ParentProfileAdmin(ModelAdmin):
    list_display = ('user', 'phone_number', 'city', 'children_count', 'created_at')
    list_filter = ('city', 'state', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number', 'city')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ChildInline]

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
