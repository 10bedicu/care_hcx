from datetime import datetime
from enum import Enum

from pydantic import UUID4, BaseModel, field_validator, model_validator

from care.emr.fhir.schema.base import Coding
from care.emr.models.condition import Condition
from care.emr.models.encounter import Encounter
from care.emr.models.file_upload import FileUpload
from care.emr.resources.base import EMRResource
from care.emr.resources.condition.spec import ConditionSpec
from care.emr.resources.file_upload.spec import FileUploadRetrieveSpec
from care.emr.resources.user.spec import UserSpec
from care.users.models import User
from hcx.models.claim import Claim, ClaimResponse
from hcx.models.coverage import Coverage
from hcx.resources.base import PeriodSpec
from hcx.resources.coverage.spec import CoverageReadSpec


class ClaimResponseOutcomeChoices(str, Enum):
    queued = "queued"
    complete = "complete"
    error = "error"
    partial = "partial"


class ClaimResponseSpec(EMRResource):
    __model__ = ClaimResponse
    __exclude__ = ["request"]
    id: UUID4 = None
    request: UUID4
    outcome: ClaimResponseOutcomeChoices
    error: dict | None = None
    disposition: str | None = None
    item: dict | None = None
    add_item: dict | None = None
    total: dict | None = None
    total_amount: float | None = None

    created_date: datetime | None = None
    modified_date: datetime | None = None

    @field_validator("request")
    @classmethod
    def validate_request(cls, request):
        if not Claim.objects.filter(external_id=request).exists():
            raise ValueError("Claim not found")
        return request

    def perform_extra_deserialization(self, is_update, obj):
        claim = Claim.objects.get(external_id=self.request)
        obj.request = claim

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id


class BaseClaimSpec(EMRResource):
    __model__ = Claim
    __exclude__ = ["patient", "facility", "encounter"]
    id: UUID4 = None


class ClaimTypeChoices(str, Enum):
    institutional = "institutional"
    oral = "oral"
    pharmacy = "pharmacy"
    professional = "professional"
    vision = "vision"


class ClaimUseChoices(str, Enum):
    claim = "claim"
    preauthorization = "preauthorization"
    predetermination = "predetermination"


class ClaimStatusChoices(str, Enum):
    active = "active"
    cancelled = "cancelled"
    draft = "draft"
    entered_in_error = "entered-in-error"


class ClaimPriorityChoices(str, Enum):
    stat = "stat"
    normal = "normal"
    deferred = "deferred"


class ClaimInsuranceSpec(BaseModel):
    sequence: int
    focal: bool = False
    coverage: UUID4

    @field_validator("coverage")
    @classmethod
    def validate_coverage(cls, coverage):
        if not Coverage.objects.filter(external_id=coverage).exists():
            raise ValueError("Coverage not found")
        return coverage


class ClaimRelatedRelationshipChoices(str, Enum):
    enhancement = "enhancement"
    settlement = "settlement"
    prior = "prior"
    associated = "associated"


class ClaimRelatedSpec(BaseModel):
    claim: UUID4
    relationship: ClaimRelatedRelationshipChoices

    @field_validator("claim")
    @classmethod
    def validate_claim(cls, claim):
        if not Claim.objects.filter(external_id=claim).exists():
            raise ValueError("Claim not found")
        return claim


class ClaimCareTeamSpec(BaseModel):
    sequence: int
    provider: UUID4
    responsible: bool = False

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, provider):
        if not User.objects.filter(external_id=provider).exists():
            raise ValueError("Provider not found")
        return provider


class ClaimDiagnosisSpec(BaseModel):
    sequence: int
    diagnosis: UUID4

    @field_validator("diagnosis")
    @classmethod
    def validate_diagnosis(cls, diagnosis):
        if not Condition.objects.filter(external_id=diagnosis).exists():
            raise ValueError("Diagnosis not found")
        return diagnosis


class ClaimProcedureSpec(BaseModel):
    sequence: int
    procedure: UUID4
    date: datetime = None

    @field_validator("procedure")
    @classmethod
    def validate_procedure(cls, procedure):
        # if not Procedure.objects.filter(external_id=procedure).exists():
        #     raise ValueError("Procedure not found")
        return procedure


class ClaimSupportingInfoSpec(BaseModel):
    sequence: int
    category: Coding | None = None
    value: str | None = None
    attachment: UUID4 | None = None

    @field_validator("attachment")
    @classmethod
    def validate_attachment(cls, attachment):
        if (
            attachment
            and not FileUpload.objects.filter(external_id=attachment).exists()
        ):
            raise ValueError("Attachment not found")
        return attachment

    @model_validator(mode="after")
    def validate_value_or_attachment(self):
        if not self.value and not self.attachment:
            raise ValueError("Either value or attachment is required")
        return self


