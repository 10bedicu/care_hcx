from django.db import models

from care.emr.models.base import EMRBaseModel


class Claim(EMRBaseModel):
    type = models.CharField(max_length=100, null=False, blank=False)
    use = models.CharField(max_length=100, null=False, blank=False)
    status = models.CharField(max_length=100, null=False, blank=False)
    priority = models.CharField(max_length=100, null=False, blank=False)
    facility = models.ForeignKey("facility.Facility", on_delete=models.CASCADE)
    patient = models.ForeignKey("emr.Patient", on_delete=models.CASCADE)
    encounter = models.ForeignKey("emr.Encounter", on_delete=models.CASCADE)
    insurance = models.JSONField(null=True, blank=True)
    billable_period = models.JSONField(null=True, blank=True)
    related = models.JSONField(null=True, blank=True)
    care_team = models.JSONField(null=True, blank=True)
    diagnosis = models.JSONField(null=True, blank=True)
    procedure = models.JSONField(null=True, blank=True)
    supporting_info = models.JSONField(null=True, blank=True)
    item = models.JSONField(null=True, blank=True)
    patient_paid = models.FloatField(null=True, blank=True)
    total = models.FloatField(null=True, blank=True)


class ClaimResponse(EMRBaseModel):
    request = models.ForeignKey("hcx.Claim", on_delete=models.CASCADE)
    outcome = models.CharField(max_length=100, null=False, blank=False)
    error = models.JSONField(null=True, blank=True)
    disposition = models.TextField(null=True, blank=True)
    item = models.JSONField(null=True, blank=True)
    add_item = models.JSONField(null=True, blank=True)
    total = models.JSONField(null=True, blank=True)
    total_amount = models.FloatField(null=True, blank=True)
