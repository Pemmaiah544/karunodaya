"""
Tests for Community Progress API Views
"""

import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.profiles.models import ParentProfile, Child, ReadingAssessment
from apps.portal.models import CommunityProgress


class CommunityProgressAPITestCase(TestCase):
    """Test community progress API endpoints"""

    def setUp(self):
        """Set up test data and client"""
        self.client = Client()

        # Create user and parent profile with completed address (city + pincode)
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.parent = ParentProfile.objects.create(
            user=self.user,
            phone_number='9876543210',
            city='Bangalore',
            state='Karnataka',
            pincode='560066',
        )

        # Create child
        self.child = Child.objects.create(
            parent=self.parent,
            name='Test Child',
            age=8,
        )

    def test_api_address_status_unauthenticated(self):
        """Unauthenticated request should redirect to login"""
        response = self.client.get(reverse('portal:api_address_status'))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_api_address_status_authenticated(self):
        """Authenticated request should return address status"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('portal:api_address_status'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data['is_completed'])
        self.assertEqual(data['city'], 'Bangalore')
        self.assertEqual(data['pincode'], '560066')

    def test_api_user_address_post_valid(self):
        """Valid POST should save address"""
        self.client.login(username='testuser', password='testpass123')

        new_parent = ParentProfile.objects.create(
            user=User.objects.create_user(username='newuser', password='newpass'),
            phone_number='9876543211',
        )

        self.client.login(username='newuser', password='newpass')

        response = self.client.post(reverse('portal:api_user_address'), {
            'address': '456 Main Street',
            'city': 'Mumbai',
            'locality': 'Fort',
            'state': 'Maharashtra',
            'pincode': '400001',
        })

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # Verify city saved in DB
        new_parent.refresh_from_db()
        self.assertEqual(new_parent.city, 'Mumbai')

    def test_api_user_address_post_invalid_pincode(self):
        """Invalid PIN code should return 400"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(reverse('portal:api_user_address'), {
            'address': '456 Main Street',
            'city': 'Mumbai',
            'locality': 'Fort',
            'state': 'Maharashtra',
            'pincode': '4000',  # Invalid: only 4 digits
        })

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('pincode', data['errors'])

    def test_api_user_address_post_missing_field(self):
        """Missing required field should return 400"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(reverse('portal:api_user_address'), {
            'address': '456 Main Street',
            'city': 'Mumbai',
            # Missing locality
            'state': 'Maharashtra',
            'pincode': '400001',
        })

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('locality', data['errors'])

    def test_api_community_progress_without_address(self):
        """No address should return 400"""
        # Create user without city/pincode (incomplete address)
        user2 = User.objects.create_user(username='noaddress', password='pass123')
        ParentProfile.objects.create(
            user=user2,
            phone_number='9876543212',
        )

        self.client.login(username='noaddress', password='pass123')
        response = self.client.get(reverse('portal:api_community_progress'))

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_api_community_progress_empty_location(self):
        """Location with no data should return empty state"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('portal:api_community_progress'),
            {'city': 'UnknownCity', 'locality': 'UnknownLocality'}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['summary']['total_children'], 0)
        self.assertIn('error', data)

    def test_api_community_progress_with_data(self):
        """Should return aggregated community data"""
        # Create assessment
        ReadingAssessment.objects.create(
            child=self.child,
            wpm=80,
            accuracy=85.5,
            level='BEGINNER',
        )

        # Update community progress
        from services.community_service import CommunityProgressService
        CommunityProgressService.update_community_progress_for_location(
            'Bangalore', 'Whitefield'
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('portal:api_community_progress'),
            {'city': 'Bangalore', 'locality': 'Whitefield'}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertGreater(data['summary']['total_children'], 0)
        self.assertIsNotNone(data['summary']['avg_wpm'])
        self.assertIn('BEGINNER', data['level_distribution'])

    def test_address_banner_check_completed(self):
        """Completed address (city + pincode set) should return empty"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('portal:address_banner_check'))

        self.assertEqual(response.status_code, 200)
        # Should be empty because address is completed
        self.assertEqual(response.content.strip(), b'')

    def test_address_banner_check_incomplete(self):
        """Incomplete address (no city/pincode) should return banner"""
        user2 = User.objects.create_user(username='noaddress', password='pass123')
        ParentProfile.objects.create(
            user=user2,
            phone_number='9876543212',
        )

        self.client.login(username='noaddress', password='pass123')
        response = self.client.get(reverse('portal:address_banner_check'))

        self.assertEqual(response.status_code, 200)
        # Should contain banner HTML
        self.assertIn(b'Connect with Your Community', response.content)

    def test_community_progress_page_without_address(self):
        """Community progress page without address should redirect"""
        user2 = User.objects.create_user(username='noaddress', password='pass123')
        ParentProfile.objects.create(
            user=user2,
            phone_number='9876543212',
        )

        self.client.login(username='noaddress', password='pass123')
        response = self.client.get(reverse('portal:community_progress_page'))

        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)

    def test_community_progress_page_with_address(self):
        """Community progress page with address should load"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('portal:community_progress_page'))

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Kids Reading Spotlight', response.content)

    def test_api_user_address_get_not_allowed(self):
        """GET request to address save endpoint should fail"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('portal:api_user_address'))

        self.assertEqual(response.status_code, 405)  # Method not allowed
