from django.apps import AppConfig
import threading
import time
from datetime import datetime


class MonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitor'
    verbose_name = 'Network Monitor'

    def ready(self):
        """Called when the app is ready"""
        import os
        # Only start the scheduler in the main process (not the reloader)
        # RUN_MAIN is set by Django when it's the actual running process, not the reloader wrapper
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            # Import here to avoid circular imports
            from monitor.services.server_status_monitor import start_automated_monitoring
            
            # Start certificate monitoring scheduler
            self.start_certificate_scheduler()
            
            # Start automated monitoring in production
            # Note: This will run when Django starts up
            try:
                # Only start in production/when explicitly enabled
                if os.environ.get('DJANGO_SETTINGS_MODULE') == 'serverwatch.settings':
                    # Uncomment the line below to enable automatic monitoring on startup
                    start_automated_monitoring()
                    pass
            except Exception as e:
                # Don't let monitoring startup errors break the app
                print(f"Warning: Could not start automated monitoring: {e}")

    def start_certificate_scheduler(self):
        """Start a background thread for certificate checking"""
        def run_scheduler():
            # Simple scheduler without external dependencies
            import time
            
            # Track last check times
            last_6h_check = 0
            last_daily_check = 0
            
            print("Certificate scheduler started:")
            print("- Every 6 hours: Certificate check")
            print("- Daily at 08:00: Full certificate check with alerts")
            
            while True:
                try:
                    current_time = time.time()
                    current_dt = datetime.now()
                    
                    # Check if it's time for 6-hourly check (every 6 hours = 21600 seconds)
                    if current_time - last_6h_check >= 21600:
                        self.check_certificates()
                        last_6h_check = current_time
                    
                    # Check if it's time for daily check (at 08:00)
                    if current_dt.hour == 8 and current_dt.minute < 5 and current_time - last_daily_check >= 86400:
                        self.daily_cert_check()
                        last_daily_check = current_time
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    print(f"Certificate scheduler error: {e}")
                    time.sleep(300)  # Wait 5 minutes on error

        def check_certificates():
            """Check certificates without alerts (frequent checks)"""
            try:
                from monitor.services.certificate_monitor import CertificateMonitor
                monitor = CertificateMonitor()
                results = monitor.check_all_certificates()
                
                success_count = len([r for r in results if r['status'] == 'success'])
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Certificate check: {success_count}/{len(results)} successful")
                
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Certificate check error: {e}")

        def daily_cert_check():
            """Daily certificate check with alerts"""
            try:
                from django.core.management import call_command
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running daily certificate check with alerts...")
                call_command('daily_cert_check')
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Daily certificate check error: {e}")

        # Store methods on the app config for scheduler access
        self.check_certificates = check_certificates
        self.daily_cert_check = daily_cert_check

        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        print("Certificate monitoring scheduler initialized")
