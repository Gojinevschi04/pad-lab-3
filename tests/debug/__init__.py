import pytest
from django.conf import settings

pytestmark = pytest.mark.skipif(not settings.DEBUG, reason="Only run in DEBUG mode")
