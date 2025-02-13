from rest_framework.routers import DefaultRouter

from hcx.api.viewsets.claim import ClaimViewSet as ClaimDeprecatedViewSet
from hcx.api.viewsets.communication import (
    CommunicationViewSet as CommunicationDeprecatedViewSet,
)
from hcx.api.viewsets.policy import PolicyViewSet as PolicyDeprecatedViewSet
from hcx.viewsets.callbacks import CallbacksViewSet
from hcx.viewsets.claim import ClaimViewSet
from hcx.viewsets.coverage import CoverageViewSet

router = DefaultRouter()

router.register("coverage", CoverageViewSet, basename="hcx-coverage")
router.register("claim", ClaimViewSet, basename="hcx-claim")
router.register("", CallbacksViewSet, basename="hcx-callbacks")


router.register(
    "policies_deprecated", PolicyDeprecatedViewSet, basename="hcx-policy-deprecated"
)
router.register(
    "claims_deprecated", ClaimDeprecatedViewSet, basename="hcx-claim-deprecated"
)
router.register(
    "communications_deprecated",
    CommunicationDeprecatedViewSet,
    basename="hcx-communication-deprecated",
)


urlpatterns = [
    *router.urls,
]
