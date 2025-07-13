import os
import logging
from typing import Dict, Any, List
from django.utils import timezone
from .agent import FeedbackToFeatureAgent
from projects.models import Project
from proposals.models import Proposal

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """Service class for handling AI feedback analysis using existing models"""
    
    def __init__(self, project: Project):
        """
        Initialize the service with project settings
        
        Args:
            project: Project instance with github_token and github_repo_path
        """
        self.project = project
        self.github_repo = project.github_repo_path
        self.github_token = project.github_token
        
        # Set environment variables for the agent
        os.environ["GITHUB_TOKEN"] = self.github_token
        os.environ["GITHUB_REPO"] = self.github_repo
        
        # Initialize the AI agent
        try:
            self.agent = FeedbackToFeatureAgent()
        except Exception as e:
            logger.error(f"Failed to initialize AI agent: {str(e)}")
            raise
    
    def analyze_feedback(self, feedback_text: str) -> Dict[str, Any]:
        """
        Analyze feedback using the AI agent
        
        Args:
            feedback_text: The feedback text to analyze
            
        Returns:
            Dict containing analysis results or error information
        """
        try:
            logger.info(f"Starting AI analysis for feedback: {feedback_text[:100]}...")
            
            # Use the agent to analyze feedback
            result = self.agent.analyze_feedback(feedback_text)
            
            logger.info(f"AI analysis completed. Status: {'error' if 'error' in result else 'success'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return {
                "error": f"AI analysis failed: {str(e)}",
                "feedback": feedback_text
            }
    
    def create_proposal_from_analysis(self, feedback, analysis_result: Dict[str, Any]) -> Proposal:
        """
        Create a Proposal instance from AI analysis results
        
        Args:
            feedback: Feedback instance
            analysis_result: Results from AI analysis
            
        Returns:
            Proposal instance
        """
        # Structure the proposal data
        proposal_data = {
            "feedback_analysis": analysis_result.get('feedback_analysis', ''),
            "files_examined": analysis_result.get('files_to_examine', []),
            "proposed_changes": analysis_result.get('proposed_changes', []),
            "additional_recommendations": analysis_result.get('additional_recommendations', ''),
            "ai_generated": True,
            "analysis_timestamp": timezone.now().isoformat()
        }
        
        # Create proposal
        proposal = Proposal.objects.create(
            feedback=feedback,
            proposal_data=proposal_data,
            status='pending'
        )
        
        return proposal
    
    def apply_proposal_changes(self, proposal: Proposal, change_indices: List[int] = None) -> Dict[str, Any]:
        """
        Apply changes from a proposal
        
        Args:
            proposal: Proposal instance
            change_indices: List of change indices to apply (None for all)
            
        Returns:
            Dict containing success status and results
        """
        try:
            logger.info(f"Applying changes for proposal {proposal.id}")
            
            proposal_data = proposal.proposal_data
            proposed_changes = proposal_data.get('proposed_changes', [])
            
            if not proposed_changes:
                return {
                    "success": False,
                    "message": "No proposed changes found",
                    "errors": ["No changes to apply"]
                }
            
            # Filter changes if indices provided
            if change_indices is not None:
                filtered_changes = []
                for i in change_indices:
                    if 0 <= i < len(proposed_changes):
                        filtered_changes.append(proposed_changes[i])
                proposed_changes = filtered_changes
            
            if not proposed_changes:
                return {
                    "success": False,
                    "message": "No valid changes found to apply",
                    "errors": ["Invalid change indices"]
                }
            
            # Convert to the format expected by the agent
            agent_proposal = {
                "feedback_analysis": proposal_data.get('feedback_analysis', ''),
                "proposed_changes": proposed_changes
            }
            
            # Apply changes using the agent
            results = self.agent.apply_changes(agent_proposal)
            
            # Update proposal status based on results
            pull_request_urls = []
            errors = []
            
            for result in results:
                if result.startswith("✅ PR Created:"):
                    # Extract PR URL
                    pr_url = result.replace("✅ PR Created: ", "")
                    pull_request_urls.append(pr_url)
                elif result.startswith("❌"):
                    errors.append(result)
            
            success = len(pull_request_urls) > 0 and len(errors) == 0
            
            # Update proposal
            if success:
                proposal.status = 'applied'
                proposal.applied_at = timezone.now()
                if pull_request_urls:
                    proposal.pr_url = pull_request_urls[0]  # Store first PR URL
                proposal.save()
                
                # Update proposal_data with results
                proposal_data['applied_changes'] = proposed_changes
                proposal_data['pull_request_urls'] = pull_request_urls
                proposal_data['applied_at'] = proposal.applied_at.isoformat()
                proposal.proposal_data = proposal_data
                proposal.save()
            
            return {
                "success": success,
                "message": f"Applied {len(pull_request_urls)} changes successfully" if success else "Some changes failed to apply",
                "pull_request_urls": pull_request_urls,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error applying proposal changes: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to apply changes: {str(e)}",
                "errors": [str(e)]
            }
    
    def test_github_connection(self) -> Dict[str, Any]:
        """
        Test the GitHub connection
        
        Returns:
            Dict containing success status and message
        """
        try:
            logger.info("Testing GitHub connection")
            
            # Try to access the repository
            repo = self.agent.repo
            
            # Get basic repo info to verify connection
            repo_name = repo.name
            repo_description = repo.description or "No description"
            
            return {
                "success": True,
                "message": f"Successfully connected to {repo_name}: {repo_description}"
            }
            
        except Exception as e:
            logger.error(f"GitHub connection test failed: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to connect to GitHub: {str(e)}"
            }
    
    def validate_proposal(self, proposal_data: Dict[str, Any]) -> bool:
        """
        Validate a proposal using the agent's validation method
        
        Args:
            proposal_data: The proposal data to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Convert to agent format for validation
        agent_proposal = {
            "feedback_analysis": proposal_data.get('feedback_analysis', ''),
            "proposed_changes": proposal_data.get('proposed_changes', [])
        }
        
        return self.agent.validate_proposal(agent_proposal)
    
    def get_repository_files(self, path: str = "") -> List[str]:
        """
        Get list of files in the repository
        
        Args:
            path: Optional path to list files from
            
        Returns:
            List of file paths
        """
        try:
            return self.agent.list_all_files(path)
        except Exception as e:
            logger.error(f"Error getting repository files: {str(e)}")
            return []
    
    def read_repository_file(self, file_path: str) -> str:
        """
        Read a file from the repository
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File contents as string
        """
        try:
            return self.agent.read_github_file(file_path)
        except Exception as e:
            logger.error(f"Error reading repository file {file_path}: {str(e)}")
            return f"Error reading file: {str(e)}" 