from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from apps.catalog.models import Book, Publisher
from apps.core.models import TableConfiguration
from django.db.models import Q


class TablePagination:
    """Helper class for pagination data"""
    def __init__(self, paginator, current_page, current_page_obj):
        self.total_pages = paginator.num_pages
        self.current_page = current_page
        self.total_items = paginator.count
        self.has_previous = current_page_obj.has_previous()
        self.has_next = current_page_obj.has_next()
        self.previous_page = current_page_obj.previous_page_number() if self.has_previous else None
        self.next_page = current_page_obj.next_page_number() if self.has_next else None
        self.start_index = current_page_obj.start_index()
        self.end_index = current_page_obj.end_index()
        
        # Create page range with smart pagination
        if self.total_pages <= 10:
            self.page_range = range(1, self.total_pages + 1)
        else:
            if current_page <= 5:
                self.page_range = range(1, 8) + range(self.total_pages - 1, self.total_pages + 1)
            elif current_page >= self.total_pages - 4:
                self.page_range = range(1, 3) + range(self.total_pages - 6, self.total_pages + 1)
            else:
                self.page_range = range(1, 3) + range(current_page - 2, current_page + 3) + range(self.total_pages - 1, self.total_pages + 1)


@staff_member_required
def enhanced_books_dashboard(request):
    """
    Enhanced dashboard using database-driven table configuration
    """
    # Get table configuration
    config = get_object_or_404(TableConfiguration, slug='books-management', is_active=True)
    
    # Get base queryset
    books = Book.objects.select_related('publisher').all()
    
    # Apply search
    search_query = request.GET.get('search', '')
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
        
        books = books.filter(search_q)
    
    # Apply filters
    current_filters = {}
    for filter_obj in config.filters.all():
        filter_value = request.GET.get(filter_obj.field_name, '')
        if filter_value:
            current_filters[filter_obj.field_name] = filter_value
            if filter_obj.filter_type == 'boolean':
                books = books.filter(**{filter_obj.field_name: filter_value.lower() == 'true'})
            else:
                books = books.filter(**{filter_obj.field_name: filter_value})
    
    # Apply sorting
    sort_field = request.GET.get('sort', 'title')
    if sort_field.startswith('-'):
        books = books.order_by(sort_field[1:])
    else:
        books = books.order_by(sort_field)
    
    # Pagination
    paginator = Paginator(books, config.items_per_page)
    page = request.GET.get('page', 1)
    
    try:
        books_page = paginator.page(page)
    except PageNotAnInteger:
        books_page = paginator.page(1)
    except EmptyPage:
        books_page = paginator.page(paginator.num_pages)
    
    # Create pagination object
    pagination = TablePagination(paginator, int(page), books_page)
    
    context = {
        'config': config,
        'data': books_page,
        'pagination': pagination,
        'search_query': search_query,
        'current_filters': current_filters,
        'user': request.user,
    }
    
    return render(request, 'admin/enhanced_books_dashboard.html', context)


@staff_member_required
def enhanced_users_dashboard(request):
    """
    Enhanced users dashboard using database configuration
    """
    config = get_object_or_404(TableConfiguration, slug='users-management', is_active=True)
    
    # Get users queryset
    users = User.objects.all()
    
    # Apply search
    search_query = request.GET.get('search', '')
    if search_query and config.enable_search:
        searchable_columns = config.columns.filter(searchable=True)
        search_q = Q()
        
        for column in searchable_columns:
            field_name = column.field_name
            search_q |= Q(**{f"{field_name}__icontains": search_query})
        
        users = users.filter(search_q)
    
    # Apply filters
    current_filters = {}
    for filter_obj in config.filters.all():
        filter_value = request.GET.get(filter_obj.field_name, '')
        if filter_value:
            current_filters[filter_obj.field_name] = filter_value
            if filter_obj.filter_type == 'boolean':
                users = users.filter(**{filter_obj.field_name: filter_value.lower() == 'true'})
            else:
                users = users.filter(**{filter_obj.field_name: filter_value})
    
    # Apply sorting
    sort_field = request.GET.get('sort', 'username')
    if sort_field.startswith('-'):
        users = users.order_by(sort_field[1:])
    else:
        users = users.order_by(sort_field)
    
    # Pagination
    paginator = Paginator(users, config.items_per_page)
    page = request.GET.get('page', 1)
    
    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)
    
    pagination = TablePagination(paginator, int(page), users_page)
    
    context = {
        'config': config,
        'data': users_page,
        'pagination': pagination,
        'search_query': search_query,
        'current_filters': current_filters,
        'user': request.user,
    }
    
    return render(request, 'admin/enhanced_users_dashboard.html', context)


@staff_member_required
def table_config_list(request):
    """
    List all table configurations
    """
    configs = TableConfiguration.objects.filter(is_active=True).order_by('name')
    
    context = {
        'configs': configs,
    }
    
    return render(request, 'admin/table_config_list.html', context)


