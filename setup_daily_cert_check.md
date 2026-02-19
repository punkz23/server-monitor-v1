# SSL Certificate Daily Check - Cron Job Setup
# Add this to your crontab to run daily certificate checks

# Run every day at 8:00 AM
0 8 * * * cd /path/to/django-serverwatch && python manage.py daily_cert_check >> /var/log/cert_check.log 2>&1

# Run every day at 8:00 AM with email notification (if mail is configured)
# 0 8 * * * cd /path/to/django-serverwatch && python manage.py daily_cert_check | mail -s "Daily Certificate Check Report" admin@yourdomain.com

# Run every 6 hours for more frequent checking
# 0 */6 * * * cd /path/to/django-serverwatch && python manage.py daily_cert_check >> /var/log/cert_check.log 2>&1

# Windows Task Scheduler equivalent:
# Create a scheduled task to run daily_cert_check.bat daily at 8:00 AM
