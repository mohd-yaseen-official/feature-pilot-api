from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProposalSerializer
from proposals.models import Proposal
from projects.models import Project
from datetime import datetime

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_proposals(request):
    proposals = Proposal.objects.filter(feedback__project__user=request.user)
    serializer = ProposalSerializer(proposals, many=True)
    
    return Response({
        'status': 200,
        'message': 'All proposals retrieved successfully.',
        'data': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_project_proposals(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({
            'status': 404,
            'message': 'Project not found.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if project.user != request.user:
        return Response({
            'status': 403,
            'message': 'You do not have permission to access this project.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    proposals = Proposal.objects.filter(feedback__project=project)
    serializer = ProposalSerializer(proposals, many=True)
    
    return Response({
        'status': 200,
        'message': 'Project proposals retrieved successfully.',
        'data': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_proposal(request, proposal_id):
    try:
        proposal = Proposal.objects.get(id=proposal_id)
    except Proposal.DoesNotExist:
        return Response({
            'status': 404,
            'message': 'Proposal not found.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if user owns the project
    if proposal.feedback.project.user != request.user:
        return Response({
            'status': 403,
            'message': 'You do not have permission to confirm this proposal.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Check if proposal is already confirmed
    if proposal.is_confirmed:
        return Response({
            'status': 400,
            'message': 'Proposal is already confirmed.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update proposal status
    proposal.is_confirmed = True
    proposal.status = 'confirmed'
    proposal.save()
    
    # TODO: Trigger AI agent to apply changes
    # This is where you would integrate with your FeedbackToFeatureAgent
    # For now, we'll just update the status to 'applied' as a placeholder
    
    try:
        # Placeholder for AI agent integration
        # agent = FeedbackToFeatureAgent()
        # results = agent.apply_changes(proposal.proposal_data)
        
        # For now, just mark as applied
        proposal.status = 'applied'
        proposal.applied_at = datetime.now()
        proposal.pr_url = "https://github.com/example/pull/123"  # Placeholder
        proposal.save()
        
        return Response({
            'status': 200,
            'message': 'Proposal confirmed and changes applied successfully.',
            'data': ProposalSerializer(proposal).data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        proposal.status = 'failed'
        proposal.save()
        
        return Response({
            'status': 500,
            'message': 'Error applying changes.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
