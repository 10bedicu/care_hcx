import json

from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework import filters as drf_filters
from rest_framework.decorators import action
from rest_framework.response import Response

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRDestroyMixin,
    EMRListMixin,
    EMRRetrieveMixin,
)
from care.emr.models.condition import Condition
from hcx.models.claim import ClaimRequest
from hcx.models.coverage import Coverage
from hcx.resources.claim.spec import (
    ClaimRetrieveSpec,
    ClaimSpec,
    ClaimStatusChoices,
    ClaimUseChoices,
)
from hcx.utils.fhir_v1 import Fhir
from hcx.utils.hcx import Hcx
from hcx.utils.hcx.operations import HcxOperations


class ClaimFilter(filters.FilterSet):
    encounter = filters.UUIDFilter(field_name="encounter__external_id")
    patient = filters.UUIDFilter(field_name="patient__external_id")
    facility = filters.UUIDFilter(field_name="facility__external_id")


class ClaimViewSet(
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRDestroyMixin,
    EMRBaseViewSet,
):
    database_model = ClaimRequest
    pydantic_model = ClaimSpec
    pydantic_retrieve_model = ClaimRetrieveSpec
    filter_backends = [filters.DjangoFilterBackend, drf_filters.OrderingFilter]
    filterset_class = ClaimFilter
    ordering_fields = [
        "created_date",
        "modified_date",
    ]

    def perform_create(self, instance):
        diagnoses = Condition.objects.filter(encounter=instance.encounter)

        instance.diagnosis = [
            {"sequence": i, "diagnosis": str(diagnosis.external_id)}
            for i, diagnosis in enumerate(diagnoses, start=1)
        ]
        super().perform_create(instance)

    def perform_destroy(self, instance):
        instance.status = ClaimStatusChoices.entered_in_error
        instance.save()
        super().perform_destroy(instance)

    @extend_schema(
        request=None,
        responses={200: {}},
    )
    @action(detail=True, methods=["POST"])
    def submit(self, request, *args, **kwargs):
        claim = self.get_object()

        coverage = Coverage.objects.filter(
            external_id=claim.insurance[0]["coverage"]
        ).first()

        fhir_data = Fhir().create_claim_bundle(claim)

        response = Hcx().generateOutgoingHcxCall(
            fhirPayload=json.loads(fhir_data.json()),
            operation=(
                HcxOperations.CLAIM_SUBMIT
                if claim.use == ClaimUseChoices.claim
                else HcxOperations.PRE_AUTH_SUBMIT
            ),
            recipientCode=coverage.payor.get("identifier"),
        )

        return Response(
            {
                "response": response,
                "fhir": json.loads(fhir_data.json()),
            }
        )
