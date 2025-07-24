import os
import django
import logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "feature_pilot_api.settings")
django.setup()

from fastapi import FastAPI, APIRouter, BackgroundTasks
from feedbacks.models import Feedback
from proposals.models import Proposal
from projects.models import Project
from .services import AIAnalysisService

app = FastAPI()
router = APIRouter()
logger = logging.getLogger(__name__)

def analyze_feedback_job(feedback_id: int):
    try:
        feedback = Feedback.objects.get(id=feedback_id)
        project = feedback.project
        ai_service = AIAnalysisService(project)
        analysis_result = ai_service.analyze_feedback(feedback.title)
        if 'error' in analysis_result:
            logger.error(f"Error analyzing feedback {feedback_id}: {analysis_result['error']}")
            return
        proposal = ai_service.create_proposal_from_analysis(feedback, analysis_result)
        logger.info(f"Successfully created proposal for feedback {feedback_id}")
    except Exception as exc:
        logger.error(f"Exception in analyze_feedback_job for feedback {feedback_id}: {str(exc)}")
        pass

def apply_proposal_changes_job(proposal_id: int):
    try:
        proposal = Proposal.objects.get(id=proposal_id)
        project = proposal.feedback.project
        ai_service = AIAnalysisService(project)
        result = ai_service.apply_proposal_changes(proposal)
        if not result.get('success', False):
            logger.error(f"Failed to apply changes for proposal {proposal_id}: {result.get('message', 'Unknown error')}")
            return
        logger.info(f"Successfully applied changes for proposal {proposal_id}")
    except Exception as exc:
        logger.error(f"Exception in apply_proposal_changes_job for proposal {proposal_id}: {str(exc)}")
        pass

def test_github_connection_job(project_id: int):
    try:
        project = Project.objects.get(id=project_id)
        ai_service = AIAnalysisService(project)
        result = ai_service.test_github_connection()
        logger.info(f"GitHub connection test result for project {project_id}: {result['message']}")
        return result
    except Project.DoesNotExist:
        logger.error(f"Project {project_id} not found")
        return {"success": False, "message": f"Project {project_id} not found"}
    except Exception as exc:
        logger.error(f"Error testing GitHub connection for project {project_id}: {str(exc)}")
        return {"success": False, "message": str(exc)}

@router.post("/analyze-feedback/{feedback_id}")
async def analyze_feedback(feedback_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(analyze_feedback_job, feedback_id)
    return {"status": "started", "feedback_id": feedback_id}

@router.post("/apply-proposal/{proposal_id}")
async def apply_proposal(proposal_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(apply_proposal_changes_job, proposal_id)
    return {"status": "started", "proposal_id": proposal_id}

@router.post("/test-github-connection/{project_id}")
async def test_github_connection(project_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(test_github_connection_job, project_id)
    return {"status": "started", "project_id": project_id}

app.include_router(router)