from django import template
from django.utils.html import format_html
from django.template import Context, Template
from django.db.models import Q
import re

register = template.Library()


@register.simple_tag(takes_context=True)
def admin_querystring(context, **kwargs):
    request = context.get('request')
    if request is None:
        return ''

    query = request.GET.copy()
    for key, value in kwargs.items():
        if value is None or value == '':
            try:
                query.pop(key)
            except KeyError:
                pass
        else:
            query[key] = str(value)

    encoded = query.urlencode()
    return f"?{encoded}" if encoded else "?"


@register.simple_tag
def admin_pagination_info(cl):
    total = getattr(cl, 'result_count', 0) or 0
    # In Django 5.1+, ChangeList.page_num is 1-indexed.
    # We'll normalize it to 0-indexed for our calculation logic if needed,
    # or just use it directly if we adjust the formulas.
    page_num = getattr(cl, 'page_num', 1) 
    paginator = getattr(cl, 'paginator', None)
    pages = getattr(paginator, 'num_pages', 1) if paginator is not None else 1
    show_all = bool(getattr(cl, 'show_all', False))

    per_page = getattr(cl, 'list_per_page', 0) or 0
    if show_all:
        per_page = total if total else per_page

    if total <= 0:
        start = 0
        end = 0
    else:
        if per_page <= 0:
            start = 1
            end = total
        else:
            # page_num is 1-indexed, so Page 1: (1-1)*5 + 1 = 1
            start = (page_num - 1) * per_page + 1
            end = min(start + per_page - 1, total)

    has_prev = page_num > 1
    has_next = page_num < pages

    return {
        'total': total,
        'start': start,
        'end': end,
        'page': page_num,
        'pages': pages,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_p': page_num - 1,
        'next_p': page_num + 1,
    }

@register.filter
def get_attr(obj, attr_path):
    """
    Get attribute from object using dot notation (e.g., 'user.name.first')
    """
    attrs = attr_path.split('.')
    value = obj
    
    try:
        for attr in attrs:
            if hasattr(value, attr):
                value = getattr(value, attr)
            elif isinstance(value, dict) and attr in value:
                value = value[attr]
            else:
                return None
        return value
    except (AttributeError, KeyError, TypeError):
        return None

