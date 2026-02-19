from django import template

register = template.Library()

@register.filter
def human_failover_reason(reason):
    """Convert technical failover reasons to human-readable descriptions"""
    
    # Dictionary of technical reasons to human-readable descriptions
    translations = {
        # Internet connectivity issues
        'internet_status == 0': 'Internet connection was lost completely',
        'internet connectivity failed': 'Internet connection was lost completely',
        'no internet access': 'Internet connection was lost completely',
        
        # High packet loss
        'packet loss > 20': 'Severe packet loss detected (over 20%)',
        'high packet loss': 'Severe packet loss detected',
        'packet loss threshold exceeded': 'Severe packet loss detected',
        
        # Very high latency
        'latency > 500': 'Extremely slow response time detected (over 500ms)',
        'very high latency': 'Extremely slow response time detected',
        'latency threshold exceeded': 'Extremely slow response time detected',
        
        # DNS issues
        'dns_status == 0': 'DNS resolution failed completely',
        'dns resolution failed': 'DNS resolution failed completely',
        'dns lookup failed': 'DNS resolution failed completely',
        
        # General connectivity
        'connection lost': 'Connection was lost unexpectedly',
        'connection timeout': 'Connection timed out',
        'connection failed': 'Connection failed to establish',
        
        # Performance issues
        'performance degradation': 'Connection performance was severely degraded',
        'slow response': 'Connection became very slow',
        'unstable connection': 'Connection became unstable',
        
        # Default fallback
    }
    
    # Check for exact matches first
    if reason.lower() in translations:
        return translations[reason.lower()]
    
    # Check for partial matches
    reason_lower = reason.lower()
    for technical, human in translations.items():
        if technical.lower() in reason_lower:
            return human
    
    # Handle specific "Metrics threshold exceeded" cases
    if 'metrics threshold exceeded' in reason_lower:
        # Extract the specific metrics that caused the failover
        if 'packet_loss_percent' in reason_lower:
            return 'Severe packet loss detected - connection quality degraded'
        elif 'latency_ms' in reason_lower and 'packet_loss_percent' in reason_lower:
            return 'High latency and packet loss - connection severely degraded'
        elif 'latency_ms' in reason_lower:
            return 'High response time detected - connection slow'
        elif 'bandwidth_mbps' in reason_lower:
            return 'Low bandwidth detected - connection speed issues'
        else:
            return 'Performance thresholds exceeded - connection quality issues'
    
    # If no match found, provide a generic but helpful description
    if 'packet loss' in reason_lower:
        return 'Packet loss issues detected'
    elif 'latency' in reason_lower:
        return 'High response time detected'
    elif 'dns' in reason_lower:
        return 'DNS resolution problems'
    elif 'internet' in reason_lower:
        return 'Internet connectivity issues'
    elif 'connection' in reason_lower:
        return 'Connection problems detected'
    else:
        return f'Connection issue: {reason.title()}'

@register.filter
def format_duration(minutes):
    """Format duration in minutes to human-readable format"""
    if not minutes:
        return 'Unknown duration'
    
    minutes = int(minutes)
    
    if minutes < 60:
        return f'{minutes} minute{"s" if minutes != 1 else ""}'
    else:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if remaining_minutes == 0:
            return f'{hours} hour{"s" if hours != 1 else ""}'
        else:
            return f'{hours} hour{"s" if hours != 1 else ""} {remaining_minutes} minute{"s" if remaining_minutes != 1 else ""}'

@register.filter
def format_decimal(value):
    """Format numeric value to 2 decimal places"""
    try:
        if value is None:
            return '0.00'
        
        # Convert to float and format
        float_value = float(value)
        return f'{float_value:.2f}'
    except (ValueError, TypeError):
        # If conversion fails, return original value
        return str(value)
