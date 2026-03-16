#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monitor.settings')

# Setup Django
django.setup()

from monitor.models import Server
from django.utils import timezone
from datetime import timedelta

def check_server_status():
    """Check server monitoring status and identify issues"""
    now = timezone.now()
    
    print(f"🔍 Server Monitoring Status Check")
    print(f"📅 Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Get all enabled servers
    servers = Server.objects.filter(enabled=True)
    total_servers = servers.count()
    
    print(f"📊 Total Enabled Servers: {total_servers}")
    print()
    
    # Check servers with old check times
    old_threshold = now - timedelta(hours=6)
    old_servers = servers.filter(last_checked__lt=old_threshold).order_by('-last_checked')
    
    if old_servers.exists():
        print(f"⚠️  Servers with OLD check times (>6 hours ago):")
        print("-" * 60)
        
        for server in old_servers:
            hours_ago = None
            if server.last_checked:
                hours_ago = (now - server.last_checked).total_seconds() / 3600
            
            status_emoji = "✅" if server.last_status == "UP" else "❌" if server.last_status == "DOWN" else "❓"
            
            print(f"  {status_emoji} {server.name}")
            print(f"     📍 IP: {server.ip_address}")
            print(f"     📊 Status: {server.last_status}")
            print(f"     ⏰ Last Checked: {server.last_checked.strftime('%Y-%m-%d %H:%M:%S') if server.last_checked else 'Never'}")
            print(f"     ⏳ Hours Ago: {hours_ago:.1f}" if hours_ago else "N/A")
            print(f"     🔄 Method: {getattr(server, 'last_check_method', 'Unknown')}")
            print()
    else:
        print("✅ All servers have been checked within the last 6 hours!")
    
    # Show most recent checks
    print("📈 Most Recent Server Checks:")
    print("-" * 60)
    recent_servers = servers.order_by('-last_checked')[:5]
    
    for i, server in enumerate(recent_servers, 1):
        hours_ago = None
        if server.last_checked:
            hours_ago = (now - server.last_checked).total_seconds() / 3600
        
        status_emoji = "✅" if server.last_status == "UP" else "❌" if server.last_status == "DOWN" else "❓"
        
        print(f"  {i}. {status_emoji} {server.name}")
        print(f"     ⏰ {hours_ago:.1f} hours ago" if hours_ago else "N/A")
        print(f"     📊 {server.last_status}")
        print()
    
    # Check monitoring system status
    print("🔧 Monitoring System Analysis:")
    print("-" * 60)
    
    # Check if monitoring is running properly
    very_old_threshold = now - timedelta(hours=24)
    very_old_servers = servers.filter(last_checked__lt=very_old_threshold)
    
    if very_old_servers.exists():
        print(f"🚨 CRITICAL: {very_old_servers.count()} servers haven't been checked in 24+ hours!")
        for server in very_old_servers:
            print(f"     🚨 {server.name}: Last checked {server.last_checked}")
    else:
        print("✅ No servers with critical check delays")
    
    # Calculate uptime percentage
    up_count = servers.filter(last_status="UP").count()
    down_count = servers.filter(last_status="DOWN").count()
    unknown_count = total_servers - up_count - down_count
    
    if total_servers > 0:
        uptime_percentage = (up_count / total_servers) * 100
        print(f"📈 Network Health: {uptime_percentage:.1f}% uptime")
        print(f"     ✅ Up: {up_count}")
        print(f"     ❌ Down: {down_count}")
        print(f"     ❓ Unknown: {unknown_count}")
    
    print()
    print("🎯 Recommendations:")
    print("-" * 60)
    
    if old_servers.exists():
        print("⚠️  IMMEDIATE ACTIONS NEEDED:")
        print("   1. Check if monitoring service is running")
        print("   2. Verify network connectivity to servers")
        print("   3. Review monitoring logs for errors")
        print("   4. Check scheduled tasks/cron jobs")
        print("   5. Verify server accessibility")
    
    if very_old_servers.exists():
        print("🚨 CRITICAL ACTIONS:")
        print("   1. Restart monitoring service immediately")
        print("   2. Check server infrastructure")
        print("   3. Verify database connectivity")
        print("   4. Check network paths/firewalls")
        print("   5. Manual server verification required")

if __name__ == "__main__":
    check_server_status()
