from django.db import models

from care.users.models import User
from care.utils.models.base import BaseModel
from care.utils.models.validators import JSONFieldSchemaValidator
from hcx.models.deprecated.claim import ClaimDeprecated
from hcx.models.json_schema.communication import CONTENT


class CommunicationDeprecated(BaseModel):
    identifier = models.TextField(null=True, blank=True)
    claim = models.ForeignKey(ClaimDeprecated, on_delete=models.CASCADE)

    content = models.JSONField(
        default=list, validators=[JSONFieldSchemaValidator(CONTENT)], null=True
    )

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="communication_last_modified_by",
    )

    class Meta:
        db_table = "communication_deprecated"
        managed = False
