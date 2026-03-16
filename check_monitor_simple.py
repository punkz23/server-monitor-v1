import os
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monitor.settings')
import django
django.setup()

from monitor.services.server_status_monitor import get_server_monitor

def check_monitoring():
    """Check monitoring system status"""
    print("🔍 Checking Server Monitor Status")
    print("=" * 50)
    
    try:
        monitor = get_server_monitor()
        print(f"✅ Monitor instance created: {monitor is not None}")
        
        if hasattr(monitor, 'running'):
            print(f"📊 Monitor running: {monitor.running}")
        else:
            print("❓ Monitor running status: Unknown")
            
        if hasattr(monitor, 'thread') and monitor.thread:
            print(f"🧵 Monitor thread alive: {monitor.thread.is_alive()}")
        else:
            print("❌ Monitor thread: Not found or dead")
            
        # Check recent server updates
        from monitor.models import Server
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        recent_servers = Server.objects.filter(enabled=True).order_by('-last_checked')[:3]
        
        print("\n📈 Most Recent Server Checks:")
        for server in recent_servers:
            hours_ago = (now - server.last_checked).total_seconds() / 3600 if server.last_checked else None
            print(f"  🖥 {server.name}: {server.last_status} ({hours_ago:.1f}h ago)" if hours_ago else f"  🖥 {server.name}: {server.last_status} (Never)")
            
    except Exception as e:
        print(f"❌ Error checking monitor: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_monitoring()
