from django.apps import AppConfig
from oauth2_provider.settings import oauth2_settings


class AppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"

    def ready(self):
        from rest_framework_simplejwt.tokens import AccessToken

        def jwt_token_generator(request, refresh_token=False):
            access = AccessToken.for_user(request.user)
            return str(access)

        oauth2_settings.ACCESS_TOKEN_GENERATOR = jwt_token_generator
