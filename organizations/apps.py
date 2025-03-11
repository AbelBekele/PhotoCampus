from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organizations'
    
    def ready(self):
        """
        Import and register Celery tasks when the app is ready.
        This ensures that Celery knows about our tasks.
        """
        import organizations.tasks  # noqa
