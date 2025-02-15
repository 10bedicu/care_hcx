import json

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRBaseViewSet
from care.utils.notification_handler import send_webpush
from hcx.utils.fhir_v1 import Fhir
from hcx.utils.hcx import Hcx


class CallbacksViewSet(EMRBaseViewSet):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        request=None,
        responses={202: {}},
    )
    @action(detail=False, methods=["POST"], url_path="coverageeligibility/on_check")
    def coverage_eligibility__on_check(self, request, *args, **kwargs):
        response = Hcx().processIncomingRequest(request.data.get("payload"))
        (eligibility_response, eligibility_request) = (
            Fhir().process_coverage_eligibility_check_response(response.get("payload"))
        )

        message = {
            "type": "MESSAGE",
            "from": "coverageelegibility/on_check",
            "message": "success" if not eligibility_response.error else "failed",
        }
        send_webpush(
            username=eligibility_request.created_by.username,
            message=json.dumps(message),
        )

        return Response({}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        request=None,
        responses={202: {}},
    )
    @action(detail=False, methods=["POST"], url_path="preauth/on_submit")
    def preauth__on_submit(self, request, *args, **kwargs):
        response = Hcx().processIncomingRequest(request.data.get("payload"))
        (claim_response, claim_request) = Fhir().process_claim_response(
            response.get("payload")
        )

        message = {
            "type": "MESSAGE",
            "from": "preauth/on_submit",
            "message": "success" if not claim_response.error else "failed",
        }
        send_webpush(
            username=claim_request.created_by.username,
            message=json.dumps(message),
        )

        return Response({}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        request=None,
        responses={202: {}},
    )
    @action(detail=False, methods=["POST"], url_path="claim/on_submit")
    def claim__on_submit(self, request, *args, **kwargs):
        response = Hcx().processIncomingRequest(request.data.get("payload"))
        (claim_response, claim_request) = Fhir().process_claim_response(
            response.get("payload")
        )

        message = {
            "type": "MESSAGE",
            "from": "claim/on_submit",
            "message": "success" if not claim_response.error else "failed",
        }
        send_webpush(
            username=claim_request.created_by.username,
            message=json.dumps(message),
        )

        return Response({}, status=status.HTTP_202_ACCEPTED)
