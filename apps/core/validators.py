"""
Custom validators for the Karunodaya application.
"""
import re
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator as DjangoEmailValidator


class StrictEmailValidator(DjangoEmailValidator):
    """
    Strict email validator that ensures:
    - Valid email format with @ symbol
    - Domain name present
    - Valid TLD (top-level domain) like .com, .org, .in, etc.
    - Minimum 2 character TLD
    """
    
    message = 'Enter a valid email address with proper domain (e.g., user@example.com)'
    
    def __call__(self, value):
        """Validate the email address."""
        if not value:
            raise ValidationError(
                'Email cannot be empty',
                code='invalid'
            )
        
        # Check for @ symbol
        if '@' not in value:
            raise ValidationError(
                'Email must contain @ symbol',
                code='invalid'
            )
        
        # Split into user and domain parts
        try:
            user_part, domain_part = value.rsplit('@', 1)
        except ValueError:
            raise ValidationError(
                self.message,
                code='invalid'
            )
        
        # Validate user part exists
        if not user_part:
            raise ValidationError(
                'Email must have a username before @',
                code='invalid'
            )
        
        # Validate domain part has a dot (for TLD)
        if not domain_part or '.' not in domain_part:
            raise ValidationError(
                'Email must have a valid domain with extension (e.g., .com, .org)',
                code='invalid'
            )
        
        # Check for valid TLD
        domain_parts = domain_part.split('.')
        if len(domain_parts) < 2:
            raise ValidationError(
                'Email must have a valid domain extension',
                code='invalid'
            )
        
        # Validate TLD (last part) - must be at least 2 letters
        tld = domain_parts[-1]
        if len(tld) < 2 or not tld.isalpha():
            raise ValidationError(
                'Email must have a valid domain extension (e.g., .com, .org, .in)',
                code='invalid'
            )
        
        # Call parent Django validator for comprehensive email validation
        super().__call__(value)


def validate_strict_email(value):
    """
    Standalone function for strict email validation.
    Can be used directly in model fields or forms.
    """
    validator = StrictEmailValidator()
    validator(value)
