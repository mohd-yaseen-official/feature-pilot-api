from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProjectSerializer
from projects.models import Project

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_project(request):
    serializer = ProjectSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        project = serializer.save()
        return Response({
            'status': 201,
            'message': 'Project created successfully.',
            'data': ProjectSerializer(project).data
        }, status=status.HTTP_201_CREATED)
    return Response({
        'status': 400,
        'message': 'Validation error.',
        'error': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_projects(request):
    projects = Project.objects.filter(user=request.user, is_deleted=False)
    serializer = ProjectSerializer(projects, many=True)
    return Response({
        'status': 200,
        'message': 'Projects retrieved successfully.',
        'data': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_project(request, id):
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

    if request.method == 'GET':
        serializer = ProjectSerializer(project)
        return Response({
            'status': 200,
            'message': 'Project info retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        serializer = ProjectSerializer(project, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 200,
                'message': 'Project updated successfully.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            'status': 400,
            'message': 'Validation error.',
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        project.is_deleted = True
        project.save()
        return Response({
            'status': 204,
            'message': 'Project deleted (soft delete).'
        }, status=status.HTTP_204_NO_CONTENT)
