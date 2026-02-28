"""
Tests for Community Progress Service Layer
"""

from django.test import TestCase
from django.contrib.auth.models import User
from apps.profiles.models import ParentProfile, Child, ReadingAssessment
from apps.portal.models import CommunityProgress
from services.community_service import AddressValidator, CommunityProgressService


class AddressValidatorTestCase(TestCase):
    """Test address validation logic"""

    def test_validate_valid_address(self):
        """Valid address should pass validation"""
        data = {
            'address': '123 Main Street, Apt 4B',
            'city': 'Bangalore',
            'locality': 'Whitefield',
            'state': 'Karnataka',
            'pincode': '560066',
        }
        is_valid, errors = AddressValidator.validate_address(data)
        self.assertTrue(is_valid)
        self.assertEqual(errors, {})

    def test_validate_missing_required_field(self):
        """Missing required field should fail"""
        data = {
            'address': '123 Main Street',
            'city': 'Bangalore',
            'locality': 'Whitefield',
            'state': 'Karnataka',
            'pincode': '',  # Missing
        }
        is_valid, errors = AddressValidator.validate_address(data)
        self.assertFalse(is_valid)
        self.assertIn('pincode', errors)

    def test_validate_invalid_pincode_format(self):
        """Invalid PIN code format should fail"""
        data = {
            'address': '123 Main Street',
            'city': 'Bangalore',
            'locality': 'Whitefield',
            'state': 'Karnataka',
            'pincode': '56006',  # Only 5 digits
        }
        is_valid, errors = AddressValidator.validate_address(data)
        self.assertFalse(is_valid)
        self.assertIn('pincode', errors)

    def test_validate_short_address(self):
        """Address less than 5 characters should fail"""
        data = {
            'address': '123',  # Too short
            'city': 'Bangalore',
            'locality': 'Whitefield',
            'state': 'Karnataka',
            'pincode': '560066',
        }
        is_valid, errors = AddressValidator.validate_address(data)
        self.assertFalse(is_valid)
        self.assertIn('address', errors)

    def test_normalize_address(self):
        """Address should be normalized (trimmed, capitalized)"""
        data = {
            'address': '  123 main street  ',
            'city': '  bangalore  ',
            'locality': '  whitefield  ',
            'state': '  karnataka  ',
            'pincode': '560066',
        }
        normalized = AddressValidator.normalize_address(data)

        self.assertEqual(normalized['address'], '123 main street')
        self.assertEqual(normalized['city'], 'Bangalore')
        self.assertEqual(normalized['locality'], 'Whitefield')
        self.assertEqual(normalized['state'], 'Karnataka')
        self.assertEqual(normalized['pincode'], '560066')


class CommunityProgressServiceTestCase(TestCase):
    """Test community progress service logic"""

    def setUp(self):
        """Set up test data"""
        # Create users and profiles
        self.user1 = User.objects.create_user(username='parent1', password='test123')
        self.parent1 = ParentProfile.objects.create(
            user=self.user1,
            phone_number='9876543210',
            city='Bangalore',
            pincode='560066',
        )

        self.user2 = User.objects.create_user(username='parent2', password='test123')
        self.parent2 = ParentProfile.objects.create(
            user=self.user2,
            phone_number='9876543211',
            city='Bangalore',
            pincode='560066',
        )

        # Create children
        self.child1 = Child.objects.create(
            parent=self.parent1,
            name='Child 1',
            age=8,
        )

        self.child2 = Child.objects.create(
            parent=self.parent2,
            name='Child 2',
            age=7,
        )

    def test_get_community_progress_no_data(self):
        """No data returns empty community progress"""
        progress = CommunityProgressService.get_community_progress(
            'Unknown City', 'Unknown Locality'
        )

        self.assertEqual(progress['summary']['total_children'], 0)
        self.assertIsNone(progress['summary']['avg_wpm'])
        self.assertIn('error', progress)

    def test_compute_improvement_percent_with_previous(self):
        """Improvement should be calculated correctly"""
        prev_assessment = ReadingAssessment.objects.create(
            child=self.child1,
            wpm=80,
            accuracy=85.5,
            level='BEGINNER',
        )

        curr_assessment = ReadingAssessment.objects.create(
            child=self.child1,
            wpm=100,
            accuracy=90.0,
            level='BEGINNER',
        )

        improvement = CommunityProgressService.compute_improvement_percent(
            curr_assessment, prev_assessment
        )

        # (100 - 80) / 80 * 100 = 25%
        self.assertAlmostEqual(improvement, 25.0, places=1)

    def test_compute_improvement_percent_no_previous(self):
        """No previous assessment should return None"""
        assessment = ReadingAssessment.objects.create(
            child=self.child1,
            wpm=80,
            accuracy=85.5,
            level='BEGINNER',
        )

        improvement = CommunityProgressService.compute_improvement_percent(assessment)
        self.assertIsNone(improvement)

    def test_get_city_suggestions(self):
        """Should return list of cities"""
        cities = CommunityProgressService.get_city_suggestions(10)
        self.assertIn('Bangalore', cities)

    def test_get_locality_suggestions(self):
        """Locality suggestions returns empty list (locality is form-only, not stored in profile)"""
        localities = CommunityProgressService.get_locality_suggestions('Bangalore', 10)
        self.assertEqual(localities, [])

    def test_update_community_progress_for_location(self):
        """Should create/update CommunityProgress records"""
        # Create assessments
        ReadingAssessment.objects.create(
            child=self.child1,
            wpm=80,
            accuracy=85.5,
            level='BEGINNER',
        )

        ReadingAssessment.objects.create(
            child=self.child2,
            wpm=90,
            accuracy=88.0,
            level='BEGINNER',
        )

        # Update community progress
        CommunityProgressService.update_community_progress_for_location(
            'Bangalore', 'Whitefield'
        )

        # Check that record was created
        progress = CommunityProgress.objects.filter(
            city='Bangalore',
            locality='Whitefield',
            reading_level='BEGINNER'
        ).first()

        self.assertIsNotNone(progress)
        self.assertEqual(progress.child_count, 2)
        self.assertAlmostEqual(progress.avg_wpm, 85.0, places=1)
        self.assertAlmostEqual(progress.avg_accuracy, 86.75, places=1)

    def test_update_community_progress_all_children_included(self):
        """All children with assessments in the city should be included"""
        ReadingAssessment.objects.create(
            child=self.child1,
            wpm=80,
            accuracy=85.5,
            level='BEGINNER',
        )

        ReadingAssessment.objects.create(
            child=self.child2,
            wpm=90,
            accuracy=88.0,
            level='BEGINNER',
        )

        CommunityProgressService.update_community_progress_for_location(
            'Bangalore', 'Whitefield'
        )

        progress = CommunityProgress.objects.filter(
            city='Bangalore',
            locality='Whitefield',
            reading_level='BEGINNER'
        ).first()

        self.assertIsNotNone(progress)
        self.assertEqual(progress.child_count, 2)
        self.assertAlmostEqual(progress.avg_wpm, 85.0, places=1)
