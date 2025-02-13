from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import EMRBaseViewSet


class CallbacksViewSet(EMRBaseViewSet):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        request=None,
        responses={202: {}},
    )
    @action(detail=False, methods=["POST"], url_path="coverageeligibility/on_check")
    def coverage_eligibility__on_check(self, request, *args, **kwargs):
        print("_------------------------------------------_")
        print(request.data)
        print("_------------------------------------------_")

        return Response({}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        request=None,
        responses={202: {}},
    )
    @action(detail=False, methods=["POST"], url_path="preauth/on_submit")
    def preauth__on_submit(self, request, *args, **kwargs):
        print("_------------------------------------------_")
        print(request.data)
        print("_------------------------------------------_")

        return Response({}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        request=None,
        responses={202: {}},
    )
    @action(detail=False, methods=["POST"], url_path="claim/on_submit")
    def claim__on_submit(self, request, *args, **kwargs):
        print("_------------------------------------------_")
        print(request.data)
        print("_------------------------------------------_")

        return Response({}, status=status.HTTP_202_ACCEPTED)
