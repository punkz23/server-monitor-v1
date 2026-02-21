import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
django.setup()

from monitor.models import Server

def configure_directory_watch():
    # 1. onlinebooking -> /var/www/
    Server.objects.filter(name='onlinebooking').update(watch_directory='/var/www')
    print("Configured onlinebooking to watch /var/www")

    # 2. server-hp4k6q2 -> /var/www/html/
    Server.objects.filter(name='server-hp4k6q2').update(watch_directory='/var/www/html')
    print("Configured server-hp4k6q2 to watch /var/www/html")

    # 3. webserver3 -> /var/www/
    Server.objects.filter(name='webserver3').update(watch_directory='/var/www')
    print("Configured webserver3 to watch /var/www")

    # 4. ho-w1 -> /var/www/html/
    Server.objects.filter(name='ho-w1').update(watch_directory='/var/www/html')
    print("Configured ho-w1 to watch /var/www/html")

    # 5. w1 -> /var/www/
    Server.objects.filter(name='w1').update(watch_directory='/var/www')
    print("Configured w1 to watch /var/www")

if __name__ == '__main__':
    configure_directory_watch()
