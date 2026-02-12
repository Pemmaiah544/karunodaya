from django.core.management.base import BaseCommand
from django.core.files import File
from apps.catalog.models import Book
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Assign default cover images to books that dont have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--default-image',
            type=str,
            default='book_covers/bookcover.png',
            help='Path to default cover image relative to MEDIA_ROOT'
        )

    def handle(self, *args, **options):
        default_image_path = options['default_image']
        full_path = os.path.join(settings.MEDIA_ROOT, default_image_path)
        
        if not os.path.exists(full_path):
            self.stdout.write(
                self.style.ERROR(f'Default cover image not found: {full_path}')
            )
            return

        books_without_covers = Book.objects.filter(cover_image='')
        
        if not books_without_covers.exists():
            self.stdout.write(self.style.SUCCESS('All books already have cover images!'))
            return

        self.stdout.write(f'Found {books_without_covers.count()} books without cover images')
        
        updated_count = 0
        for book in books_without_covers:
            try:
                with open(full_path, 'rb') as f:
                    book.cover_image.save(
                        f'bookcover_{book.id}.png',
                        File(f),
                        save=True
                    )
                updated_count += 1
                self.stdout.write(f'  ✓ Added cover to: {book.title}')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed to add cover to {book.title}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully added cover images to {updated_count} books'
            )
        )
