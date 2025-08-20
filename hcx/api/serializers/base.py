from rest_framework import serializers


class EMRPydanticModelField(serializers.ReadOnlyField):
    """
    Custom serializer field to handle EMRResource-based Pydantic models in DRF
    with serialization support
    """

    def __init__(self, pydantic_model, **kwargs):
        self.pydantic_model = pydantic_model
        super().__init__(**kwargs)

    def to_representation(self, value):
        if not value:
            return None

        request = self.context.get("request", None)
        user = request.user if request else None

        pydantic_instance = self.pydantic_model.serialize(value, user=user)
        return pydantic_instance.to_json()
