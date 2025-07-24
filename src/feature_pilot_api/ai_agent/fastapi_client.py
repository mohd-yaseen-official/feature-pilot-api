import httpx
import asyncio
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

FASTAPI_BASE_URL = os.environ.get("FASTAPI_BASE_URL", "http://localhost:8001")

def call_fastapi_endpoint(endpoint, **kwargs):
    """Synchronous wrapper to call FastAPI endpoints"""
    url = f"{FASTAPI_BASE_URL}{endpoint}"
    try:
        with httpx.Client() as client:
            response = client.post(url, json=kwargs)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error calling FastAPI endpoint {endpoint}: {str(e)}")
        return {"error": str(e)}

def analyze_feedback(feedback_id):
    """Replacement for analyze_feedback_task.delay()"""
    return call_fastapi_endpoint(f"/analyze-feedback/{feedback_id}")

def apply_proposal_changes(proposal_id):
    """Replacement for apply_proposal_changes_task.delay()"""
    return call_fastapi_endpoint(f"/apply-proposal/{proposal_id}")

def test_github_connection(project_id):
    """Replacement for test_github_connection_task.delay()"""
    return call_fastapi_endpoint(f"/test-github-connection/{project_id}")