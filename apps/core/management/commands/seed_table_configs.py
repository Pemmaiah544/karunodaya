from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.core.models import TableConfiguration, TableColumn, TableFilter, TableAction


class Command(BaseCommand):
    help = 'Seed table configurations for the admin interface'
    
    def handle(self, *args, **options):
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        # Create Books table configuration
        books_config, created = TableConfiguration.objects.get_or_create(
            name='Books Management',
            defaults={
                'slug': 'books-management',
                'description': 'Comprehensive books table for admin management',
                'model_name': 'catalog.Book',
                'items_per_page': 15,
                'enable_search': True,
                'enable_sorting': True,
                'enable_pagination': True,
                'mobile_card_view': True,
                'header_style': 'gradient',
                'row_striping': True,
                'hover_effects': True,
                'compact_mode': False,
                'created_by': admin_user,
            }
        )
        
        if created:
            # Add columns for books table
            columns_data = [
                {'field': 'title', 'display': 'Title', 'type': 'text', 'order': 1, 'width': '200px'},
                {'field': 'author', 'display': 'Author', 'type': 'text', 'order': 2, 'width': '150px'},
                {'field': 'publisher.name', 'display': 'Publisher', 'type': 'text', 'order': 3, 'width': '120px'},
                {'field': 'mrp', 'display': 'Price', 'type': 'currency', 'order': 4, 'width': '100px', 'align': 'right'},
                {'field': 'stock_count', 'display': 'Stock', 'type': 'number', 'order': 5, 'width': '80px', 'align': 'center'},
                {'field': 'is_active', 'display': 'Active', 'type': 'boolean', 'order': 6, 'width': '80px', 'align': 'center'},
                {'field': 'created_at', 'display': 'Created', 'type': 'datetime', 'order': 7, 'width': '150px'},
            ]
            
            for col_data in columns_data:
                TableColumn.objects.create(
                    table_config=books_config,
                    field_name=col_data['field'],
                    display_name=col_data['display'],
                    column_type=col_data['type'],
                    order=col_data['order'],
                    width=col_data.get('width', ''),
                    text_align=col_data.get('align', 'left'),
                    sortable=True,
                    searchable=True,
                )
            
            # Add filters for books table
            filters_data = [
                {'field': 'title', 'label': 'Search Books', 'type': 'text', 'placeholder': 'Search by title...'},
                {'field': 'publisher', 'label': 'Publisher', 'type': 'select'},
                {'field': 'is_active', 'label': 'Status', 'type': 'boolean'},
                {'field': 'difficulty_rating', 'label': 'Difficulty', 'type': 'select'},
            ]
            
            for filter_data in filters_data:
                TableFilter.objects.create(
                    table_config=books_config,
                    field_name=filter_data['field'],
                    filter_type=filter_data['type'],
                    label=filter_data['label'],
                    placeholder=filter_data.get('placeholder', ''),
                    order=len(TableFilter.objects.filter(table_config=books_config)) + 1,
                )
            
            # Add actions for books table
            actions_data = [
                {'name': 'view', 'label': 'View', 'type': 'view', 'url': '/admin/catalog/book/{id}/change/', 'button': 'info', 'icon': 'fas fa-eye'},
                {'name': 'edit', 'label': 'Edit', 'type': 'edit', 'url': '/admin/catalog/book/{id}/change/', 'button': 'primary', 'icon': 'fas fa-edit'},
                {'name': 'delete', 'label': 'Delete', 'type': 'delete', 'url': '/admin/catalog/book/{id}/delete/', 'button': 'danger', 'icon': 'fas fa-trash'},
            ]
            
            for action_data in actions_data:
                TableAction.objects.create(
                    table_config=books_config,
                    name=action_data['name'],
                    label=action_data['label'],
                    action_type=action_data['type'],
                    url_pattern=action_data['url'],
                    button_class=action_data['button'],
                    icon=action_data['icon'],
                    order=len(TableAction.objects.filter(table_config=books_config)) + 1,
                )
        
        # Create Users table configuration
        users_config, created = TableConfiguration.objects.get_or_create(
            name='Users Management',
            defaults={
                'slug': 'users-management',
                'description': 'User management table',
                'model_name': 'auth.User',
                'items_per_page': 20,
                'enable_search': True,
                'enable_sorting': True,
                'enable_pagination': True,
                'mobile_card_view': False,
                'header_style': 'solid',
                'row_striping': True,
                'hover_effects': True,
                'compact_mode': True,
                'created_by': admin_user,
            }
        )
        
        if created:
            # Add columns for users table
            columns_data = [
                {'field': 'username', 'display': 'Username', 'type': 'text', 'order': 1, 'width': '150px'},
                {'field': 'email', 'display': 'Email', 'type': 'email', 'order': 2, 'width': '200px'},
                {'field': 'first_name', 'display': 'First Name', 'type': 'text', 'order': 3, 'width': '120px'},
                {'field': 'last_name', 'display': 'Last Name', 'type': 'text', 'order': 4, 'width': '120px'},
                {'field': 'is_staff', 'display': 'Staff', 'type': 'boolean', 'order': 5, 'width': '80px', 'align': 'center'},
                {'field': 'is_active', 'display': 'Active', 'type': 'boolean', 'order': 6, 'width': '80px', 'align': 'center'},
                {'field': 'date_joined', 'display': 'Joined', 'type': 'datetime', 'order': 7, 'width': '150px'},
            ]
            
            for col_data in columns_data:
                TableColumn.objects.create(
                    table_config=users_config,
                    field_name=col_data['field'],
                    display_name=col_data['display'],
                    column_type=col_data['type'],
                    order=col_data['order'],
                    width=col_data.get('width', ''),
                    text_align=col_data.get('align', 'left'),
                    sortable=True,
                    searchable=True,
                )
        
        # Create Publishers table configuration
        publishers_config, created = TableConfiguration.objects.get_or_create(
            name='Publishers Management',
            defaults={
                'slug': 'publishers-management',
                'description': 'Publishers management table',
                'model_name': 'catalog.Publisher',
                'items_per_page': 25,
                'enable_search': True,
                'enable_sorting': True,
                'enable_pagination': True,
                'mobile_card_view': True,
                'header_style': 'minimal',
                'row_striping': False,
                'hover_effects': True,
                'compact_mode': False,
                'created_by': admin_user,
            }
        )
        
        if created:
            # Add columns for publishers table
            columns_data = [
                {'field': 'name', 'display': 'Name', 'type': 'text', 'order': 1, 'width': '200px'},
                {'field': 'email', 'display': 'Email', 'type': 'email', 'order': 2, 'width': '200px'},
                {'field': 'phone', 'display': 'Phone', 'type': 'text', 'order': 3, 'width': '150px'},
                {'field': 'created_at', 'display': 'Created', 'type': 'datetime', 'order': 4, 'width': '150px'},
            ]
            
            for col_data in columns_data:
                TableColumn.objects.create(
                    table_config=publishers_config,
                    field_name=col_data['field'],
                    display_name=col_data['display'],
                    column_type=col_data['type'],
                    order=col_data['order'],
                    width=col_data.get('width', ''),
                    sortable=True,
                    searchable=True,
                )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded table configurations!')
        )
        
        # Display created configurations
        configs = TableConfiguration.objects.all()
        for config in configs:
            self.stdout.write(f"- {config.name}: {config.columns.count()} columns, {config.filters.count()} filters")
