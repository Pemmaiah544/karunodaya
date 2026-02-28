"""
Django signal handlers for portal app.
Automatically maintains CommunityProgress aggregates when ReadingAssessment changes.
"""

import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.profiles.models import ReadingAssessment
from services.community_service import CommunityProgressService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ReadingAssessment)
def on_reading_assessment_saved(sender, instance, created, **kwargs):
    """
    Signal handler: When a ReadingAssessment is created/updated,
    compute improvement_percent and update CommunityProgress aggregates.

    Args:
        sender: ReadingAssessment model
        instance: The ReadingAssessment instance being saved
        created: True if this is a new instance
        **kwargs: Additional signal kwargs
    """
    try:
        # Step 1: Compute improvement_percent if not already set
        if not instance.improvement_percent:
            previous = ReadingAssessment.objects.filter(
                child=instance.child,
                level=instance.level,
                assessed_at__lt=instance.assessed_at
            ).order_by('-assessed_at').first()

            if previous:
                instance.improvement_percent = CommunityProgressService.compute_improvement_percent(
                    instance, previous
                )
                # Save only the improvement_percent field (avoid infinite recursion)
                ReadingAssessment.objects.filter(pk=instance.pk).update(
                    improvement_percent=instance.improvement_percent
                )

        # Step 2: Get child's location
        child = instance.child
        parent_profile = child.parent

        # Check if parent has completed address (has city and pincode)
        if not (parent_profile.city and parent_profile.pincode):
            # Skip if parent hasn't completed address
            return

        # Step 3: Update CommunityProgress for this location
        # For locality, use city as fallback if not available
        locality = getattr(parent_profile, 'locality', None) or parent_profile.city
        CommunityProgressService.update_community_progress_for_location(
            parent_profile.city,
            locality
        )

    except Exception as e:
        logger.error(f"Error in on_reading_assessment_saved signal: {str(e)}", exc_info=True)


@receiver(post_delete, sender=ReadingAssessment)
def on_reading_assessment_deleted(sender, instance, **kwargs):
    """
    Signal handler: When a ReadingAssessment is deleted,
    recalculate and update CommunityProgress aggregates.

    Args:
        sender: ReadingAssessment model
        instance: The ReadingAssessment instance being deleted
        **kwargs: Additional signal kwargs
    """
    try:
        # Get child's location before it might be deleted
        child = instance.child
        parent_profile = child.parent

        # Check if parent has completed address (has city and pincode)
        if not (parent_profile.city and parent_profile.pincode):
            # Skip if parent hasn't completed address
            return

        # Recalculate aggregates for this location
        # For locality, use city as fallback if not available
        locality = getattr(parent_profile, 'locality', None) or parent_profile.city
        CommunityProgressService.update_community_progress_for_location(
            parent_profile.city,
            locality
        )

    except Exception as e:
        logger.error(f"Error in on_reading_assessment_deleted signal: {str(e)}", exc_info=True)
