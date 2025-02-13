from django.shortcuts import HttpResponse
from django.urls import path
from rest_framework.routers import DefaultRouter

from care_hcx.hcx.api.viewsets.claim import ClaimViewSet
from care_hcx.hcx.api.viewsets.communication import CommunicationViewSet
from care_hcx.hcx.api.viewsets.gateway import HcxGatewayViewSet
from care_hcx.hcx.api.viewsets.listener import CoverageElibilityOnCheckView
from care_hcx.hcx.api.viewsets.policy import PolicyViewSet
from hcx.viewsets.coverage import CoverageViewSet


def healthy(request):
    return HttpResponse("Hello from CARE HCX")


router = DefaultRouter()

router.register("coverage", CoverageViewSet, basename="hcx-coverage")


router.register("policy", PolicyViewSet, basename="hcx-policy")
router.register("claim", ClaimViewSet, basename="hcx-claim")
router.register("communication", CommunicationViewSet, basename="hcx-communication")
router.register("", HcxGatewayViewSet, basename="hcx-gateway")


# path(
#     "coverageeligibility/on_check",
#     CoverageElibilityOnCheckView.as_view(),
#     name="hcx_coverage_eligibility_on_check",
# ),
# path(
#     "preauth/on_submit",
#     PreAuthOnSubmitView.as_view(),
#     name="hcx_pre_auth_on_submit",
# ),
# path(
#     "claim/on_submit",
#     ClaimOnSubmitView.as_view(),
#     name="hcx_claim_on_submit",
# ),
# path(
#     "communication/request",
#     CommunicationRequestView.as_view(),
#     name="hcx_communication_on_request",
# ),

urlpatterns = [
    path("health", healthy),
    path(
        "coverageeligibility/on_check",
        CoverageElibilityOnCheckView.as_view(),
        name="hcx_coverage_eligibility_on_check",
    ),
    *router.urls,
]
