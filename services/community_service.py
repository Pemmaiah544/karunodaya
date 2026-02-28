"""
Community Progress Service Layer
Handles address validation and community progress aggregation.
"""

import re
from difflib import SequenceMatcher
from typing import Dict, Optional, List, Tuple
from django.db.models import Avg, Count, Q, F
from apps.profiles.models import ParentProfile, Child, ReadingAssessment
from apps.portal.models import CommunityProgress


def _normalize_city(name: str) -> str:
    """Lowercase and strip all non-alpha chars for fuzzy comparison."""
    return re.sub(r'[^a-z]', '', name.lower()) if name else ''


def resolve_city_variants(city: str, threshold: float = 0.85) -> List[str]:
    """
    Return all city values stored in the DB that are likely the same city
    as `city`, using fuzzy string similarity (SequenceMatcher).

    Handles common typos like 'Banglore' for 'Bangalore' or
    'Manglore' for 'Mangalore' (similarity >= 0.85).

    Args:
        city: The canonical city name (e.g. from the dropdown).
        threshold: Minimum similarity ratio to be considered a match.

    Returns:
        List of matching city strings as stored in DB (may be empty).
    """
    nc = _normalize_city(city)
    if not nc:
        return []

    all_db_cities = (
        ParentProfile.objects
        .exclude(city='').exclude(city=None)
        .values_list('city', flat=True)
        .distinct()
    )

    matches = []
    for db_city in all_db_cities:
        ndb = _normalize_city(db_city)
        if not ndb:
            continue
        score = SequenceMatcher(None, nc, ndb).ratio()
        if score >= threshold:
            matches.append(db_city)

    return matches

# Mapping of Indian states to major cities
STATE_TO_CITIES = {
    'Andhra Pradesh': ['Visakhapatnam', 'Vijayawada', 'Tirupati', 'Nellore'],
    'Arunachal Pradesh': ['Itanagar', 'Naharlagun'],
    'Assam': ['Guwahati', 'Silchar', 'Dibrugarh'],
    'Bihar': ['Patna', 'Gaya', 'Bhagalpur', 'Darbhanga'],
    'Chhattisgarh': ['Raipur', 'Bilaspur', 'Durg', 'Rajnandgaon'],
    'Goa': ['Panjim', 'Margao', 'Vasco da Gama'],
    'Gujarat': ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Bhavnagar'],
    'Haryana': ['Faridabad', 'Gurgaon', 'Hisar', 'Rohtak'],
    'Himachal Pradesh': ['Shimla', 'Kangra', 'Mandi', 'Kullu'],
    'Jharkhand': ['Ranchi', 'Jamshedpur', 'Dhanbad', 'Giridih'],
    'Karnataka': ['Bangalore', 'Mysore', 'Hubballi', 'Mangalore', 'Belgaum'],
    'Kerala': ['Kochi', 'Thiruvananthapuram', 'Kozhikode', 'Thrissur'],
    'Madhya Pradesh': ['Indore', 'Bhopal', 'Jabalpur', 'Gwalior', 'Ujjain'],
    'Maharashtra': ['Mumbai', 'Pune', 'Nagpur', 'Aurangabad', 'Nashik'],
    'Manipur': ['Imphal', 'Bishnupur'],
    'Meghalaya': ['Shillong', 'Tura'],
    'Mizoram': ['Aizawl', 'Lunglei'],
    'Nagaland': ['Kohima', 'Dimapur'],
    'Odisha': ['Bhubaneswar', 'Cuttack', 'Rourkela', 'Sambalpur'],
    'Punjab': ['Chandigarh', 'Amritsar', 'Ludhiana', 'Jalandhar'],
    'Rajasthan': ['Jaipur', 'Jodhpur', 'Udaipur', 'Ajmer', 'Kota'],
    'Sikkim': ['Gangtok', 'Pelling'],
    'Tamil Nadu': ['Chennai', 'Coimbatore', 'Salem', 'Madurai', 'Tirunelveli'],
    'Telangana': ['Hyderabad', 'Warangal', 'Nizamabad'],
    'Tripura': ['Agartala', 'Udaipur'],
    'Uttar Pradesh': ['Delhi', 'Lucknow', 'Kanpur', 'Varanasi', 'Agra', 'Meerut'],
    'Uttarakhand': ['Dehradun', 'Nainital', 'Rishikesh'],
    'West Bengal': ['Kolkata', 'Asansol', 'Siliguri', 'Darjeeling'],
    'Delhi': ['Delhi', 'New Delhi'],
}


class AddressValidationError(Exception):
    """Raised when address validation fails"""
    pass


