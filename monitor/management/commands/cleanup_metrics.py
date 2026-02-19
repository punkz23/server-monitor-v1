from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from monitor.models import AlertEvent, DbSample, DiskIOSample, DiskUsageSample, NetworkSample, RebootEvent, ResourceSample


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Delete raw metrics older than N days (default: 7).",
        )

    def handle(self, *args, **options):
        days = int(options.get("days") or 7)
        days = max(1, days)
        cutoff = timezone.now() - timedelta(days=days)

        rs = ResourceSample.objects.filter(collected_at__lt=cutoff).delete()[0]
        du = DiskUsageSample.objects.filter(collected_at__lt=cutoff).delete()[0]
        dio = DiskIOSample.objects.filter(collected_at__lt=cutoff).delete()[0]
        net = NetworkSample.objects.filter(collected_at__lt=cutoff).delete()[0]
        db = DbSample.objects.filter(collected_at__lt=cutoff).delete()[0]

        reb_cutoff = timezone.now() - timedelta(days=max(days * 4, 28))
        reb = RebootEvent.objects.filter(boot_time__lt=reb_cutoff).delete()[0]

        evt_cutoff = timezone.now() - timedelta(days=max(days * 4, 28))
        evt = AlertEvent.objects.filter(created_at__lt=evt_cutoff).delete()[0]

        self.stdout.write(
            self.style.SUCCESS(
                f"Cleanup done. cutoff={cutoff.isoformat()} deleted: resources={rs} disk_usage={du} disk_io={dio} network={net} db={db} reboots={reb} events={evt}"
            )
        )
