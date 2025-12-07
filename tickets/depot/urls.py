from rest_framework.routers import DefaultRouter

from tickets.depot.views import TripViewSet

app_name = "tickets-depot"

router = DefaultRouter()
router.register(r"trips", TripViewSet, basename="trip")

urlpatterns = router.urls
