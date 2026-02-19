from django.core.management.base import BaseCommand

from monitor.models import Server


class Command(BaseCommand):
    def handle(self, *args, **options):
        servers = [
            ("MNL Web Server Main", "192.168.254.7"),
            ("MNL Web Server #2", "192.168.254.10"),
            ("MNL Web HA", "192.168.254.12"),
            ("MNL Online Booking (Main)", "192.168.254.13"),
            ("MNL Online Booking (Backup)", "192.168.254.19"),
            ("MNL Web Server (New - Laravel)", "192.168.254.50"),
            ("HO Web Server Main", "192.168.253.7"),
            ("HO Web Server (New - Laravel)", "192.168.253.15"),
        ]

        created = 0
        updated = 0
        for name, ip in servers:
            obj, was_created = Server.objects.update_or_create(
                name=name,
                defaults={
                    "ip_address": ip,
                    "port": 80,
                    "use_https": False,
                    "path": "/",
                    "http_check": True,
                    "enabled": True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Seed complete. created={created} updated={updated}"))
