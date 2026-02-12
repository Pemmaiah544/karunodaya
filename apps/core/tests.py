"""
Tests for custom validators.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.core.validators import StrictEmailValidator, validate_strict_email


class StrictEmailValidatorTest(TestCase):
    """Test cases for strict email validation."""
    
    def setUp(self):
        self.validator = StrictEmailValidator()
    
    def test_valid_emails(self):
        """Test that valid email addresses pass validation."""
        valid_emails = [
            'user@example.com',
            'test.user@example.com',
            'user_name@example.org',
            'user-name@example.co.in',
            'firstname.lastname@company.com',
            'email@subdomain.example.com',
            '123@example.com',
            'user123@test123.com',
            'a@example.co',
        ]
        
        for email in valid_emails:
            try:
                self.validator(email)
            except ValidationError:
                self.fail(f"Valid email '{email}' failed validation")
    
    def test_invalid_emails_no_at_symbol(self):
        """Test that emails without @ symbol fail validation."""
        invalid_emails = [
            'userexample.com',
            'user.example.com',
            'plaintext',
        ]
        
        for email in invalid_emails:
            with self.assertRaises(ValidationError):
                self.validator(email)
    
    def test_invalid_emails_no_domain(self):
        """Test that emails without proper domain fail validation."""
        invalid_emails = [
            'user@',
            'user@domain',
            'user@.com',
            '@example.com',
        ]
        
        for email in invalid_emails:
            with self.assertRaises(ValidationError):
                self.validator(email)
    
    def test_invalid_emails_no_tld(self):
        """Test that emails without TLD fail validation."""
        invalid_emails = [
            'user@domain.',
            'user@domain.c',  # TLD too short
        ]
        
        for email in invalid_emails:
            with self.assertRaises(ValidationError):
                self.validator(email)
    
    def test_invalid_emails_special_characters(self):
        """Test that emails with invalid special characters fail."""
        invalid_emails = [
            'user name@example.com',  # space in username
            'user@exam ple.com',  # space in domain
            'user..name@example.com',  # consecutive dots
            '.user@example.com',  # starts with dot
            'user.@example.com',  # ends with dot
        ]
        
        for email in invalid_emails:
            with self.assertRaises(ValidationError):
                self.validator(email)
    
    def test_empty_email(self):
        """Test that empty email fails validation."""
        with self.assertRaises(ValidationError):
            self.validator('')
    
    def test_validate_strict_email_function(self):
        """Test the standalone validation function."""
        # Valid email should not raise
        try:
            validate_strict_email('user@example.com')
        except ValidationError:
            self.fail("Valid email failed validation")
        
        # Invalid email should raise
        with self.assertRaises(ValidationError):
            validate_strict_email('invalid-email')
