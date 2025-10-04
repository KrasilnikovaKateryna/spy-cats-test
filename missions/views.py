from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
from rest_framework import generics, status, serializers
from rest_framework.response import Response

from missions.models import Mission, Note, Target
from missions.serializers import MissionSerializer, MissionCreateSerializer, MissionAssignCatSerializer, NoteSerializer, \
    TargetCompleteSerializer


@extend_schema(
    tags=["Missions"],
    summary="Create a mission with targets",
    description="Creates a mission and up to three targets in a single request.",
    request=MissionCreateSerializer,
    responses={201: MissionSerializer, 400: OpenApiResponse(description="Validation error")},
    examples=[OpenApiExample(
        "Create mission with up to 3 targets",
        value={
            "cat": 1,
            "targets": [
                {"name": "Harbor Warehouse", "country": "US", "completed": False},
                {"name": "Old Bridge", "country": "UA"}
            ]
        },
        request_only=True,
    )],
)
class CreateMission(generics.CreateAPIView):
    serializer_class = MissionCreateSerializer

    def create(self, request, *args, **kwargs):
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        mission = write_serializer.save()

        mission = Mission.objects.select_related("cat").prefetch_related("targets__note").get(pk=mission.pk)

        read_serializer = MissionSerializer(mission, context=self.get_serializer_context())
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema(
    tags=["Missions"],
    summary="Assign a cat to a mission",
    description="Assigns a cat to a mission. A cat can have only one active (not completed) mission.",
    parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Mission ID")],
    request=MissionAssignCatSerializer,
    responses={
        200: MissionSerializer,
        400: OpenApiResponse(description="Mission is completed / invalid data"),
        409: OpenApiResponse(description="Mission already has a cat / cat already has active mission"),
    },
    examples=[OpenApiExample(
        "Assign a cat to a mission",
        value={"cat": 3},
        request_only=True,
    )],
)
class AssignCatToMission(generics.UpdateAPIView):
    http_method_names = ["patch"]
    queryset = Mission.objects.only("id", "cat_id")
    serializer_class = MissionAssignCatSerializer


@extend_schema(
    tags=["Missions"],
    summary="List missions",
    description="Returns a paginated list of missions with embedded targets and their notes.",
    responses={200: MissionSerializer},
)
class ListAllMissions(generics.ListAPIView):
    queryset = Mission.objects.select_related("cat").prefetch_related(
        Prefetch(
            "targets",
            queryset=Target.objects.select_related("note")
        )
    )
    serializer_class = MissionSerializer


class RetrieveRemoveMission(generics.RetrieveDestroyAPIView):
    serializer_class = MissionSerializer

    def get_queryset(self):
        if self.request.method == "GET":
            return (Mission.objects
                    .select_related("cat")
                    .prefetch_related(Prefetch("targets", queryset=Target.objects.select_related("note"))))

        return Mission.objects.only("id", "cat_id")

    def perform_destroy(self, instance):
        if instance.cat_id:
            raise serializers.ValidationError("Mission cannot be deleted because it is already assigned to a cat.")
        instance.delete()

    @extend_schema(
        tags=["Missions"],
        summary="Get a mission",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Mission ID")],
        responses={200: MissionSerializer, 404: OpenApiResponse(description="Not found")},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["Missions"],
        summary="Delete a mission",
        description="Deletes a mission. Deletion is not allowed if the mission is already assigned to a cat.",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Mission ID")],
        responses={
            204: OpenApiResponse(description="Deleted"),
            400: OpenApiResponse(description="Mission is assigned to a cat"),
            404: OpenApiResponse(description="Not found"),
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


@extend_schema(
    tags=["Targets"],
    summary="Update a target",
    description="Partially updates a target. To mark a target as completed, the mission must be assigned to a cat.",
    parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Target ID")],
    request=TargetCompleteSerializer,
    responses={
        200: TargetCompleteSerializer,
        400: OpenApiResponse(description="Mission is not assigned to a cat"),
        404: OpenApiResponse(description="Target not found"),
    },
    examples=[OpenApiExample(
        "Mark target as completed",
        value={"completed": True},
        request_only=True,
    )],
)
class UpdateTarget(generics.UpdateAPIView):
    http_method_names = ["patch"]
    queryset = Target.objects.select_related("mission").only("id", "completed", "mission_id", "mission__cat_id")
    serializer_class = TargetCompleteSerializer

    def patch(self, request, *args, **kwargs):
        target = self.get_object()

        if not target.mission.cat_id:
            return Response({"detail": "Cannot complete the mission while it is not assigned to cat."},
                            status=status.HTTP_400_BAD_REQUEST)

        return super().patch(request, *args, **kwargs)


class UpdateNote(generics.UpdateAPIView):
    http_method_names = ["patch"]
    queryset = (Note.objects
                .select_related("target", "target__mission")
                .only("id", "text", "target"))
    serializer_class = NoteSerializer

    def get_object(self):
        target_id = self.kwargs["pk"]
        return get_object_or_404(Note, target_id=target_id)

    @extend_schema(
        tags=["Notes"],
        summary="Update a target note",
        description="Updates the note text for a target. Editing is forbidden if the target or its mission is completed.",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Target ID")],
        request=NoteSerializer,
        responses={
            200: NoteSerializer,
            400: OpenApiResponse(description="Target or mission is completed"),
            404: OpenApiResponse(description="Note/target not found"),
        },
        examples=[OpenApiExample("Update note body", value={"text": "Observe north perimeter at 03:00"}, request_only=True)],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class CreateNote(generics.CreateAPIView):
    serializer_class = NoteSerializer

    def get_queryset(self):
        return Note.objects.none()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        target = get_object_or_404(Target.objects.select_related("mission"), pk=self.kwargs["pk"])
        ctx["target"] = target
        return ctx

    @extend_schema(
        tags=["Notes"],
        summary="Create a target note",
        description="Creates a note for the target. Returns 400 if the note already exists.",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Target ID")],
        request=NoteSerializer,
        responses={
            201: NoteSerializer,
            400: OpenApiResponse(description="Target or mission is completed, Note already exists"),
            404: OpenApiResponse(description="Target not found"),
        },
        examples=[OpenApiExample("Create note body", value={"text": "Observe north perimeter at 03:00"}, request_only=True)],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
