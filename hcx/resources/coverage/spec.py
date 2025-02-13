from datetime import datetime
from enum import Enum

from pydantic import UUID4, BaseModel, field_validator, model_validator

from care.emr.models.patient import Patient
from care.emr.resources.base import EMRResource
from care.emr.resources.user.spec import UserSpec
from care.facility.models.facility import Facility
from hcx.models.coverage import Coverage, CoverageEligibilityRequest
from hcx.resources.base import PeriodSpec


class BaseCoverageSpec(EMRResource):
    __model__ = Coverage
    __exclude__ = ["beneficiary"]
    id: UUID4 = None


class PolicyHolderTypeChoices(str, Enum):
    organization = "organization"
    related_person = "related_person"
    self = "self"


class PolicyHolderSpec(BaseModel):
    type: PolicyHolderTypeChoices
    name: str | None = None

    @model_validator(mode="after")
    def validate_name(self):
        if (self.type != PolicyHolderTypeChoices.self) and (self.name is None):
            raise ValueError("Name is required for non-self policy holder")
        return self


class SubscriberTypeChoices(str, Enum):
    related_person = "related_person"
    self = "self"


class SubscriberSpec(BaseModel):
    type: SubscriberTypeChoices
    name: str | None = None

    @model_validator(mode="after")
    def validate_name(self):
        if (self.type != SubscriberTypeChoices.self) and (self.name is None):
            raise ValueError("Name is required for non-self policy holder")
        return self


class PayorSpec(BaseModel):
    identifier: str
    name: str


class CoverageStatusChoices(str, Enum):
    active = "active"
    cancelled = "cancelled"
    draft = "draft"
    entered_in_error = "entered-in-error"


class CoverageKindChoices(str, Enum):
    insurance = "insurance"
    self_pay = "self_pay"
    other = "other"


class CoverageRelationshipChoices(str, Enum):
    child = "child"
    parent = "parent"
    spouse = "spouse"
    common = "common"
    other = "other"
    self = "self"
    injured = "injured"


class CoverageSpec(BaseCoverageSpec):
    identifier: str
    subscriber_id: str
    period: PeriodSpec | None = None
    policy_holder: PolicyHolderSpec | None = None
    subscriber: SubscriberSpec | None = None
    relationship: CoverageRelationshipChoices | None = None
    beneficiary: UUID4
    payor: PayorSpec
    status: CoverageStatusChoices
    kind: CoverageKindChoices

    @model_validator(mode="after")
    def validate_relationship(self):
        if (
            self.subscriber
            and self.subscriber["type"] == SubscriberTypeChoices.related_person
        ) and (self.relationship is None):
            raise ValueError("Relationship is required for related person subscriber")
        return self

    @field_validator("beneficiary")
    @classmethod
    def validate_beneficiary(cls, beneficiary):
        if not Patient.objects.filter(external_id=beneficiary).exists():
            raise ValueError("Patient not found")
        return beneficiary

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            obj.beneficiary = Patient.objects.get(external_id=self.beneficiary)


class BaseCoverageEligibilityRequestSpec(EMRResource):
    __model__ = CoverageEligibilityRequest
    __exclude__ = ["facility", "patient", "encounter", "coverage"]
    id: UUID4 = None


class CoverageEligibilityRequestPriorityChoices(str, Enum):
    stat = "stat"
    normal = "normal"
    deferred = "deferred"


class CoverageEligibilityRequestPurposeChoices(str, Enum):
    auth_requirements = "auth-requirements"
    benefits = "benefits"
    discovery = "discovery"
    validation = "validation"


class CoverageEligibilityRequestSpec(BaseCoverageEligibilityRequestSpec):
    priority: CoverageEligibilityRequestPriorityChoices
    purpose: CoverageEligibilityRequestPurposeChoices
    facility: UUID4 | None = None
    coverage: UUID4

    @field_validator("facility")
    @classmethod
    def validate_facility(cls, facility):
        if facility and not Facility.objects.filter(external_id=facility).exists():
            raise ValueError("Facility not found")
        return facility

    @field_validator("coverage")
    @classmethod
    def validate_coverage(cls, coverage):
        if not Coverage.objects.filter(external_id=coverage).exists():
            raise ValueError("Coverage not found")
        return coverage

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            coverage = Coverage.objects.get(external_id=self.coverage)
            obj.coverage = coverage
            obj.patient = coverage.beneficiary
            if self.facility:
                obj.facility = Facility.objects.get(external_id=self.facility)


# TODO: Implement the CoverageEligibilityResponseSpec class
# TODO: Implement the CoverageEligibilityRequestReadSpec class and have last_coverage_eligibility_request as an instance of it


class CoverageReadSpec(CoverageSpec):
    last_coverage_eligibility_request: CoverageEligibilityRequestSpec | None = None

    created_by: UserSpec | None = None
    updated_by: UserSpec | None = None
    created_date: datetime | None = None
    modified_date: datetime | None = None

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id

        last_coverage_eligibility_request = (
            CoverageEligibilityRequest.objects.filter(
                coverage__external_id=obj.external_id
            )
            .order_by("-created_date")
            .first()
        )
        if last_coverage_eligibility_request:
            mapping["last_coverage_eligibility_request"] = (
                CoverageEligibilityRequestSpec.serialize(
                    last_coverage_eligibility_request
                ).to_json()
            )

        if obj.created_by:
            mapping["created_by"] = UserSpec.serialize(obj.created_by).to_json()
        if obj.updated_by:
            mapping["updated_by"] = UserSpec.serialize(obj.updated_by).to_json()
