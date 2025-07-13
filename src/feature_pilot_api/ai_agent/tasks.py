import logging
from celery import shared_task
from feedbacks.models import Feedback
from proposals.models import Proposal
from .services import AIAnalysisService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def analyze_feedback_task(self, feedback_id: int):
    """
    Background task to analyze feedback and create proposals.
    
    Args:
        feedback_id: ID of the feedback to analyze
    """
    try:
        feedback = Feedback.objects.get(id=feedback_id)
        project = feedback.project
        
        logger.info(f"Starting AI analysis for feedback {feedback_id}")
        
        # Initialize AI service
        ai_service = AIAnalysisService(project)
        
        # Analyze feedback
        analysis_result = ai_service.analyze_feedback(feedback.title)
        
        if 'error' in analysis_result:
            logger.error(f"AI analysis failed for feedback {feedback_id}: {analysis_result['error']}")
            raise Exception(analysis_result['error'])
        
        # Create proposal from analysis
        proposal = ai_service.create_proposal_from_analysis(feedback, analysis_result)
        
        logger.info(f"Successfully created proposal {proposal.id} for feedback {feedback_id}")
        
        return {
            'success': True,
            'feedback_id': feedback_id,
            'proposal_id': proposal.id,
            'analysis_result': analysis_result
        }
        
    except Feedback.DoesNotExist:
        logger.error(f"Feedback {feedback_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Error analyzing feedback {feedback_id}: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries  # Exponential backoff
            raise self.retry(countdown=countdown, exc=exc)
        else:
            # Mark proposal as failed if it exists
            try:
                proposal = Proposal.objects.get(feedback_id=feedback_id)
                proposal.status = 'failed'
                proposal.save()
            except Proposal.DoesNotExist:
                pass
            
            raise

@shared_task(bind=True, max_retries=3)
def apply_proposal_changes_task(self, proposal_id: int):
    """
    Background task to apply proposal changes to GitHub repository.
    
    Args:
        proposal_id: ID of the proposal to apply
    """
    try:
        proposal = Proposal.objects.get(id=proposal_id)
        project = proposal.feedback.project
        
        logger.info(f"Starting to apply changes for proposal {proposal_id}")
        
        # Initialize AI service
        ai_service = AIAnalysisService(project)
        
        # Apply changes
        result = ai_service.apply_proposal_changes(proposal)
        
        if not result['success']:
            logger.error(f"Failed to apply changes for proposal {proposal_id}: {result['message']}")
            raise Exception(result['message'])
        
        logger.info(f"Successfully applied changes for proposal {proposal_id}")
        
        return {
            'success': True,
            'proposal_id': proposal_id,
            'result': result
        }
        
    except Proposal.DoesNotExist:
        logger.error(f"Proposal {proposal_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Error applying changes for proposal {proposal_id}: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries  # Exponential backoff
            raise self.retry(countdown=countdown, exc=exc)
        else:
            # Mark proposal as failed
            try:
                proposal = Proposal.objects.get(id=proposal_id)
                proposal.status = 'failed'
                proposal.save()
            except Proposal.DoesNotExist:
                pass
            
            raise

@shared_task
def test_github_connection_task(project_id: int):
    """
    Background task to test GitHub connection for a project.
    
    Args:
        project_id: ID of the project to test
    """
    try:
        from projects.models import Project
        project = Project.objects.get(id=project_id)
        
        logger.info(f"Testing GitHub connection for project {project_id}")
        
        # Initialize AI service
        ai_service = AIAnalysisService(project)
        
        # Test connection
        result = ai_service.test_github_connection()
        
        logger.info(f"GitHub connection test result for project {project_id}: {result['message']}")
        
        return result
        
    except Project.DoesNotExist:
        logger.error(f"Project {project_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Error testing GitHub connection for project {project_id}: {str(exc)}")
        raise 