class AddressValidator:
    """Validates and normalizes address data"""

    # Indian PIN code format: 6 digits
    PINCODE_REGEX = re.compile(r'^\d{6}$')

    REQUIRED_FIELDS = ['address', 'city', 'locality', 'state', 'pincode']

    @staticmethod
    def validate_address(data: Dict[str, str]) -> Tuple[bool, Dict[str, str]]:
        """
        Validate address data.

        Args:
            data: Dictionary with keys: address, city, locality, state, pincode

        Returns:
            Tuple of (is_valid: bool, errors: Dict[field_name] -> error_message)
        """
        errors = {}

        # Required fields
        for field in AddressValidator.REQUIRED_FIELDS:
            value = data.get(field, '').strip()
            if not value:
                errors[field] = f"{field.replace('_', ' ').title()} is required"

        if errors:
            return False, errors

        # Field-specific validation
        address = data.get('address', '').strip()
        city = data.get('city', '').strip()
        locality = data.get('locality', '').strip()
        state = data.get('state', '').strip()
        pincode = data.get('pincode', '').strip()

        # Length validation
        if len(address) < 5 or len(address) > 500:
            errors['address'] = "Address must be between 5 and 500 characters"

        if len(city) < 2 or len(city) > 100:
            errors['city'] = "City must be between 2 and 100 characters"

        if len(locality) < 2 or len(locality) > 100:
            errors['locality'] = "Locality must be between 2 and 100 characters"

        if len(state) < 2 or len(state) > 100:
            errors['state'] = "State must be between 2 and 100 characters"

        # PIN code validation (Indian format)
        if not AddressValidator.PINCODE_REGEX.match(pincode):
            errors['pincode'] = "PIN code must be 6 digits"

        return len(errors) == 0, errors

    @staticmethod
    def normalize_address(data: Dict[str, str]) -> Dict[str, str]:
        """
        Normalize address fields (trim, capitalize, etc.)

        Args:
            data: Raw address data

        Returns:
            Normalized address data
        """
        return {
            'address': data.get('address', '').strip(),
            'city': data.get('city', '').strip().title(),
            'locality': data.get('locality', '').strip().title(),
            'state': data.get('state', '').strip().title(),
            'pincode': data.get('pincode', '').strip(),
        }


