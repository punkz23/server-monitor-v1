#!/usr/bin/env python
"""Test metrics monitoring service"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.services.metrics_monitor_service import MetricsMonitorService

def test_metrics_monitoring():
    print('🔍 Testing Comprehensive Metrics Monitoring')
    print('=' * 60)
    
    monitor = MetricsMonitorService()
    
    # Test with one of the monitored servers
    test_ip = '192.168.254.13'
    print(f'Testing metrics monitoring for {test_ip}:')
    
    try:
        metrics = monitor.get_comprehensive_metrics(test_ip)
        
        if 'error' in metrics:
            print(f'❌ Error: {metrics["error"]}')
        else:
            print('✅ Metrics collected successfully:')
            print(f'   📊 Timestamp: {metrics["timestamp"]}')
            print(f'   🔄 Cached: {metrics["cached"]}')
            
            current = metrics.get('current', {})
            
            if 'cpu' in current:
                cpu = current['cpu']
                print(f'   🖥️  CPU: {cpu.get("usage_percent", "N/A")}% - {cpu.get("status", "unknown")}')
            
            if 'ram' in current:
                ram = current['ram']
                print(f'   💾 RAM: {ram.get("usage_percent", "N/A")}% - {ram.get("status", "unknown")}')
            
            if 'disk' in current:
                disk = current['disk']
                print(f'   💿 Disk: {disk.get("usage_percent", "N/A")}% - {disk.get("status", "unknown")}')
            
            if 'ssl' in current:
                ssl = current['ssl']
                print(f'   🔒 SSL: {ssl.get("days_remaining", "N/A")} days - {ssl.get("status", "unknown")}')
            
            changes = metrics.get('changes', {})
            if changes:
                print(f'   🔄 Changes detected: {len(changes)} items')
                for metric, change in changes.items():
                    print(f'      {metric}: {change["old"]} → {change["new"]} ({change["direction"]})')
            else:
                print('   🔄 No changes detected')
                
    except Exception as e:
        print(f'❌ Test failed: {e}')

if __name__ == '__main__':
    test_metrics_monitoring()
