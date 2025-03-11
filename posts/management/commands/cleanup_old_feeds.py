from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
from photocampus.utils import get_redis_connection
from datetime import timedelta
import logging

from posts.models import FeedEntry

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Cleans up old feed entries older than a specified number of days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Remove entries older than this many days (default: 90)',
        )
        
        parser.add_argument(
            '--inactive-only', 
            action='store_true',
            help='Only clean up feeds for users who have been inactive for the specified days',
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only count what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options.get('days')
        inactive_only = options.get('inactive_only')
        dry_run = options.get('dry_run')
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f"Cleaning up feed entries older than {days} days (before {cutoff_date})")
        
        # Build query for deletion
        entries_query = FeedEntry.objects.filter(created_at__lt=cutoff_date)
        
        # Add inactive user filter if requested
        if inactive_only:
            inactive_users = User.objects.filter(last_login__lt=cutoff_date)
            self.stdout.write(f"Restricting to {inactive_users.count()} inactive users")
            entries_query = entries_query.filter(user__in=inactive_users)
        
        # Count before deleting
        count = entries_query.count()
        self.stdout.write(f"Found {count} feed entries to clean up")
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Dry run completed. Would have deleted {count} entries."))
            return
        
        # Perform deletion in database
        with transaction.atomic():
            deleted, _ = entries_query.delete()
        
        self.stdout.write(self.style.SUCCESS(f"Successfully deleted {deleted} old feed entries from database"))
        
        # Also clean up Redis entries
        if not inactive_only:  # Skip Redis cleanup if only cleaning inactive users
            self.stdout.write("Cleaning up Redis feed entries...")
            redis_conn = get_redis_connection("default")
            
            # For Redis, we rely on TTL for automatic cleanup, but we can force expire
            # old keys for users that had DB entries deleted
            user_ids = FeedEntry.objects.values_list('user_id', flat=True).distinct()
            
            for user_id in user_ids:
                key = f"user:feed:{user_id}"
                # Remove old entries
                try:
                    entries = redis_conn.zrange(key, 0, -1, withscores=True)
                    for entry_json, score in entries:
                        if b'"created_at":' in entry_json:
                            import json
                            entry = json.loads(entry_json)
                            created_timestamp = entry.get('created_at', 0)
                            if created_timestamp < cutoff_date.timestamp():
                                redis_conn.zrem(key, entry_json)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error cleaning Redis for user {user_id}: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS("Redis cleanup completed"))
        
        self.stdout.write(self.style.SUCCESS("Feed cleanup completed successfully"))