from django.apps import AppConfig


class ViewerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'viewer'
def ready(self):
    import viewer.signals  # Remplace "ton_app" par le nom de ton application
