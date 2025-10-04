from django.db import transaction, IntegrityError
from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from cats.models import SpyCat
from missions.models import Mission, Target, Note


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'text', 'created_at']
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        target = self._get_target()
        if target.completed or target.mission.is_completed:
            raise serializers.ValidationError(
                {"detail": "Notes cannot be created/updated because the target or the mission is completed."}
            )
        return attrs

    def create(self, validated_data):
        target = self._get_target(required=True)
        if hasattr(target, "note"):
            raise serializers.ValidationError({"detail": "Note already exists."})
        try:
            return Note.objects.create(target=target, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"detail": "Note already exists."})


    def _get_target(self, required=False):
        target = self.context.get("target") or getattr(self.instance, "target", None)
        if required and target is None:
            raise serializers.ValidationError({"detail": "Target context is required."})
        return target


class TargetCompleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = ["completed"]

    def update(self, instance, validated_data):
        if instance.completed or instance.mission.is_completed:
            raise serializers.ValidationError(
                "Notes cannot be updated because the target or the mission is completed."
            )
        return super().update(instance, validated_data)


class TargetSerializer(serializers.ModelSerializer):
    country = CountryField()
    note = NoteSerializer(read_only=True)

    class Meta:
        model = Target
        fields = ['id', 'name', 'country', 'completed', 'note']
        read_only_fields = ["id"]


class TargetCreateSerializer(serializers.ModelSerializer):
    country = CountryField()

    class Meta:
        model = Target
        fields = ["name", "country", "completed"]


class MissionSerializer(serializers.ModelSerializer):
    targets = TargetSerializer(many=True)

    class Meta:
        model = Mission
        fields = ['id', 'cat', 'is_completed', 'targets']
        read_only_fields = ["id"]


class MissionAssignCatSerializer(serializers.ModelSerializer):
    cat = serializers.PrimaryKeyRelatedField(queryset=SpyCat.objects.all())

    class Meta:
        model = Mission
        fields = ['cat']

    def validate(self, attrs):
        mission = self.instance
        cat = attrs.get("cat")

        if mission.is_completed:
            raise serializers.ValidationError("Cannot assign a cat to a completed mission.")

        other_active_exists = (
            Mission.objects
            .filter(cat=cat)
            .exclude(pk=mission.pk)
            .filter(targets__completed=False)
            .exists()
        )
        if other_active_exists:
            raise serializers.ValidationError("This cat already has an active mission.")

        return attrs


class MissionCreateSerializer(serializers.ModelSerializer):
    cat = serializers.PrimaryKeyRelatedField(queryset=SpyCat.objects.all(), required=False)
    targets = TargetCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Mission
        fields = ["id", "cat", "is_completed", "targets"]
        read_only_fields = ["id"]

    def validate_targets(self, targets):
        if not targets:
            raise serializers.ValidationError("At least one target is required.")

        if len(targets) > 3:
            raise serializers.ValidationError("A mission can have at most 3 targets.")

        return targets

    @transaction.atomic
    def create(self, validated_data):
        targets_data = validated_data.pop("targets", [])
        mission = Mission.objects.create(**validated_data)
        Target.objects.bulk_create([
            Target(mission=mission, **t) for t in targets_data
        ])
        return mission