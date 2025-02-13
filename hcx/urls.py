from rest_framework.routers import DefaultRouter

from care_hcx.hcx.viewsets.callbacks import CallbacksViewSet
from hcx.viewsets.coverage import CoverageViewSet

router = DefaultRouter()

router.register("coverage", CoverageViewSet, basename="hcx-coverage")
router.register("", CallbacksViewSet, basename="hcx-callbacks")


urlpatterns = [
    *router.urls,
]
