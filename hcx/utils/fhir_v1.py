from datetime import UTC, datetime
from functools import reduce, wraps
from uuid import uuid4

from fhir.resources.R4B.address import Address
from fhir.resources.R4B.attachment import Attachment
from fhir.resources.R4B.bundle import Bundle, BundleEntry
from fhir.resources.R4B.claim import (
    Claim,
    ClaimCareTeam,
    ClaimDiagnosis,
    ClaimInsurance,
    ClaimItem,
    ClaimPayee,
    ClaimProcedure,
    ClaimRelated,
    ClaimSupportingInfo,
)
from fhir.resources.R4B.claimresponse import ClaimResponse
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.coding import Coding
from fhir.resources.R4B.condition import Condition
from fhir.resources.R4B.contactpoint import ContactPoint
from fhir.resources.R4B.coverage import Coverage
from fhir.resources.R4B.coverageeligibilityrequest import (
    CoverageEligibilityRequest,
    CoverageEligibilityRequestInsurance,
)
from fhir.resources.R4B.coverageeligibilityresponse import CoverageEligibilityResponse
from fhir.resources.R4B.humanname import HumanName
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.meta import Meta
from fhir.resources.R4B.money import Money
from fhir.resources.R4B.organization import Organization
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.period import Period
from fhir.resources.R4B.practitioner import Practitioner
from fhir.resources.R4B.quantity import Quantity
from fhir.resources.R4B.reference import Reference
from fhir.resources.R4B.resource import Resource

from care.emr.models.base import EMRBaseModel
from care.emr.models.condition import Condition as ConditionModel
from care.emr.models.file_upload import FileUpload
from care.emr.models.patient import Patient as PatientModel
from care.emr.resources.base import Coding as CodingSpec
from care.facility.models import Facility as FacilityModel
from care.users.models import User as UserModel
from hcx.models.claim import ClaimRequest as ClaimRequestModel
from hcx.models.claim import ClaimResponse as ClaimResponseModel
from hcx.models.coverage import Coverage as CoverageModel
from hcx.models.coverage import (
    CoverageEligibilityRequest as CoverageEligibilityRequestModel,
)
from hcx.models.coverage import (
    CoverageEligibilityResponse as CoverageEligibilityResponseModel,
)
from hcx.settings import plugin_settings as settings

CARE_IDENTIFIER_SYSTEM = settings.BACKEND_DOMAIN


