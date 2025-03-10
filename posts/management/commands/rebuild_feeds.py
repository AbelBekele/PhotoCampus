from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.conf import settings
import time
import logging

from posts.tasks import refresh_feed_for_user

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Rebuilds feed caches for all users or a specific subset'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Rebuild feed for a specific user ID only',
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Number of users to process in each batch (default: 500)',
        )
        
        parser.add_argument(
            '--active-only', 
            action='store_true',
            help='Only rebuild for users who have been active in the last 30 days',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        batch_size = options.get('batch_size')
        active_only = options.get('active_only')
        
        start_time = time.time()
        
        # If user ID is provided, process only that user
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f"Rebuilding feed for user: {user.username} (ID: {user.id})")
                refresh_feed_for_user(user.id)
                self.stdout.write(self.style.SUCCESS(f"Successfully rebuilt feed for {user.username}"))
                return
            except User.DoesNotExist:
                raise CommandError(f"User with ID {user_id} does not exist")
        
        # Filter users if active_only
        if active_only:
            from django.utils import timezone
            from datetime import timedelta
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            # Users who have been active in the last 30 days
            user_queryset = User.objects.filter(
                Q(last_login__gte=thirty_days_ago) |
                Q(posts__created_at__gte=thirty_days_ago) |
                Q(comments__created_at__gte=thirty_days_ago) |
                Q(likes__created_at__gte=thirty_days_ago) |
                Q(shares__created_at__gte=thirty_days_ago)
            ).distinct()
            
            self.stdout.write(f"Rebuilding feeds for {user_queryset.count()} active users")
        else:
            user_queryset = User.objects.all()
            self.stdout.write(f"Rebuilding feeds for all {user_queryset.count()} users")
        
        # Process users in batches to avoid memory issues
        paginator = Paginator(user_queryset.order_by('id'), batch_size)
        
        for page_num in range(1, paginator.num_pages + 1):
            self.stdout.write(f"Processing batch {page_num} of {paginator.num_pages}")
            user_batch = paginator.page(page_num).object_list
            
            for user in user_batch:
                self.stdout.write(f"  Rebuilding feed for user: {user.username} (ID: {user.id})")
                try:
                    refresh_feed_for_user(user.id)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error rebuilding feed for {user.username}: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS(f"Completed batch {page_num}"))
        
        elapsed_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f"Feed rebuild complete. Total time: {elapsed_time:.2f} seconds"))