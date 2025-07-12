from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import FeedbackSerializer
from feedbacks.models import Feedback
from projects.models import Project

@api_view(['POST'])
def create_feedback(request):
    project_key = request.data.get('project_key')
    
    if not project_key:
        return Response({
            'status': 400,
            'message': 'Project key is required.',
            'error': 'Missing project_key field'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        project = Project.objects.get(project_key=project_key)
    except Project.DoesNotExist:
        return Response({
            'status': 404,
            'message': 'Project not found.',
            'error': 'Invalid project key'
        }, status=status.HTTP_404_NOT_FOUND)
    
    data = request.data.copy()
    data['project'] = project.id
    
    serializer = FeedbackSerializer(data=data)
    if serializer.is_valid():
        feedback = serializer.save()
        return Response({
            'status': 201,
            'message': 'Feedback created successfully.',
            'data': FeedbackSerializer(feedback).data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'status': 400,
        'message': 'Validation error.',
        'error': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_feedbacks(request, id):
    try:
        project = Project.objects.get(id=id)
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
    
    feedbacks = Feedback.objects.filter(project=project)
    serializer = FeedbackSerializer(feedbacks, many=True)
    
    return Response({
        'status': 200,
        'message': 'Project feedbacks retrieved successfully.',
        'data': serializer.data
    }, status=status.HTTP_200_OK)



