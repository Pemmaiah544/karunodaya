from django.core.management.base import BaseCommand
from apps.catalog.models import Book


class Command(BaseCommand):
    help = 'Check marketplace visibility of all books and fix common issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix visibility issues',
        )

    def handle(self, *args, **options):
        self.stdout.write('📚 Book Marketplace Visibility Check\n')
        
        all_books = Book.objects.all()
        visible_books = Book.objects.filter(
            is_purchase_eligible=True,
            is_active=True,
            stock_count__gt=0
        )
        invisible_books = all_books.exclude(
            is_purchase_eligible=True,
            is_active=True,
            stock_count__gt=0
        )

        self.stdout.write(f'Total books: {all_books.count()}')
        self.stdout.write(f'Visible in marketplace: {visible_books.count()}')
        self.stdout.write(f'Hidden from marketplace: {invisible_books.count()}\n')

        if invisible_books.exists():
            self.stdout.write('🔍 Books hidden from marketplace:')
            for book in invisible_books:
                reasons = []
                if not book.is_purchase_eligible:
                    reasons.append('Not purchase eligible')
                if not book.is_active:
                    reasons.append('Inactive')
                if book.stock_count <= 0:
                    reasons.append('No stock')
                
                self.stdout.write(f'  ❌ {book.title}')
                self.stdout.write(f'     Reasons: {", ".join(reasons)}')
                self.stdout.write(f'     Stock: {book.stock_count}, Active: {book.is_active}, Purchase: {book.is_purchase_eligible}\n')

            if options['fix']:
                self.stdout.write('🔧 Fixing visibility issues...')
                
                # Make books purchase eligible and active
                updated = invisible_books.update(
                    is_purchase_eligible=True,
                    is_active=True
                )
                
                # Add stock to books with zero stock
                zero_stock = Book.objects.filter(stock_count=0)
                zero_stock.update(stock_count=10)
                
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Fixed {updated} books. Added stock to {zero_stock.count()} books.'
                ))
                
                # Verify fix
                new_visible = Book.objects.filter(
                    is_purchase_eligible=True,
                    is_active=True,
                    stock_count__gt=0
                ).count()
                self.stdout.write(self.style.SUCCESS(
                    f'📊 Now {new_visible} books are visible in marketplace.'
                ))
        else:
            self.stdout.write(self.style.SUCCESS('✅ All books are visible in marketplace!'))
