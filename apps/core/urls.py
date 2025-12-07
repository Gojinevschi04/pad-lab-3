from rest_framework.routers import DefaultRouter

from .views import TicketViewSet

app_name = "tickets-core"

router = DefaultRouter()
router.register(r"tickets", TicketViewSet, basename="ticket")

urlpatterns = router.urls
