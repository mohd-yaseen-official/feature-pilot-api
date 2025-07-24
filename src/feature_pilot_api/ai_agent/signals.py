import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from feedbacks.models import Feedback
from proposals.models import Proposal
from .fastapi_client import analyze_feedback, apply_proposal_changes

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Feedback)
def trigger_ai_analysis_on_feedback_creation(sender, instance, created, **kwargs):
    """Automatically trigger AI analysis when new feedback is created."""
    if created:
        # Use FastAPI endpoint instead of Celery
        analyze_feedback(instance.id)
        
        # Log the trigger
        logger.info(f"Triggered AI analysis for feedback {instance.id} in project {instance.project.id}")

@receiver(post_save, sender=Proposal)
def trigger_change_application_on_proposal_confirmation(sender, instance, **kwargs):
    """Automatically apply changes when proposal is confirmed."""
    # Check if this is a confirmation (is_confirmed changed to True)
    if instance.is_confirmed and instance.status == 'confirmed':
        # Use FastAPI endpoint instead of Celery
        apply_proposal_changes(instance.id)
        
        # Log the trigger
        logger.info(f"Triggered automatic change application for proposal {instance.id}")