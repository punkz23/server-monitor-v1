from rest_framework import versioning
from rest_framework.response import Response
from rest_framework import status
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class APIVersioningMiddleware(MiddlewareMixin):
    """
    Middleware to handle API versioning with multiple strategies:
    1. URL path versioning (/api/v1/, /api/v2/)
    2. Header versioning (Accept: application/vnd.api+json;version=1)
    3. Query parameter versioning (?version=1)
    4. Custom header versioning (X-API-Version: 1)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Supported versions and their status
        self.supported_versions = {
            '1': {
                'status': 'current',
                'deprecated': False,
                'sunset_date': None,
                'migration_guide': None,
            },
            '2': {
                'status': 'beta',
                'deprecated': False,
                'sunset_date': None,
                'migration_guide': None,
            }
        }
        
        # Default version if none specified
        self.default_version = '1'
        
        # Version priority for detection
        self.version_priority = ['url', 'header', 'query', 'custom_header']
    
    def process_request(self, request):
        """
        Detect and set API version from various sources
        """
        if not request.path.startswith('/api/'):
            return None
        
        # Detect version from different sources
        version = None
        source = None
        
        # 1. URL path versioning (highest priority)
        if '/api/v' in request.path:
            import re
            match = re.search(r'/api/v(\d+)/', request.path)
            if match:
                version = match.group(1)
                source = 'url'
        
        # 2. Accept header versioning
        if not version:
            accept_header = request.META.get('HTTP_ACCEPT', '')
            if 'application/vnd.api+json' in accept_header:
                import re
                match = re.search(r'version=(\d+)', accept_header)
                if match:
                    version = match.group(1)
                    source = 'header'
        
        # 3. Query parameter versioning
        if not version:
            version = request.GET.get('version')
            if version:
                source = 'query'
        
        # 4. Custom header versioning
        if not version:
            version = request.META.get('HTTP_X_API_VERSION')
            if version:
                source = 'custom_header'
        
        # Use default version if none detected
        if not version:
            version = self.default_version
            source = 'default'
        
        # Validate version
        if version not in self.supported_versions:
            return Response({
                'error': 'unsupported_version',
                'message': f'API version {version} is not supported',
                'supported_versions': list(self.supported_versions.keys()),
                'default_version': self.default_version
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if version is deprecated
        version_info = self.supported_versions[version]
        if version_info['deprecated']:
            logger.warning(f"Deprecated API version {version} being used")
        
        # Store version information
        request.api_version = version
        request.api_version_source = source
        request.api_version_info = version_info
        
        logger.info(f"API version {version} detected from {source}")
        
        return None
    
    def process_response(self, request, response):
        """
        Add version information to response headers
        """
        if hasattr(request, 'api_version'):
            version_info = request.api_version_info
            
            # Add version headers
            response['API-Version'] = request.api_version
            response['API-Version-Status'] = version_info['status']
            
            if version_info['deprecated']:
                response['API-Version-Deprecated'] = 'true'
                if version_info['sunset_date']:
                    response['API-Version-Sunset'] = version_info['sunset_date']
                if version_info['migration_guide']:
                    response['API-Version-Migration-Guide'] = version_info['migration_guide']
            
            # Add supported versions header
            response['API-Supported-Versions'] = ','.join(self.supported_versions.keys())
            response['API-Default-Version'] = self.default_version
        
        return response


class APIVersioningMixin:
    """
    Mixin for views to handle version-specific logic
    """
    
    def get_versioned_serializer_class(self, version):
        """
        Get serializer class based on API version
        """
        serializer_map = getattr(self, 'version_serializer_map', {})
        return serializer_map.get(version, self.serializer_class)
    
    def get_serializer(self, *args, **kwargs):
        """
        Override to use version-specific serializer
        """
        version = getattr(self.request, 'api_version', '1')
        serializer_class = self.get_versioned_serializer_class(version)
        
        if serializer_class:
            kwargs['context'] = self.get_serializer_context()
            return serializer_class(*args, **kwargs)
        
        return super().get_serializer(*args, **kwargs)
    
    def get_versioned_response(self, data):
        """
        Add version-specific metadata to response
        """
        version = getattr(self.request, 'api_version', '1')
        version_info = getattr(self.request, 'api_version_info', {})
        
        response_data = data
        
        # Add version metadata for certain versions
        if version == '2':
            response_data = {
                'data': data,
                'meta': {
                    'version': version,
                    'version_status': version_info.get('status', 'unknown'),
                    'timestamp': self.request.build_absolute_uri()
                }
            }
        
        return response_data


class APIVersionDeprecationMiddleware(MiddlewareMixin):
    """
    Middleware to handle API version deprecation and sunset
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Deprecation warnings
        self.deprecation_warnings = {
            '1': {
                'warning_date': '2026-06-01',
                'sunset_date': '2026-12-31',
                'migration_guide': '/api/v2/docs/migration-from-v1',
                'reason': 'Improved data structure and enhanced security'
            }
        }
    
    def process_response(self, request, response):
        """
        Add deprecation warnings to response
        """
        if hasattr(request, 'api_version'):
            version = request.api_version
            
            if version in self.deprecation_warnings:
                deprecation_info = self.deprecation_warnings[version]
                
                # Add deprecation headers
                response['API-Version-Warning'] = deprecation_info['reason']
                response['API-Version-Warning-Date'] = deprecation_info['warning_date']
                response['API-Version-Sunset'] = deprecation_info['sunset_date']
                response['API-Version-Migration-Guide'] = deprecation_info['migration_guide']
                
                # Add warning to response body for API responses
                if (response.get('Content-Type', '').startswith('application/json') and 
                    hasattr(response, 'data') and response.data):
                    
                    if isinstance(response.data, dict):
                        response.data['warnings'] = {
                            'version_deprecation': {
                                'version': version,
                                'warning_date': deprecation_info['warning_date'],
                                'sunset_date': deprecation_info['sunset_date'],
                                'migration_guide': deprecation_info['migration_guide'],
                                'reason': deprecation_info['reason']
                            }
                        }
        
        return response


def get_api_version_info():
    """
    Utility function to get current API version information
    """
    return {
        'current_version': '1',
        'supported_versions': ['1', '2'],
        'default_version': '1',
        'versioning_strategies': {
            'url_path': '/api/v1/, /api/v2/',
            'header': 'Accept: application/vnd.api+json;version=1',
            'query_param': '?version=1',
            'custom_header': 'X-API-Version: 1'
        },
        'deprecation_schedule': {
            'v1': {
                'deprecated': False,
                'sunset_date': None,
                'migration_guide': None
            }
        }
    }


def validate_api_version(version):
    """
    Validate if API version is supported
    """
    supported_versions = ['1', '2']  # This should match the middleware
    return version in supported_versions


def get_versioned_url(url, version=None):
    """
    Convert URL to versioned URL
    """
    if version is None:
        version = '1'  # Default version
    
    if url.startswith('/api/'):
        return url.replace('/api/', f'/api/v{version}/')
    
    return url
