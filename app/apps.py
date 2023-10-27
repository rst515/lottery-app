from django.apps import AppConfig


# pylint: disable=function-redefined
class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    # def ready(self):
    #     from .scheduler import scheduler
    #     scheduler.start()
