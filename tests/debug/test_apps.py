from django.apps import apps

from tickets.debug.apps import DebugConfig


def test_debug_app_config():
    app_config = apps.get_app_config("debug")
    assert isinstance(app_config, DebugConfig)
    assert app_config.name == "tickets.debug"
    assert app_config.default_auto_field == "django.db.models.BigAutoField"