@register.filter
def multiply(value, arg):
    """Multiply two numbers"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def min_value(value, arg):
    """Return the minimum of two numbers"""
    try:
        return min(int(value), int(arg))
    except (ValueError, TypeError):
        return value

@register.filter
def add(value, arg):
    """Add two numbers"""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def selected_if(value, arg):
    """Returns 'selected' if value matches arg, else empty string."""
    if str(value) == str(arg):
        return 'selected'
    return ''

@register.filter
def active_if(value, arg):
    """Returns 'active' if value matches arg, else empty string."""
    if str(value) == str(arg):
        return 'active'
    return ''

@register.filter
def has_permission(user, permission):
    """Check if user has a specific permission"""
    if not permission:
        return True
    return user.has_perm(permission)

@register.simple_tag
def render_table_cell(row, column):
    """
    Render a table cell based on column configuration
    """
    field_name = column.field_name
    value = get_attr(row, field_name)
    
    if value is None:
        return format_html('<span class="text-muted">-</span>')
    
    column_type = column.column_type
    
    if column_type == 'currency':
        try:
            return format_html(
                '<span class="cell-currency">${}</span>',
                "{:,.2f}".format(float(value))
            )
        except (ValueError, TypeError):
            return str(value)
    
    elif column_type == 'date':
        try:
            return format_html(
                '<span class="cell-date">{}</span>',
                value.strftime('%Y-%m-%d')
            )
        except AttributeError:
            return str(value)
    
    elif column_type == 'datetime':
        try:
            return format_html(
                '<span class="cell-date">{}</span>',
                value.strftime('%Y-%m-%d %H:%M')
            )
        except AttributeError:
            return str(value)
    
    elif column_type == 'boolean':
        if value:
            return format_html('<span class="badge-true">✓ Yes</span>')
        else:
            return format_html('<span class="badge-false">✗ No</span>')
    
    elif column_type == 'email':
        return format_html('<a href="mailto:{}">{}</a>', value, value)
    
    elif column_type == 'url':
        return format_html('<a href="{}" target="_blank">{}</a>', value, value)
    
    elif column_type == 'image':
        if hasattr(value, 'url'):
            return format_html(
                '<div class="cell-image"><img src="{}" alt="Image"></div>',
                value.url
            )
        else:
            return format_html('<span class="text-muted">No image</span>')
    
    elif column_type == 'number':
        try:
            return format_html('{}'.format(int(value)))
        except (ValueError, TypeError):
            return str(value)
    
    else:  # text
        text_value = str(value)
        if column.truncate and column.max_length:
            if len(text_value) > column.max_length:
                text_value = text_value[:column.max_length] + '...'
        return text_value

@register.inclusion_tag('components/enhanced_table.html')
def enhanced_table(config, data, pagination=None, loading=False, empty_message=None, search_query='', current_filters=None):
    """
    Render an enhanced table component using database configuration
    
    Usage:
    {% enhanced_table 
        config=table_config 
        data=books 
        pagination=paginator 
        search_query=search_term
    %}
    """
    if current_filters is None:
        current_filters = {}
    
    return {
        'config': config,
        'data': data,
        'pagination': pagination,
        'loading': loading,
        'empty_message': empty_message,
        'search_query': search_query,
        'current_filters': current_filters,
        'user': None,  # Will be set in the template context
    }

@register.inclusion_tag('components/enhanced_table.html')
def render_table_from_slug(slug, data, pagination=None, **kwargs):
    """
    Render table using configuration slug
    
    Usage:
    {% render_table_from_slug 'books-management' books %}
    """
    from apps.core.models import TableConfiguration
    
    try:
        config = TableConfiguration.objects.get(slug=slug, is_active=True)
        return enhanced_table(config, data, pagination, **kwargs)
    except TableConfiguration.DoesNotExist:
        return {
            'config': None,
            'data': [],
            'error': f'Table configuration "{slug}" not found'
        }

@register.simple_tag
def get_table_data(config, search_query='', filters=None, page=1):
    """
    Get table data based on configuration
    """
    if filters is None:
        filters = {}
    
    # Import the model dynamically
    model_parts = config.model_name.split('.')
    app_label = model_parts[0]
    model_name = model_parts[1]
    
    try:
        from django.apps import apps
        model = apps.get_model(app_label, model_name)
        
        queryset = model.objects.all()
        
        # Apply search
        if search_query and config.enable_search:
            searchable_columns = config.columns.filter(searchable=True)
            search_q = Q()
            
            for column in searchable_columns:
                field_name = column.field_name
                if '.' in field_name:
                    # Handle related fields
                    related_parts = field_name.split('.')
                    search_q |= Q(**{f"{related_parts[0]}__{related_parts[1]}__icontains": search_query})
                else:
                    search_q |= Q(**{f"{field_name}__icontains": search_query})
            
            queryset = queryset.filter(search_q)
        
        # Apply filters
        for filter_obj in config.filters.all():
            filter_value = filters.get(filter_obj.field_name)
            if filter_value:
                if filter_obj.filter_type == 'boolean':
                    queryset = queryset.filter(**{filter_obj.field_name: filter_value.lower() == 'true'})
                else:
                    queryset = queryset.filter(**{filter_obj.field_name: filter_value})
        
        # Apply sorting
        sort_field = search_query.split('sort=')[-1] if 'sort=' in search_query else None
        if sort_field and sort_field != search_query:
            if sort_field.startswith('-'):
                queryset = queryset.order_by(sort_field[1:]).reverse()
            else:
                queryset = queryset.order_by(sort_field)
        
        return queryset
        
    except (LookupError, AttributeError):
        return None
