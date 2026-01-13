"""
Management command to seed sample data for development and testing.

Usage:
    python manage.py seed_data

Creates:
- Sample publishers
- Sample books with various difficulty levels and grades
- Physical copies for subscription books
- Subscription plans
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.catalog.models import Publisher, Book
from apps.inventory.models import PhysicalCopy
from apps.orders.models import SubscriptionPlan
from apps.profiles.models import ParentProfile, Child
from datetime import date, timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed sample data for development'

    def handle(self, *args, **options):
        self.stdout.write('Seeding sample data...\n')

        # Clear existing data (optional - comment out if you want to keep existing data)
        # Book.objects.all().delete()
        # Publisher.objects.all().delete()
        # SubscriptionPlan.objects.all().delete()

        # Create Publishers
        self.stdout.write('Creating publishers...')
        publishers = []
        publisher_data = [
            {'name': 'Penguin Books India', 'email': 'contact@penguin.in', 'phone': '9876543210', 'address': 'Mumbai, Maharashtra'},
            {'name': 'Scholastic India', 'email': 'info@scholastic.in', 'phone': '9876543211', 'address': 'New Delhi'},
            {'name': 'Tulika Publishers', 'email': 'hello@tulikabooks.com', 'phone': '9876543212', 'address': 'Chennai, Tamil Nadu'},
        ]

        for data in publisher_data:
            publisher, created = Publisher.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            publishers.append(publisher)
            if created:
                self.stdout.write(f'  ✓ Created: {publisher.name}')

        # Create Subscription Plans
        self.stdout.write('\nCreating subscription plans...')
        plans_data = [
            {
                'name': 'Little Readers',
                'books_per_month': 3,
                'price_per_month': Decimal('499.00'),
                'age_group_min': 3,
                'age_group_max': 6,
                'description': 'Perfect for preschool and early readers'
            },
            {
                'name': 'Young Explorers',
                'books_per_month': 4,
                'price_per_month': Decimal('699.00'),
                'age_group_min': 7,
                'age_group_max': 10,
                'description': 'Engaging stories for growing readers'
            },
            {
                'name': 'Teen Scholars',
                'books_per_month': 5,
                'price_per_month': Decimal('899.00'),
                'age_group_min': 11,
                'age_group_max': 14,
                'description': 'Advanced reading for young adults'
            },
        ]

        for data in plans_data:
            plan, created = SubscriptionPlan.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if created:
                self.stdout.write(f'  ✓ Created: {plan.name}')

        # Create Books
        self.stdout.write('\nCreating books...')
        books_data = [
            # BEGINNER (Ages 3-6)
            {
                'title': 'The Very Hungry Caterpillar',
                'author': 'Eric Carle',
                'publisher': publishers[0],
                'isbn': '9780141332208',
                'mrp': Decimal('350.00'),
                'description': 'A classic picture book about a caterpillar eating through various foods.',
                'difficulty_rating': 'BEGINNER',
                'recommended_grade_min': 'PRE_K',
                'recommended_grade_max': 'GRADE_1',
                'is_subscription_eligible': True,
                'is_purchase_eligible': True,
                'stock_count': 10
            },
            {
                'title': 'Brown Bear, Brown Bear',
                'author': 'Bill Martin Jr.',
                'publisher': publishers[1],
                'isbn': '9780141501598',
                'mrp': Decimal('299.00'),
                'description': 'A rhythmic book about animals and colors.',
                'difficulty_rating': 'BEGINNER',
                'recommended_grade_min': 'PRE_K',
                'recommended_grade_max': 'KINDERGARTEN',
                'is_subscription_eligible': True,
                'is_purchase_eligible': True,
                'stock_count': 8
            },
            {
                'title': 'Where is the Green Sheep?',
                'author': 'Mem Fox',
                'publisher': publishers[2],
                'isbn': '9780670894314',
                'mrp': Decimal('325.00'),
                'description': 'A delightful book about finding the green sheep.',
                'difficulty_rating': 'BEGINNER',
                'recommended_grade_min': 'KINDERGARTEN',
                'recommended_grade_max': 'GRADE_1',
                'is_subscription_eligible': True,
                'is_purchase_eligible': True,
                'stock_count': 12
            },
            # INTERMEDIATE (Ages 7-10)
            {
                'title': 'Charlotte\'s Web',
                'author': 'E.B. White',
                'publisher': publishers[0],
                'isbn': '9780064400558',
                'mrp': Decimal('450.00'),
                'description': 'The story of a pig named Wilbur and his friendship with Charlotte the spider.',
                'difficulty_rating': 'INTERMEDIATE',
                'recommended_grade_min': 'GRADE_2',
                'recommended_grade_max': 'GRADE_5',
                'is_subscription_eligible': True,
                'is_purchase_eligible': True,
                'stock_count': 15
            },
            {
                'title': 'The Magic Faraway Tree',
                'author': 'Enid Blyton',
                'publisher': publishers[1],
                'isbn': '9781405284264',
                'mrp': Decimal('399.00'),
                'description': 'Adventures in a magical tree with different lands at the top.',
                'difficulty_rating': 'INTERMEDIATE',
                'recommended_grade_min': 'GRADE_3',
                'recommended_grade_max': 'GRADE_5',
                'is_subscription_eligible': True,
                'is_purchase_eligible': True,
                'stock_count': 10
            },
            {
                'title': 'Diary of a Wimpy Kid',
                'author': 'Jeff Kinney',
                'publisher': publishers[2],
                'isbn': '9781419741852',
                'mrp': Decimal('495.00'),
                'description': 'The humorous journal of middle schooler Greg Heffley.',
                'difficulty_rating': 'INTERMEDIATE',
                'recommended_grade_min': 'GRADE_3',
                'recommended_grade_max': 'GRADE_5',
                'is_subscription_eligible': True,
                'is_purchase_eligible': True,
                'stock_count': 20
            },
            # ADVANCED (Ages 11-14)
            {
                'title': 'Harry Potter and the Philosopher\'s Stone',
                'author': 'J.K. Rowling',
                'publisher': publishers[0],
                'isbn': '9781408855652',
                'mrp': Decimal('599.00'),
                'description': 'The beginning of Harry Potter\'s magical journey at Hogwarts.',
                'difficulty_rating': 'ADVANCED',
                'recommended_grade_min': 'GRADE_6',
                'recommended_grade_max': 'GRADE_8',
                'is_subscription_eligible': True,
                'is_purchase_eligible': True,
                'stock_count': 25
            },
            {
                'title': 'The Hunger Games',
                'author': 'Suzanne Collins',
                'publisher': publishers[1],
                'isbn': '9781407132082',
                'mrp': Decimal('550.00'),
                'description': 'A dystopian novel about survival and rebellion.',
                'difficulty_rating': 'ADVANCED',
                'recommended_grade_min': 'GRADE_7',
                'recommended_grade_max': 'GRADE_8',
                'is_subscription_eligible': True,
                'is_purchase_eligible': True,
                'stock_count': 18
            },
            {
                'title': 'Percy Jackson and the Lightning Thief',
                'author': 'Rick Riordan',
                'publisher': publishers[2],
                'isbn': '9780141346809',
                'mrp': Decimal('475.00'),
                'description': 'A modern take on Greek mythology with young demigods.',
                'difficulty_rating': 'ADVANCED',
                'recommended_grade_min': 'GRADE_6',
                'recommended_grade_max': 'GRADE_8',
                'is_subscription_eligible': True,
                'is_purchase_eligible': True,
                'stock_count': 16
            },
        ]

        created_books = 0
        for data in books_data:
            book, created = Book.objects.get_or_create(
                isbn=data['isbn'],
                defaults=data
            )
            if created:
                created_books += 1
                self.stdout.write(f'  ✓ Created: {book.title}')

                # Create physical copies for subscription-eligible books
                if book.is_subscription_eligible:
                    copies_to_create = 5  # Create 5 physical copies per book
                    for i in range(1, copies_to_create + 1):
                        barcode = f"{book.isbn}-{i:03d}"
                        PhysicalCopy.objects.get_or_create(
                            barcode=barcode,
                            defaults={
                                'book': book,
                                'status': 'AVAILABLE',
                                'purchased_date': date.today() - timedelta(days=30)
                            }
                        )
                    self.stdout.write(f'    → Created {copies_to_create} physical copies')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Seed complete!'
            f'\n   Publishers: {Publisher.objects.count()}'
            f'\n   Books: {Book.objects.count()}'
            f'\n   Physical Copies: {PhysicalCopy.objects.count()}'
            f'\n   Subscription Plans: {SubscriptionPlan.objects.count()}'
        ))