class CommunityProgressService:
    """Handles community progress aggregation and queries"""

    @staticmethod
    def get_community_progress(
        city: str,
        locality: Optional[str] = None,
        reading_level: Optional[str] = None
    ) -> Dict:
        """
        Get aggregated community progress for a location.

        Real-time query on pre-aggregated CommunityProgress table
        (maintained by signals on ReadingAssessment save/delete).

        Args:
            city: City name
            locality: Optional locality name
            reading_level: Optional reading level filter (BEGINNER/INTERMEDIATE/ADVANCED)

        Returns:
            Dictionary with summary stats and level distribution
        """
        # Build query
        query = Q(city__iexact=city)

        if locality:
            query &= Q(locality__iexact=locality)

        if reading_level:
            query &= Q(reading_level=reading_level)

        # Fetch pre-aggregated records
        progress_records = CommunityProgress.objects.filter(query).order_by('reading_level')

        if not progress_records.exists():
            return {
                'city': city,
                'locality': locality or 'All',
                'summary': {
                    'total_children': 0,
                    'avg_wpm': None,
                    'avg_accuracy': None,
                    'improvement_percent': None,
                },
                'level_distribution': {},
                'error': 'No community data available for this location',
            }

        # Calculate summary stats from all levels
        total_children = sum(r.child_count for r in progress_records)
        total_wpm = sum((r.avg_wpm or 0) * r.child_count for r in progress_records)
        total_accuracy = sum((r.avg_accuracy or 0) * r.child_count for r in progress_records)
        total_improvement = sum((r.improvement_percent or 0) * r.child_count for r in progress_records)

        avg_wpm = total_wpm / total_children if total_children > 0 else None
        avg_accuracy = total_accuracy / total_children if total_children > 0 else None
        avg_improvement = total_improvement / total_children if total_children > 0 else None

        # Build level distribution
        level_distribution = {}
        for record in progress_records:
            level_key = record.get_reading_level_display()
            level_distribution[record.reading_level] = {
                'count': record.child_count,
                'percent': round((record.child_count / total_children * 100)) if total_children > 0 else 0,
                'avg_wpm': round(record.avg_wpm, 1) if record.avg_wpm else None,
                'avg_accuracy': round(record.avg_accuracy, 1) if record.avg_accuracy else None,
            }

        return {
            'city': city,
            'locality': locality or 'All locations',
            'summary': {
                'total_children': total_children,
                'avg_wpm': round(avg_wpm, 1) if avg_wpm else None,
                'avg_accuracy': round(avg_accuracy, 1) if avg_accuracy else None,
                'improvement_percent': round(avg_improvement, 1) if avg_improvement else None,
            },
            'level_distribution': level_distribution,
        }

    @staticmethod
    def compute_improvement_percent(
        latest_assessment: ReadingAssessment,
        previous_assessment: Optional[ReadingAssessment] = None
    ) -> Optional[float]:
        """
        Compute improvement percentage between two assessments.

        Args:
            latest_assessment: Most recent reading assessment
            previous_assessment: Previous assessment (or None to fetch)

        Returns:
            Improvement percentage (positive = improvement, negative = decline)
            or None if no previous assessment exists
        """
        if not previous_assessment:
            # Get previous assessment for this child at same level
            try:
                previous_assessment = ReadingAssessment.objects.filter(
                    child=latest_assessment.child,
                    level=latest_assessment.level,
                    assessed_at__lt=latest_assessment.assessed_at
                ).order_by('-assessed_at').first()
            except ReadingAssessment.DoesNotExist:
                return None

        if not previous_assessment:
            return None

        # Calculate % change in WPM
        previous_wpm = previous_assessment.wpm
        if previous_wpm == 0:
            return None

        improvement = ((latest_assessment.wpm - previous_wpm) / previous_wpm) * 100
        return round(improvement, 1)

    @staticmethod
    def get_locality_suggestions(city: str, limit: int = 10) -> List[str]:
        """
        Get list of localities for a city from existing profiles.

        Args:
            city: City name
            limit: Maximum number of suggestions

        Returns:
            List of locality names (empty list as locality is form-only field)
        """
        # Note: 'locality' is a form input field, not stored in ParentProfile database
        # Return empty list to allow free-text user input
        return []

    @staticmethod
    def get_city_suggestions(limit: int = 10) -> List[str]:
        """
        Get list of cities from existing profiles.

        Args:
            limit: Maximum number of suggestions

        Returns:
            List of city names
        """
        # Get cities where both city and pincode are filled (address completed)
        cities = ParentProfile.objects.filter(
            city__isnull=False
        ).exclude(
            city=''
        ).values_list('city', flat=True).distinct().order_by('-updated_at')[:limit]

        return [city for city in cities if city]

    @staticmethod
    def update_community_progress_for_location(city: str, locality: str) -> None:
        """
        Recalculate and update CommunityProgress for a specific location.
        Called by signals after ReadingAssessment changes.

        Args:
            city: City name
            locality: Locality name
        """
        # Get all assessments for this location by reading level
        # Note: locality filter simplified since locality field may not exist in database
        # Use city as primary grouping key
        assessments = ReadingAssessment.objects.filter(
            child__parent__city__iexact=city
        ).select_related('child')

        if not assessments.exists():
            # Delete progress record if no assessments
            CommunityProgress.objects.filter(
                city__iexact=city,
                locality__iexact=locality
            ).delete()
            return

        # Group by reading level and calculate aggregates
        from django.db.models import Q
        for level_code, level_name in Child.DIFFICULTY_LEVEL_CHOICES:
            level_assessments = assessments.filter(level=level_code)

            if not level_assessments.exists():
                # Delete if no assessments at this level
                CommunityProgress.objects.filter(
                    city__iexact=city,
                    locality__iexact=locality,
                    reading_level=level_code
                ).delete()
                continue

            # Get unique children at this level (latest assessment per child)
            child_ids = level_assessments.values('child_id').distinct()
            latest_assessments = []
            for child_id in [cid['child_id'] for cid in child_ids]:
                latest = level_assessments.filter(child_id=child_id).order_by('-assessed_at').first()
                if latest:
                    latest_assessments.append(latest)

            if not latest_assessments:
                CommunityProgress.objects.filter(
                    city__iexact=city,
                    locality__iexact=locality,
                    reading_level=level_code
                ).delete()
                continue

            # Calculate aggregates
            child_count = len(latest_assessments)
            avg_wpm = sum(a.wpm for a in latest_assessments) / child_count
            avg_accuracy = sum(a.accuracy for a in latest_assessments) / child_count

            # Calculate average improvement
            improvements = []
            for assessment in latest_assessments:
                if assessment.improvement_percent is not None:
                    improvements.append(assessment.improvement_percent)

            avg_improvement = sum(improvements) / len(improvements) if improvements else None

            # Normalize city/locality for consistent storage
            city_normalized = city.strip().title()
            locality_normalized = locality.strip().title()

            # Update or create CommunityProgress record
            progress, created = CommunityProgress.objects.update_or_create(
                city=city_normalized,
                locality=locality_normalized,
                reading_level=level_code,
                defaults={
                    'child_count': child_count,
                    'avg_wpm': avg_wpm,
                    'avg_accuracy': avg_accuracy,
                    'improvement_percent': avg_improvement,
                }
            )

            if created:
                print(f"Created CommunityProgress: {progress}")
            else:
                print(f"Updated CommunityProgress: {progress}")

    @staticmethod
    def get_young_readers(city: str, current_user_id: Optional[int] = None) -> Dict:
        """
        Get anonymized individual reader cards for a city.

        Args:
            city: City name
            current_user_id: Current logged-in user ID (to exclude their children)

        Returns:
            Dictionary with reader list and summary stats
        """
        GRADE_TARGETS = {
            'PRE_K': 10, 'KINDERGARTEN': 40,
            'GRADE_1': 60, 'GRADE_2': 100,
            'GRADE_3': 115, 'GRADE_4': 130,
            'GRADE_5': 160, 'GRADE_6': 170,
            'GRADE_7': 190, 'GRADE_8': 190,
        }
        AVATAR_COLORS = ['#fb923c', '#06b6d4', '#3b82f6', '#10b981', '#a855f7', '#f97316']

        # Build base query: exclude current user's children + only test-completed
        base_query = Q(reading_test_completed=True)
        if current_user_id:
            base_query &= ~Q(parent__user_id=current_user_id)

        # Fuzzy city matching: find all DB-stored city variants that match
        # the requested city (handles typos like 'Banglore' vs 'Bangalore').
        city_variants = resolve_city_variants(city)
        # Always include the exact city name itself as a fallback
        if city not in city_variants:
            city_variants.append(city)

        children = Child.objects.filter(
            base_query & Q(parent__city__in=city_variants)
        ).select_related('parent')


        if not children.exists():
            return {
                'city': city,
                'total_active': 0,
                'summary_line': '0 learners',
                'readers': [],
                'error': 'No readers found in this city',
            }

        # Build reader cards
        readers = []
        wpm_list = []

        for child in children:
            # Anonymize name: "Rahul S."
            name_parts = child.name.split()
            first_name = name_parts[0]
            last_initial = name_parts[-1][0] if len(name_parts) > 1 else ''
            display_name = f"{first_name} {last_initial}." if last_initial else f"{first_name}"

            # Avatar color from hash
            avatar_idx = hash(child.id) % len(AVATAR_COLORS)
            avatar_color = AVATAR_COLORS[avatar_idx]

            # Grade display
            grade_display = f"Class {child.grade.split('_')[-1]}" if child.grade else "Grade Unknown"

            # Level badge
            level_badges = {
                'BEGINNER': 'Enthusiast',
                'INTERMEDIATE': 'Silver Medalist',
                'ADVANCED': 'Top Achiever',
            }
            level_badge = level_badges.get(child.reading_difficulty_level, 'Reader')

            # WPM and progress
            wpm = child.reading_wpm or 0
            wpm_list.append(wpm)
            grade_target = GRADE_TARGETS.get(child.grade, 100)
            progress_percent = min(100, int((wpm / grade_target * 100) if grade_target > 0 else 0))

            # Assessment count
            assessment_count = ReadingAssessment.objects.filter(child=child).count()

            readers.append({
                'display_name': display_name,
                'initial': first_name[0],
                'avatar_color': avatar_color,
                'grade': grade_display,
                'level_badge': level_badge,
                'wpm': wpm,
                'progress_percent': progress_percent,
                'assessment_count': assessment_count,
                'is_top_reader': False,  # Set after finding max
            })

        # Mark top reader
        if readers:
            max_wpm_idx = max(range(len(readers)), key=lambda i: readers[i]['wpm'])
            readers[max_wpm_idx]['is_top_reader'] = True

            # Sort: top reader first, then by WPM descending
            readers.sort(key=lambda r: (-r['is_top_reader'], -r['wpm']))

        # Calculate summary stats
        total_active = len(readers)
        avg_wpm = sum(wpm_list) / len(wpm_list) if wpm_list else 0
        avg_accuracy_list = list(ReadingAssessment.objects.filter(
            child__in=children
        ).values_list('accuracy', flat=True))
        avg_accuracy = sum(avg_accuracy_list) / len(avg_accuracy_list) if avg_accuracy_list else 0

        summary_line = f"{total_active} learner{'s' if total_active != 1 else ''} · Avg {int(avg_wpm)} WPM · {int(avg_accuracy)}% accuracy"

        return {
            'city': city,
            'total_active': total_active,
            'summary_line': summary_line,
            'readers': readers,
        }
