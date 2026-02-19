from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def mobile_login(request):
    """
    Mobile API login endpoint that returns an authentication token
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'missing_credentials',
            'message': 'Both username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Authenticate user
    user = authenticate(username=username, password=password)
    
    if not user:
        return Response({
            'error': 'invalid_credentials',
            'message': 'Invalid username or password'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        return Response({
            'error': 'account_disabled',
            'message': 'Account is disabled'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Get or create token
    token, created = Token.objects.get_or_create(user=user)
    
    # Update token creation time for new tokens
    if created:
        token.created = timezone.now()
        token.save()
    
    return Response({
        'token': token.key,
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'token_created': token.created.isoformat() if token.created else None,
        'message': 'Login successful'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mobile_logout(request):
    """
    Mobile API logout endpoint that deletes the authentication token
    """
    try:
        # Delete the user's token
        token = Token.objects.get(user=request.user)
        token.delete()
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
    except Token.DoesNotExist:
        return Response({
            'message': 'Already logged out'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mobile_token_info(request):
    """
    Mobile API endpoint to get current token information
    """
    try:
        token = Token.objects.get(user=request.user)
        
        return Response({
            'token': token.key,
            'user_id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'token_created': token.created.isoformat() if token.created else None,
            'token_age_days': (timezone.now() - token.created).days if token.created else None
        }, status=status.HTTP_200_OK)
        
    except Token.DoesNotExist:
        return Response({
            'error': 'no_token',
            'message': 'No authentication token found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mobile_refresh_token(request):
    """
    Mobile API endpoint to refresh the authentication token
    """
    try:
        # Delete old token
        old_token = Token.objects.get(user=request.user)
        old_token.delete()
        
        # Create new token
        new_token = Token.objects.create(user=request.user)
        new_token.created = timezone.now()
        new_token.save()
        
        return Response({
            'token': new_token.key,
            'message': 'Token refreshed successfully',
            'token_created': new_token.created.isoformat()
        }, status=status.HTTP_200_OK)
        
    except Token.DoesNotExist:
        # Create new token if none exists
        new_token = Token.objects.create(user=request.user)
        new_token.created = timezone.now()
        new_token.save()
        
        return Response({
            'token': new_token.key,
            'message': 'New token created',
            'token_created': new_token.created.isoformat()
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def mobile_register(request):
    """
    Mobile API registration endpoint for new users
    """
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    
    if not username or not password:
        return Response({
            'error': 'missing_fields',
            'message': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate password length
    if len(password) < 8:
        return Response({
            'error': 'weak_password',
            'message': 'Password must be at least 8 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if username already exists
    if User.objects.filter(username=username).exists():
        return Response({
            'error': 'username_exists',
            'message': 'Username already exists'
        }, status=status.HTTP_409_CONFLICT)
    
    # Check if email already exists
    if email and User.objects.filter(email=email).exists():
        return Response({
            'error': 'email_exists',
            'message': 'Email already exists'
        }, status=status.HTTP_409_CONFLICT)
    
    try:
        # Create new user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create token for the new user
        token = Token.objects.create(user=user)
        token.created = timezone.now()
        token.save()
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'message': 'Registration successful'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': 'registration_failed',
            'message': f'Registration failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mobile_profile(request):
    """
    Mobile API endpoint to get user profile information
    """
    user = request.user
    
    return Response({
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'is_active': user.is_active,
        'date_joined': user.date_joined.isoformat() if user.date_joined else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    }, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def mobile_update_profile(request):
    """
    Mobile API endpoint to update user profile
    """
    user = request.user
    email = request.data.get('email', user.email)
    first_name = request.data.get('first_name', user.first_name)
    last_name = request.data.get('last_name', user.last_name)
    
    # Check if email is being changed and if it already exists
    if email != user.email and User.objects.filter(email=email).exists():
        return Response({
            'error': 'email_exists',
            'message': 'Email already exists'
        }, status=status.HTTP_409_CONFLICT)
    
    try:
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'update_failed',
            'message': f'Profile update failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mobile_change_password(request):
    """
    Mobile API endpoint to change user password
    """
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not old_password or not new_password:
        return Response({
            'error': 'missing_fields',
            'message': 'Both old_password and new_password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify old password
    if not user.check_password(old_password):
        return Response({
            'error': 'invalid_old_password',
            'message': 'Old password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate new password
    if len(new_password) < 8:
        return Response({
            'error': 'weak_password',
            'message': 'New password must be at least 8 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user.set_password(new_password)
        user.save()
        
        # Delete all tokens for this user (force re-login on all devices)
        Token.objects.filter(user=user).delete()
        
        return Response({
            'message': 'Password changed successfully. Please login again.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'password_change_failed',
            'message': f'Password change failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