class Fhir:
    def __init__(self):
        self._profiles = {}
        self._resource_id_url_map = {}

    @staticmethod
    def cache_profiles(resource_type: str):
        def decorator(func):
            @wraps(func)
            def wrapper(self, model_instance: EMRBaseModel, *args, **kwargs):
                if not hasattr(model_instance, "external_id"):
                    err = f"{model_instance.__class__.__name__} does not have 'external_id' attribute"
                    raise AttributeError(err)

                cache_key_prefix = kwargs.get("cache_key_prefix", "")
                cache_key_id = str(model_instance.external_id)
                cache_key_suffix = kwargs.get("cache_key_suffix", "")
                cache_key = f"{resource_type}/{cache_key_prefix}{cache_key_id}{cache_key_suffix}"

                if cache_key in self._profiles:
                    return self._profiles[cache_key]

                result = func(self, model_instance, *args, **kwargs)

                self._profiles[cache_key] = result
                self._resource_id_url_map[cache_key] = uuid4()
                return result

            return wrapper

        return decorator

    def cached_profiles(self):
        return list(
            filter(lambda profile: profile is not None, self._profiles.values())
        )

    def _reference_url(self, resource: Resource = None):
        if resource is None:
            return ""

        key = f"{resource.resource_type}/{resource.id}"
        return f"urn:uuid:{self._resource_id_url_map.get(key, uuid4())}"

    def _reference(self, resource: Resource = None):
        if resource is None:
            return None

        return Reference(reference=self._reference_url(resource))

    @cache_profiles(Patient.get_resource_type())
    def _patient(self, patient: PatientModel):
        id = str(patient.external_id)

        return Patient(
            id=id,
            meta=Meta(
                profile=["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Patient"],
            ),
            identifier=[
                Identifier(
                    value=id,
                    system=f"{CARE_IDENTIFIER_SYSTEM}/patient",
                    type=CodeableConcept(
                        coding=[
                            Coding(
                                system="http://terminology.hl7.org/CodeSystem/v2-0203",
                                code="MR",
                                display="Medical Record Number",
                            )
                        ]
                    ),
                )
            ],
            name=[HumanName(text=patient.name)],
            telecom=[
                *(
                    [ContactPoint(system="phone", value=patient.phone_number)]
                    if patient.phone_number
                    else []
                ),
                *(
                    [ContactPoint(system="phone", value=patient.emergency_phone_number)]
                    if patient.emergency_phone_number
                    else []
                ),
            ],
            gender=patient.gender,
            birthDate=patient.date_of_birth.isoformat()
            if patient.date_of_birth
            else None,
            address=[
                Address(
                    line=[patient.address],
                    postalCode=patient.pincode,
                    country="IN",
                ),
                Address(
                    line=[patient.permanent_address],
                    postalCode=patient.pincode,
                    country="IN",
                ),
            ],
        )

    @cache_profiles(Practitioner.get_resource_type())
    def _practitioner(self, user: UserModel):
        id = str(user.external_id)

        return Practitioner(
            id=id,
            identifier=[
                Identifier(
                    value=id,
                    type=CodeableConcept(
                        coding=[
                            Coding(
                                system="http://terminology.hl7.org/CodeSystem/v2-0203",
                                code="PRN",
                                display="Provider number",
                            )
                        ]
                    ),
                )
            ],
            name=[HumanName(text=user.full_name)],
            telecom=[
                *(
                    [ContactPoint(system="phone", value=user.phone_number)]
                    if user.phone_number
                    else []
                ),
                *(
                    [ContactPoint(system="email", value=user.email)]
                    if user.email
                    else []
                ),
            ],
            gender=user.gender,
            birthDate=user.date_of_birth,
        )

    @cache_profiles(Organization.get_resource_type())
    def _organization(self, facility: FacilityModel):
        id = str(facility.external_id)

        return Organization(
            id=id,
            identifier=[
                Identifier(
                    system=f"{CARE_IDENTIFIER_SYSTEM}/facility",
                    value=id,
                    type=CodeableConcept(
                        coding=[
                            Coding(
                                system="http://terminology.hl7.org/CodeSystem/v2-0203",
                                code="FI",
                                display="Facility ID",
                            )
                        ]
                    ),
                )
            ],
            type=[
                CodeableConcept(
                    coding=[
                        Coding(
                            system="http://terminology.hl7.org/CodeSystem/organization-type",
                            code="prov",
                            display="Healthcare Provider",
                        )
                    ]
                )
            ],
            name=facility.name,
            telecom=[
                *(
                    [ContactPoint(system="phone", value=facility.phone_number)]
                    if facility.phone_number
                    else []
                )
            ],
            address=[
                Address(
                    line=[facility.address],
                    postalCode=facility.pincode,
                    country="IN",
                )
            ]
            if facility.address
            else None,
        )

    @cache_profiles(Condition.get_resource_type())
    def _condition(self, condition: ConditionModel):
        id = str(condition.external_id)

        return Condition(
            id=id,
            # identifier=[Identifier(value=id)],
            # category=[
            #     CodeableConcept(
            #         coding=[
            #             Coding(
            #                 system="http://terminology.hl7.org/CodeSystem/condition-category",
            #                 code=condition.category,
            #                 display=condition.category,
            #             )
            #         ],
            #     )
            # ],
            # verificationStatus=CodeableConcept(
            #     coding=[
            #         Coding(
            #             system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
            #             code=condition.verification_status,
            #             display=condition.verification_status,
            #         )
            #     ]
            # ),
            code=CodeableConcept(
                coding=[Coding(**condition.code)],
            ),
            subject=self._reference(self._patient(condition.patient)),
        )

    def _attachment(self, attachment: FileUpload):
        id = str(attachment.external_id)
        url = attachment.files_manager.read_signed_url(attachment)

        return Attachment(
            id=id,
            title=attachment.name,
            url=url,
        )

    def _coding(self, coding: CodingSpec | None):
        if coding is None:
            return None

        return Coding(
            code=coding.code,
            display=coding.display,
            system=coding.system,
        )

    def _coding_to_codable_concept(self, coding: CodingSpec | None):
        if coding is None:
            return None

        return CodeableConcept(coding=[self._coding(coding)])

    @cache_profiles(Coverage.get_resource_type())
    def _coverage(self, coverage: CoverageModel):
        id = str(coverage.external_id)

        return Coverage(
            id=id,
            meta=Meta(
                profile=[
                    "https://ig.hcxprotocol.io/v0.7.1/StructureDefinition-Coverage.html"
                ],
            ),
            identifier=[Identifier(value=id)],
            subscriberId=coverage.subscriber_id,
            period=Period(**coverage.period) if coverage.period else None,
            subscriber=None,
            policyHolder=None,
            relationship=CodeableConcept(
                coding=[
                    Coding(
                        system="http://terminology.hl7.org/CodeSystem/subscriber-relationship",
                        code=coverage.relationship,
                    )
                ]
            )
            if coverage.relationship
            else None,
            beneficiary=self._reference(self._patient(coverage.beneficiary)),
            payor=[
                self._reference(
                    self._organization(
                        FacilityModel(
                            id=coverage.payor.get("identifier"),
                            name=coverage.payor.get("name"),
                        )
                    )
                )
            ],
            status=coverage.status,
        )

    def _coverage_eligibility_request(self, request: CoverageEligibilityRequestModel):
        id = str(request.external_id)

        return CoverageEligibilityRequest(
            id=id,
            meta=Meta(
                profile=[
                    "https://ig.hcxprotocol.io/v0.7.1/StructureDefinition-CoverageEligibilityRequest.html"
                ],
            ),
            identifier=[Identifier(value=id)],
            status=request.coverage.status,
            priority=CodeableConcept(
                coding=[
                    Coding(
                        system="http://terminology.hl7.org/CodeSystem/processpriority",
                        code=request.priority,
                    )
                ]
            ),
            purpose=[request.purpose],
            created=request.created_date.isoformat(),
            patient=self._reference(self._patient(request.patient)),
            enterer=self._reference(self._practitioner(request.created_by)),
            provider=self._reference(self._organization(request.facility))
            if request.facility
            else None,
            insurer=self._reference(
                self._organization(
                    FacilityModel(
                        id=request.coverage.payor.get("identifier"),
                        name=request.coverage.payor.get("name"),
                    )
                )
            ),
            insurance=[
                CoverageEligibilityRequestInsurance(
                    coverage=self._reference(self._coverage(request.coverage))
                )
            ],
        )

    def _claim(self, claim: ClaimRequestModel):
        id = str(claim.external_id)
        coverage = CoverageModel.objects.filter(
            external_id=claim.insurance[0].get("coverage")
        ).first()

        return Claim(
            id=id,
            meta=Meta(
                profile=[
                    "https://ig.hcxprotocol.io/v0.7.1/StructureDefinition-Claim.html"
                ],
            ),
            identifier=[Identifier(value=id)],
            status=claim.status,
            type=CodeableConcept(
                coding=[
                    Coding(
                        system="http://terminology.hl7.org/CodeSystem/claim-type",
                        code=claim.type,
                    )
                ]
            ),
            use=claim.use,
            priority=CodeableConcept(
                coding=[
                    Coding(
                        system="http://terminology.hl7.org/CodeSystem/processpriority",
                        code=claim.priority,
                    )
                ]
            ),
            created=claim.created_date.isoformat(),
            billablePeriod=Period(**claim.billable_period)
            if claim.billable_period
            else None,
            patient=self._reference(self._patient(claim.patient)),
            enterer=self._reference(self._practitioner(claim.created_by)),
            provider=self._reference(self._organization(claim.facility)),
            insurer=self._reference(
                self._organization(
                    FacilityModel(
                        id=coverage.payor.get("identifier"),
                        name=coverage.payor.get("name"),
                    )
                )
            ),
            insurance=[
                ClaimInsurance(
                    sequence=insurance.get("sequence"),
                    focal=insurance.get("focal"),
                    coverage=self._reference(
                        self._coverage(
                            CoverageModel.objects.filter(
                                external_id=insurance.get("coverage")
                            ).first()
                        )
                    ),
                )
                for insurance in claim.insurance
            ],
            payee=ClaimPayee(
                type=CodeableConcept(
                    coding=[
                        Coding(
                            system="http://terminology.hl7.org/CodeSystem/payeetype",
                            code="provider",
                        )
                    ],
                ),
                party=self._reference(self._organization(claim.facility)),
            ),
            related=[
                ClaimRelated(
                    claim=self._reference(self._claim(related.get("claim"))),
                    relationship=CodeableConcept(
                        coding=[
                            Coding(
                                system="http://hl7.org/fhir/ValueSet/related-claim-relationship",
                                code=related.get("relationship"),
                            )
                        ]
                    ),
                )
                for related in claim.related
            ]
            if claim.related
            else None,
            careTeam=[
                ClaimCareTeam(
                    sequence=care_team.get("sequence"),
                    provider=self._reference(
                        self._practitioner(
                            UserModel.objects.filter(
                                external_id=care_team.get("provider")
                            ).first()
                        )
                    ),
                    responsible=care_team.get("responsible"),
                )
                for care_team in claim.care_team
            ]
            if claim.care_team
            else [
                ClaimCareTeam(
                    sequence=1,
                    provider=self._reference(self._organization(claim.facility)),
                    responsible=True,
                )
            ],
            diagnosis=[
                ClaimDiagnosis(
                    sequence=diagnosis.get("sequence"),
                    diagnosisReference=self._reference(
                        self._condition(
                            ConditionModel.objects.filter(
                                external_id=diagnosis.get("diagnosis")
                            ).first()
                        )
                    ),
                    type=[
                        CodeableConcept(
                            coding=[
                                Coding(
                                    system="http://terminology.hl7.org/CodeSystem/ex-diagnosistype",
                                    code="clinical",  # TODO: make this dynamic
                                )
                            ]
                        )
                    ],
                )
                for diagnosis in claim.diagnosis
            ]
            if claim.diagnosis
            else None,
            procedure=[
                ClaimProcedure(
                    sequence=procedure.get("sequence"),
                    procedureReference=self._reference(
                        self._condition(
                            ConditionModel.objects.filter(
                                external_id=procedure.get("procedure")
                            ).first()
                        )
                    ),
                    date=procedure.get("date").isoformat()
                    if procedure.get("date")
                    else None,
                )
                for procedure in claim.procedure
            ]
            if claim.procedure
            else None,
            supportingInfo=[
                ClaimSupportingInfo(
                    sequence=supporting_info.get("sequence"),
                    category=CodeableConcept(
                        coding=[
                            Coding(
                                **(
                                    supporting_info.get("category")
                                    or {
                                        "system": "http://terminology.hl7.org/CodeSystem/claiminformationcategory",
                                        "code": "info",
                                    }
                                ),
                            )
                        ]
                    ),
                    valueString=supporting_info.get("value"),
                    valueAttachment=self._attachment(
                        FileUpload.objects.filter(
                            external_id=supporting_info.get("attachment")
                        ).first()
                    )
                    if supporting_info.get("attachment")
                    else None,
                )
                for supporting_info in claim.supporting_info
            ]
            if claim.supporting_info
            else None,
            item=[
                ClaimItem(
                    sequence=item.get("sequence"),
                    productOrService=CodeableConcept(
                        coding=[Coding(**item.get("product_or_service"))]
                    ),
                    unitPrice=Money(
                        value=item.get("unit_price"),
                        currency="INR",
                    ),
                    quantity=Quantity(
                        value=item.get("quantity"),
                    ),
                    net=Money(
                        value=item.get("net"),
                        currency="INR",
                    ),
                    careTeamSequence=item.get("care_team_sequence"),
                    diagnosisSequence=item.get("diagnosis_sequence"),
                    procedureSequence=item.get("procedure_sequence"),
                    informationSequence=item.get("information_sequence"),
                )
                for item in claim.item
            ]
            if claim.item
            else None,
            total=Money(
                value=claim.total,
                currency="INR",
            ),
        )

    def _bundle_entry(self, resource: Resource):
        return BundleEntry(fullUrl=self._reference_url(resource), resource=resource)

    def create_coverage_eligibility_request_bundle(
        self,
        coverage_eligibility_request: CoverageEligibilityRequestModel,
    ):
        id = str(coverage_eligibility_request.external_id)

        return Bundle(
            id=id,
            meta=Meta(
                profile=[
                    "https://ig.hcxprotocol.io/v0.7.1/StructureDefinition-CoverageEligibilityRequestBundle.html"
                ],
                lastUpdated=coverage_eligibility_request.modified_date.isoformat(),
            ),
            identifier=Identifier(value=id, system=f"{CARE_IDENTIFIER_SYSTEM}/bundle"),
            type="collection",
            timestamp=datetime.now(UTC).isoformat(),
            entry=[
                self._bundle_entry(
                    self._coverage_eligibility_request(coverage_eligibility_request)
                ),
                *[self._bundle_entry(profile) for profile in self.cached_profiles()],
            ],
        )

    def create_claim_bundle(self, claim: ClaimRequestModel):
        id = str(claim.external_id)

        return Bundle(
            id=id,
            meta=Meta(
                profile=[
                    "https://ig.hcxprotocol.io/v0.7.1/StructureDefinition-ClaimRequestBundle.html"
                ],
                lastUpdated=claim.modified_date.isoformat(),
            ),
            identifier=Identifier(value=id, system=f"{CARE_IDENTIFIER_SYSTEM}/bundle"),
            type="collection",
            timestamp=datetime.now(UTC).isoformat(),
            entry=[
                self._bundle_entry(self._claim(claim)),
                *[self._bundle_entry(profile) for profile in self.cached_profiles()],
            ],
        )

    def process_coverage_eligibility_check_response(
        self, response: dict, headers: dict | None = None
    ):
        # Using construct to avoid fhir validation errors
        coverage_eligibility_response_bundle = Bundle.construct(**response)

        coverage_eligibility_response = CoverageEligibilityResponse.construct(
            **next(
                filter(
                    lambda entry: entry.get("resource", {}).get("resourceType")
                    == "CoverageEligibilityResponse",
                    coverage_eligibility_response_bundle.entry,
                )
            ).get("resource")
        )

        # TODO: this is temporary solution, once the CoverageEligibilityRequest is sent in the bundle, use that
        request_id = coverage_eligibility_response_bundle.id
        coverage_eligibility_request_instance = (
            CoverageEligibilityRequestModel.objects.filter(external_id=request_id)
        ).first()

        # TODO: use CoverageEligibilityResponseSpec to create the instance
        coverage_eligibility_response_instance = (
            CoverageEligibilityResponseModel.objects.create(
                request=coverage_eligibility_request_instance,
                outcome=coverage_eligibility_response.outcome,
                error=coverage_eligibility_response.error,
                disposition=coverage_eligibility_response.disposition,
                meta={
                    "raw_response": response,
                    "raw_headers": headers,
                },
            )
        )

        return (
            coverage_eligibility_response_instance,
            coverage_eligibility_request_instance,
        )

    def process_claim_response(self, response: dict, headers: dict | None = None):
        # Using construct to avoid fhir validation errors
        claim_response_bundle = Bundle.construct(**response)

        claim_response = ClaimResponse.construct(
            **next(
                filter(
                    lambda entry: entry.get("resource", {}).get("resourceType")
                    == "ClaimResponse",
                    claim_response_bundle.entry,
                )
            ).get("resource")
        )

        # TODO: this is temporary solution, once the Claim is sent in the bundle, use that
        request_id = claim_response_bundle.id
        claim_instance = ClaimRequestModel.objects.filter(
            external_id=request_id
        ).first()

        total_amount = reduce(
            lambda price, acc: price + acc,
            (
                float(claim_response_total.get("amount", {}).get("value", 0))
                for claim_response_total in claim_response.total
            ),
            0.0,
        )

        # TODO: use ClaimResponseSpec to create the instance
        claim_response_instance = ClaimResponseModel.objects.create(
            request=claim_instance,
            outcome=claim_response.outcome,
            error=claim_response.error,
            disposition=claim_response.disposition,
            item=claim_response.item,
            add_item=claim_response.addItem,
            total=claim_response.total,
            total_amount=total_amount,
            meta={
                "raw_response": response,
                "raw_headers": headers,
            },
        )

        return (claim_response_instance, claim_instance)
