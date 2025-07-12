from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserSerializer  


@api_view(['POST'])
def create_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        if user is not None:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            token = {
                'access': access_token,
                'refresh': refresh_token
            }

            return Response({
                'status': 201,
                'message': 'User created successfully.',
                'token': token
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'status': 400,
                'message': 'Authentication failed after user creation.'
            }, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_user(request):
    user = request.user
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response({
            'status': 200,
            'message': 'User info retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    elif request.method == 'PATCH':
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 200,
                'message': 'User info updated successfully.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            'status': 400,
            'message': 'Validation error.',
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        user.is_active = False
        user.save()
        return Response({
            'status': 204,
            'message': 'User deactivated.'
        }, status=status.HTTP_204_NO_CONTENT)
