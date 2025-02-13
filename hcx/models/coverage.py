from django.db import models

from care.emr.models.base import EMRBaseModel


class Coverage(EMRBaseModel):
    identifier = models.CharField(max_length=100, null=False, blank=False)
    subscriber_id = models.CharField(max_length=100, null=False, blank=False)
    period = models.JSONField(null=True, blank=True)
    policy_holder = models.JSONField(null=True, blank=True)
    subscriber = models.JSONField(null=True, blank=True)
    relationship = models.JSONField(null=True, blank=True)
    beneficiary = models.ForeignKey("emr.Patient", on_delete=models.CASCADE)
    payor = models.JSONField(default=dict, null=False, blank=False)
    status = models.CharField(max_length=100, null=False, blank=False)
    kind = models.CharField(max_length=100, null=False, blank=False)


class CoverageEligibilityRequest(EMRBaseModel):
    priority = models.CharField(max_length=100, null=False, blank=False)
    purpose = models.CharField(max_length=100, null=False, blank=False)
    facility = models.ForeignKey(
        "facility.Facility", on_delete=models.CASCADE, null=True, blank=True
    )
    patient = models.ForeignKey("emr.Patient", on_delete=models.CASCADE)
    coverage = models.ForeignKey("hcx.Coverage", on_delete=models.CASCADE)


class CoverageEligibilityResponse(EMRBaseModel):
    request = models.ForeignKey(
        "hcx.CoverageEligibilityRequest", on_delete=models.CASCADE
    )
    outcome = models.CharField(max_length=100, null=False, blank=False)
    error = models.JSONField(null=True, blank=True)
    disposition = models.TextField(null=True, blank=True)
