#!/usr/bin/env python3
"""
Setup script for Windows Task Scheduler to run daily certificate checks
"""

import os
import sys
import subprocess
from datetime import datetime, time

def setup_daily_task():
    """Create a Windows scheduled task for daily certificate checks"""
    
    # Get the current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    batch_file = os.path.join(script_dir, 'daily_cert_check.bat')
    
    # Task details
    task_name = "ServerWatch_Daily_Certificate_Check"
    task_description = "Daily SSL certificate check for ServerWatch monitoring system"
    
    # Command to create the task
    cmd = [
        'schtasks',
        '/create',
        '/tn', task_name,
        '/tr', f'"{batch_file}"',
        '/sc', 'daily',
        '/st', '08:00',  # Run at 8:00 AM
        '/ru', 'SYSTEM',  # Run as system account
        '/f',  # Force overwrite if task exists
        '/rl', 'HIGHEST',  # Highest privileges
        '/description', task_description
    ]
    
    try:
        print("Creating Windows scheduled task for daily certificate checks...")
        print(f"Task name: {task_name}")
        print(f"Command: {batch_file}")
        print(f"Schedule: Daily at 8:00 AM")
        print()
        
        # Create the task
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Scheduled task created successfully!")
            print()
            print("Task details:")
            print(f"  Name: {task_name}")
            print(f"  Schedule: Daily at 8:00 AM")
            print(f"  Command: {batch_file}")
            print(f"  Run as: SYSTEM")
            print()
            print("You can manage this task in Windows Task Scheduler.")
            print("To run it manually: schtasks /run /tn \"ServerWatch_Daily_Certificate_Check\"")
            print("To delete it: schtasks /delete /tn \"ServerWatch_Daily_Certificate_Check\" /f")
        else:
            print(f"❌ Failed to create scheduled task:")
            print(f"Error: {result.stderr}")
            print()
            print("You may need to run this script as Administrator.")
            return False
            
    except Exception as e:
        print(f"❌ Error creating scheduled task: {e}")
        return False
    
    return True

def test_task():
    """Test the scheduled task by running it once"""
    try:
        print("\nTesting the scheduled task...")
        result = subprocess.run([
            'schtasks', '/run', '/tn', 'ServerWatch_Daily_Certificate_Check'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Task test completed successfully!")
            print("Check the output above for certificate check results.")
        else:
            print(f"❌ Failed to run task test: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error testing task: {e}")

if __name__ == '__main__':
    print("ServerWatch - Daily Certificate Check Setup")
    print("=" * 50)
    
    if setup_daily_task():
        test_task()
        
        print("\n" + "=" * 50)
        print("Setup completed!")
        print("\nNext steps:")
        print("1. The task will run daily at 8:00 AM")
        print("2. Certificate alerts will be created automatically")
        print("3. Check the ServerWatch dashboard for certificate status")
        print("4. Logs will be displayed when the batch file runs")
        print("\nTo modify the schedule, use Windows Task Scheduler.")
    else:
        print("\nSetup failed. Please run this script as Administrator.")