class ClaimItemSpec(BaseModel):
    sequence: int
    care_team_sequence: list[int] = []
    diagnosis_sequence: list[int] = []
    procedure_sequence: list[int] = []
    information_sequence: list[int] = []
    category: Coding | None = None
    product_or_service: Coding
    quantity: int
    unit_price: float
    patient_paid: float = 0
    tax: float = 0
    net: float = 0

    @model_validator(mode="after")
    def validate_net(self):
        self.net = (self.unit_price * self.quantity) + self.tax
        return self


class ClaimSpec(BaseClaimSpec):
    type: ClaimTypeChoices
    use: ClaimUseChoices
    status: ClaimStatusChoices
    priority: ClaimPriorityChoices
    encounter: UUID4
    insurance: list[ClaimInsuranceSpec]
    billable_period: PeriodSpec | None = None
    related: list[ClaimRelatedSpec] = []
    care_team: list[ClaimCareTeamSpec] = []
    diagnosis: list[ClaimDiagnosisSpec] = []
    procedure: list[ClaimProcedureSpec] = []
    supporting_info: list[ClaimSupportingInfoSpec] = []
    item: list[ClaimItemSpec] = []
    patient_paid: float = 0
    total: float = 0

    latest_response: ClaimResponseSpec | None = None

    created_date: datetime | None = None
    modified_date: datetime | None = None

    @model_validator(mode="after")
    def validate_price(self):
        self.total = sum([item.net for item in self.item])
        self.patient_paid = sum([item.patient_paid for item in self.item])
        return self

    @field_validator("encounter")
    @classmethod
    def validate_encounter(cls, encounter):
        if not Encounter.objects.filter(external_id=encounter).exists():
            raise ValueError("Encounter not found")
        return encounter

    def perform_extra_deserialization(self, is_update, obj):
        if not is_update:
            encounter = Encounter.objects.get(external_id=self.encounter)

            obj.encounter = encounter
            obj.patient = encounter.patient
            obj.facility = encounter.facility

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id

        response = (
            ClaimResponse.objects.filter(request=obj).order_by("-created_date").first()
        )
        if response:
            mapping["latest_response"] = ClaimResponseSpec.serialize(response).to_json()


class ClaimRetrieveSpec(ClaimSpec):
    created_by: UserSpec | None = None
    updated_by: UserSpec | None = None

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):  # noqa
        super().perform_extra_serialization(mapping, obj)

        if obj.insurance:
            mapping["insurance"] = []
            for insurance in obj.insurance:
                parsed = {**insurance}
                coverage = Coverage.objects.get(external_id=insurance.get("coverage"))
                parsed["coverage"] = CoverageReadSpec.serialize(coverage).to_json()
                mapping["insurance"].append(parsed)

        if obj.related:
            mapping["related"] = []
            for related in obj.related:
                parsed = {**related}
                claim = Claim.objects.get(external_id=related.get("claim"))
                parsed["claim"] = ClaimSpec.serialize(claim).to_json()
                mapping["related"].append(parsed)

        if obj.care_team:
            mapping["care_team"] = []
            for care_team in obj.care_team:
                parsed = {**care_team}
                user = User.objects.get(external_id=care_team.get("provider"))
                parsed["provider"] = UserSpec.serialize(user).to_json()
                mapping["care_team"].append(parsed)

        if obj.diagnosis:
            mapping["diagnosis"] = []
            for diagnosis in obj.diagnosis:
                parsed = {**diagnosis}
                condition = Condition.objects.get(
                    external_id=diagnosis.get("diagnosis")
                )
                parsed["diagnosis"] = ConditionSpec.serialize(condition).to_json()
                mapping["diagnosis"].append(parsed)

        if obj.procedure:
            mapping["procedure"] = []
            for procedure in obj.procedure:
                parsed = {**procedure}
                # procedure = Procedure.objects.get(external_id=procedure.get("procedure"))
                # parsed["procedure"] = ProcedureReadSpec.serialize(procedure).to_json()
                mapping["procedure"].append(parsed)

        if obj.supporting_info:
            mapping["supporting_info"] = []
            for supporting_info in obj.supporting_info:
                parsed = {**supporting_info}
                if supporting_info.get("attachment"):
                    attachment = FileUpload.objects.get(
                        external_id=supporting_info.get("attachment")
                    )
                    parsed["attachment"] = FileUploadRetrieveSpec.serialize(
                        attachment
                    ).to_json()
                mapping["supporting_info"].append(parsed)

        if obj.created_by:
            mapping["created_by"] = UserSpec.serialize(obj.created_by).to_json()
        if obj.updated_by:
            mapping["updated_by"] = UserSpec.serialize(obj.updated_by).to_json()
