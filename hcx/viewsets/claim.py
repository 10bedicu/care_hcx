from django_filters import rest_framework as filters

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRDestroyMixin,
    EMRListMixin,
    EMRRetrieveMixin,
)
from hcx.models.claim import Claim
from hcx.resources.claim.spec import ClaimSpec, ClaimStatusChoices


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
    database_model = Claim
    pydantic_model = ClaimSpec
    filterset_class = ClaimFilter
    filter_backends = [filters.DjangoFilterBackend]

    def perform_destroy(self, instance):
        instance.status = ClaimStatusChoices.entered_in_error
        instance.save()

    def perform_create(self, instance):
        super().perform_create(instance)
