from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token
from django.utils import timezone
from datetime import timedelta


class IsAuthenticatedOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
    Custom permission that allows authenticated users to perform any action,
    but unauthenticated users can only perform safe methods (GET, HEAD, OPTIONS).
    """
    pass


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission that only allows owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission that only allows staff users to edit objects.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_staff


class MobileTokenAuthentication(TokenAuthentication):
    """
    Custom token authentication for mobile apps with additional validation.
    """
    def authenticate_credentials(self, key):
        model = Token
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')
        
        if not token.user.is_active:
            raise AuthenticationFailed('User inactive or deleted.')
        
        # Check token age (optional - uncomment if you want token expiration)
        # token_age = timezone.now() - token.created
        # if token_age > timedelta(days=30):
        #     token.delete()
        #     raise AuthenticationFailed('Token has expired.')
        
        return (token.user, token)


class HasMobileAppPermission(permissions.BasePermission):
    """
    Custom permission for mobile app access.
    Checks if the user has permission to access mobile features.
    """
    def has_permission(self, request, view):
        # Allow authenticated users
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has mobile app permission (you can customize this)
        # For now, all authenticated users have access
        return True
    
    def has_object_permission(self, request, view, obj):
        # Implement object-level permissions if needed
        return True


class CanManageServers(permissions.BasePermission):
    """
    Custom permission for server management operations.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff users can manage all servers
        if request.user.is_staff:
            return True
        
        # Non-staff users can only view servers
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Non-staff users cannot modify servers
        return False


class CanViewAlerts(permissions.BasePermission):
    """
    Custom permission for alert viewing.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # All authenticated users can view alerts
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only staff can modify alerts
        return request.user.is_staff


class CanManageNetworkDevices(permissions.BasePermission):
    """
    Custom permission for network device management.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff users can manage all network devices
        if request.user.is_staff:
            return True
        
        # Non-staff users can only view network devices
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False


class IsAgentUser(permissions.BasePermission):
    """
    Custom permission for agent users (for data ingestion).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has agent role (you might want to add a role field to User model)
        # For now, we'll check if username starts with 'agent_' or if user is staff
        return (
            request.user.is_staff or 
            request.user.username.startswith('agent_') or
            hasattr(request.user, 'profile') and getattr(request.user.profile, 'is_agent', False)
        )
