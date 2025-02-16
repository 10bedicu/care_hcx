from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer, UUIDField

from care.utils.serializers.fields import ExternalIdSerializerField
from hcx.models.deprecated.claim import Claim
from hcx.models.deprecated.communication import Communication
from hcx.models.deprecated.policy import Policy


class CheckEligibilitySerializer(Serializer):
    policy = UUIDField(required=True)

    def validate(self, attrs):
        if "policy" in attrs:
            get_object_or_404(Policy.objects.filter(external_id=attrs["policy"]))
        else:
            raise ValidationError({"policy": "Field is Required"})

        return super().validate(attrs)


class MakeClaimSerializer(Serializer):
    claim = UUIDField(required=True)

    def validate(self, attrs):
        if "claim" in attrs:
            get_object_or_404(Claim.objects.filter(external_id=attrs["claim"]))
        else:
            raise ValidationError({"claim": "Field is Required"})

        return super().validate(attrs)


class SendCommunicationSerializer(Serializer):
    communication = ExternalIdSerializerField(
        queryset=Communication.objects.all(), required=True
    )
