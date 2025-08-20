from rest_framework.serializers import CharField, JSONField, ModelSerializer, UUIDField

from care.emr.resources.user.spec import UserRetrieveSpec
from care.utils.serializers.fields import ExternalIdSerializerField
from hcx.api.serializers.base import EMRPydanticModelField
from hcx.api.serializers.claim import ClaimSerializer
from hcx.models.deprecated.claim import Claim
from hcx.models.deprecated.communication import Communication

TIMESTAMP_FIELDS = (
    "created_date",
    "modified_date",
)


class CommunicationSerializer(ModelSerializer):
    id = UUIDField(source="external_id", read_only=True)

    claim = ExternalIdSerializerField(
        queryset=Claim.objects.all(), write_only=True, required=True
    )
    claim_object = ClaimSerializer(source="claim", read_only=True)

    identifier = CharField(required=False)
    content = JSONField(required=False)

    created_by = EMRPydanticModelField(
        UserRetrieveSpec,
        source="created_by",
        read_only=True,
    )
    last_modified_by = EMRPydanticModelField(
        UserRetrieveSpec,
        source="last_modified_by",
        read_only=True,
    )

    class Meta:
        model = Communication
        exclude = ("deleted", "external_id")
        read_only_fields = TIMESTAMP_FIELDS

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        validated_data["last_modified_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        instance.last_modified_by = self.context["request"].user
        return super().update(instance, validated_data)
