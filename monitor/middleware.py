from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class TokenValidationMiddleware(MiddlewareMixin):
    """
    Middleware to validate and manage authentication tokens.
    
    Features:
    - Token age validation (optional)
    - Request logging for authenticated users
    - Token cleanup for inactive users
    - Rate limiting hints
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Configuration
        self.token_max_age_days = 30  # Set to None to disable token expiration
        self.cleanup_probability = 0.01  # 1% chance to cleanup old tokens per request
        self.log_authenticated_requests = True
    
    def process_request(self, request):
        """
        Process incoming request for token validation and logging.
        """
        # Check if this is an API request
        if not request.path.startswith('/api/'):
            return None
        
        # Extract token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Token '):
            token_key = auth_header[6:]  # Remove 'Token ' prefix
            
            try:
                token = Token.objects.select_related('user').get(key=token_key)
                
                # Validate user is active
                if not token.user.is_active:
                    logger.warning(f"Inactive user {token.user.username} attempted API access")
                    return JsonResponse({
                        'error': 'account_disabled',
                        'message': 'Account is disabled'
                    }, status=401)
                
                # Optional: Check token age
                if self.token_max_age_days and token.created:
                    token_age = timezone.now() - token.created
                    if token_age.days > self.token_max_age_days:
                        logger.warning(f"Expired token used by user {token.user.username}")
                        token.delete()
                        return JsonResponse({
                            'error': 'token_expired',
                            'message': 'Token has expired. Please login again.'
                        }, status=401)
                
                # Update last used timestamp (you might want to add this field to Token model)
                # token.last_used = timezone.now()
                # token.save(update_fields=['last_used'])
                
                # Log authenticated request
                if self.log_authenticated_requests:
                    logger.info(f"API access: {token.user.username} -> {request.method} {request.path}")
                
                # Add user info to request for logging
                request.auth_user = token.user
                request.auth_token = token
                
            except Token.DoesNotExist:
                # Don't handle invalid token here - let DRF handle it
                logger.warning(f"Invalid token used for API access: {token_key[:8]}...")
                pass
        
        # Random cleanup of old tokens
        if self.cleanup_probability and self.token_max_age_days:
            import random
            if random.random() < self.cleanup_probability:
                self._cleanup_old_tokens()
        
        return None
    
    def _cleanup_old_tokens(self):
        """
        Clean up tokens older than the maximum age.
        """
        if not self.token_max_age_days:
            return
        
        cutoff_date = timezone.now() - timedelta(days=self.token_max_age_days)
        
        try:
            old_count = Token.objects.filter(created__lt=cutoff_date).count()
            if old_count > 0:
                deleted_count = Token.objects.filter(created__lt=cutoff_date).delete()[0]
                logger.info(f"Cleaned up {deleted_count} expired tokens")
        except Exception as e:
            logger.error(f"Error cleaning up old tokens: {e}")


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware for API endpoints.
    
    Note: This is a basic implementation. For production use,
    consider using django-ratelimit or redis-based rate limiting.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Rate limits per user per minute
        self.rate_limits = {
            'default': 1000,  # 1000 requests per minute (increased)
            'auth': 100,      # 100 auth requests per minute (increased)
            'agent': 2000,   # 2000 agent requests per minute (increased)
        }
        
        # In-memory storage for rate limits (reset on server restart)
        self.rate_limit_storage = {}
    
    def process_request(self, request):
        """
        Check rate limits for API requests.
        """
        if not request.path.startswith('/api/'):
            return None
        
        # Get user identifier
        user_id = self._get_user_id(request)
        if not user_id:
            return None
        
        # Determine rate limit category
        category = self._get_rate_limit_category(request)
        max_requests = self.rate_limits.get(category, self.rate_limits['default'])
        
        # Check rate limit
        current_time = timezone.now()
        minute_key = current_time.strftime('%Y%m%d%H%M')
        storage_key = f"{user_id}:{category}:{minute_key}"
        
        current_count = self.rate_limit_storage.get(storage_key, 0)
        
        if current_count >= max_requests:
            logger.warning(f"Rate limit exceeded for user {user_id} in category {category}")
            return JsonResponse({
                'error': 'rate_limit_exceeded',
                'message': f'Rate limit exceeded. Maximum {max_requests} requests per minute.',
                'retry_after': 60
            }, status=429)
        
        # Increment counter
        self.rate_limit_storage[storage_key] = current_count + 1
        
        # Clean up old entries (keep only last 5 minutes)
        self._cleanup_old_rate_limits(current_time)
        
        return None
    
    def _get_user_id(self, request):
        """
        Get user identifier for rate limiting.
        """
        # Try to get user from token
        if hasattr(request, 'auth_user'):
            return f"user:{request.auth_user.id}"
        
        # Fall back to IP address (less reliable)
        ip_address = self._get_client_ip(request)
        return f"ip:{ip_address}"
    
    def _get_rate_limit_category(self, request):
        """
        Determine rate limit category based on request path.
        """
        path = request.path
        
        if '/auth/' in path:
            return 'auth'
        elif '/agent/ingest/' in path:
            return 'agent'
        else:
            return 'default'
    
    def _get_client_ip(self, request):
        """
        Get client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _cleanup_old_rate_limits(self, current_time):
        """
        Clean up old rate limit entries to prevent memory leaks.
        """
        cutoff_time = current_time - timedelta(minutes=5)
        cutoff_minute = cutoff_time.strftime('%Y%m%d%H%M')
        
        keys_to_delete = []
        for key in self.rate_limit_storage.keys():
            if key.endswith(f':{cutoff_minute}'):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.rate_limit_storage[key]


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to API responses.
    Note: CORS headers are handled by django-cors-headers middleware.
    """
    
    def process_response(self, request, response):
        """
        Add security headers to API responses.
        """
        if request.path.startswith('/api/'):
            # Security headers
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            
            # API version hint
            response['API-Version'] = '1.0'
            
            # Cache control for API responses
            if request.method in ['GET', 'HEAD', 'OPTIONS']:
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
        
        return response


class AuditLogMiddleware(MiddlewareMixin):
    """
    Audit logging for important API operations.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Operations to audit log
        self.audit_operations = [
            'POST',  # Create operations
            'PUT',   # Update operations
            'DELETE', # Delete operations
        ]
    
    def process_response(self, request, response):
        """
        Log important API operations.
        """
        if (request.path.startswith('/api/') and 
            request.method in self.audit_operations and
            response.status_code < 400):  # Only log successful operations
            
            user = getattr(request, 'auth_user', None)
            username = user.username if user else 'anonymous'
            
            logger.info(f"AUDIT: {username} {request.method} {request.path} -> {response.status_code}")
        
        return response
