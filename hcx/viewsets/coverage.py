import json

from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRDestroyMixin,
    EMRListMixin,
    EMRRetrieveMixin,
)
from hcx.models.coverage import Coverage
from hcx.resources.coverage.spec import (
    CoverageEligibilityRequestSpec,
    CoverageReadSpec,
    CoverageSpec,
    CoverageStatusChoices,
)
from hcx.utils.fhir_v1 import Fhir
from hcx.utils.hcx import Hcx
from hcx.utils.hcx.operations import HcxOperations


class CoverageFilter(filters.FilterSet):
    beneficiary = filters.UUIDFilter(field_name="beneficiary__external_id")


class CoverageViewSet(
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRDestroyMixin,
    EMRBaseViewSet,
):
    database_model = Coverage
    pydantic_model = CoverageSpec
    pydantic_read_model = CoverageReadSpec
    filterset_class = CoverageFilter
    filter_backends = [filters.DjangoFilterBackend]

    def perform_destroy(self, instance):
        instance.status = CoverageStatusChoices.entered_in_error
        instance.save()

    @extend_schema(
        request=CoverageEligibilityRequestSpec,
        responses={200: CoverageReadSpec},
    )
    @action(detail=True, methods=["POST"])
    def check_eligibility(self, request, *args, **kwargs):
        coverage = self.get_object()

        instance = CoverageEligibilityRequestSpec(
            **request.data, coverage=coverage.external_id
        ).de_serialize()
        instance.created_by = request.user
        instance.save()

        fhir_data = Fhir().create_coverage_eligibility_request_bundle(instance)

        response = Hcx().generateOutgoingHcxCall(
            fhirPayload=json.loads(fhir_data.json()),
            operation=HcxOperations.COVERAGE_ELIGIBILITY_CHECK,
            recipientCode=coverage.payor["identifier"],
        )

        return Response(
            {
                "response": response,
                "fhir": json.loads(fhir_data.json()),
            }
        )

    @action(detail=False, methods=["GET"])
    def payors(self, request):
        payors = Hcx().searchRegistry("roles", "payor")["participants"]

        result = filter(lambda payor: payor["status"] == "Active", payors)

        if query := request.query_params.get("query"):
            query = query.lower()
            result = filter(
                lambda payor: (
                    query in payor["participant_name"].lower()
                    or query in payor["participant_code"].lower()
                ),
                result,
            )

        response = [
            {
                "name": payor["participant_name"],
                "code": payor["participant_code"],
            }
            for payor in result
        ]

        return Response(response, status=status.HTTP_200_OK)