@staff_member_required
def table_config_detail(request, slug):
    """
    Show table configuration details and preview
    """
    config = get_object_or_404(TableConfiguration, slug=slug, is_active=True)
    
    # Get sample data for preview
    try:
        model_parts = config.model_name.split('.')
        from django.apps import apps
        model = apps.get_model(model_parts[0], model_parts[1])
        sample_data = model.objects.all()[:5]
    except (LookupError, AttributeError):
        sample_data = []
    
    context = {
        'config': config,
        'sample_data': sample_data,
    }
    
    return render(request, 'admin/table_config_detail.html', context)


def books_dashboard(request):
    """
    Legacy dashboard view demonstrating the reusable table component
    """
    # Get books with publisher information
    books = Book.objects.select_related('publisher').all()
    
    # Apply search filter
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(publisher__name__icontains=search_query)
        )
    
    # Apply sorting
    sort_field = request.GET.get('sort', 'title')
    if sort_field.startswith('-'):
        books = books.order_by(sort_field[1:]).reverse()
    else:
        books = books.order_by(sort_field)
    
    # Pagination
    paginator = Paginator(books, 10)
    page = request.GET.get('page', 1)
    
    try:
        books_page = paginator.page(page)
    except PageNotAnInteger:
        books_page = paginator.page(1)
    except EmptyPage:
        books_page = paginator.page(paginator.num_pages)
    
    # Create pagination object
    pagination = TablePagination(paginator, int(page), books_page)
    
    # Define table columns for books
    book_columns = [
        {
            'title': 'Title',
            'field': 'title',
            'format': 'text',
            'sortable': True
        },
        {
            'title': 'Author',
            'field': 'author',
            'format': 'text',
            'sortable': True
        },
        {
            'title': 'Publisher',
            'field': 'publisher.name',
            'format': 'text',
            'sortable': True
        },
        {
            'title': 'Price',
            'field': 'mrp',
            'format': 'currency',
            'sortable': True
        },
        {
            'title': 'Stock',
            'field': 'stock_count',
            'format': 'text',
            'sortable': True
        },
        {
            'title': 'Status',
            'field': 'is_active',
            'format': 'boolean',
            'sortable': True
        }
    ]
    
    # Define table columns with actions
    book_action_columns = book_columns + [
        {
            'title': 'Actions',
            'template': '<a href="/admin/catalog/book/{{ row.id }}/change/" class="action-btn edit">Edit</a> '
                       '<a href="/admin/catalog/book/{{ row.id }}/delete/" class="action-btn delete">Delete</a>',
            'sortable': False
        }
    ]
    
    # Get users for second table example
    users = User.objects.all().order_by('-date_joined')
    user_paginator = Paginator(users, 5)
    user_page = request.GET.get('user_page', 1)
    
    try:
        users_page = user_paginator.page(user_page)
    except PageNotAnInteger:
        users_page = user_paginator.page(1)
    except EmptyPage:
        users_page = user_paginator.page(user_paginator.num_pages)
    
    user_pagination = TablePagination(user_paginator, int(user_page), users_page)
    
    # Define user table columns
    user_columns = [
        {
            'title': 'Username',
            'field': 'username',
            'format': 'text',
            'sortable': True
        },
        {
            'title': 'Email',
            'field': 'email',
            'format': 'text',
            'sortable': True
        },
        {
            'title': 'First Name',
            'field': 'first_name',
            'format': 'text',
            'sortable': True
        },
        {
            'title': 'Last Name',
            'field': 'last_name',
            'format': 'text',
            'sortable': True
        },
        {
            'title': 'Staff Status',
            'field': 'is_staff',
            'format': 'boolean',
            'sortable': True
        },
        {
            'title': 'Joined',
            'field': 'date_joined',
            'format': 'datetime',
            'sortable': True
        }
    ]
    
    context = {
        'books': books_page,
        'book_columns': book_columns,
        'book_action_columns': book_action_columns,
        'paginator': pagination,
        'users': users_page,
        'user_columns': user_columns,
        'user_paginator': user_pagination,
        'search_query': search_query,
    }
    
    return render(request, 'admin/books_dashboard.html', context)


def simple_table_example(request):
    """
    Simple example showing basic table usage
    """
    # Sample data structure
    sample_data = [
        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com', 'age': 30, 'active': True},
        {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com', 'age': 25, 'active': False},
        {'id': 3, 'name': 'Bob Johnson', 'email': 'bob@example.com', 'age': 35, 'active': True},
    ]
    
    columns = [
        {'title': 'Name', 'field': 'name', 'sortable': True},
        {'title': 'Email', 'field': 'email', 'sortable': True},
        {'title': 'Age', 'field': 'age', 'sortable': True},
        {'title': 'Active', 'field': 'active', 'format': 'boolean', 'sortable': True},
    ]
    
    return render(request, 'admin/simple_table.html', {
        'data': sample_data,
        'columns': columns,
    })
