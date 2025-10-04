from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from rest_framework import generics, status
import requests
from rest_framework.response import Response

from cats.models import SpyCat
from cats.serializers import SpyCatSerializer, UpdateSpyCatSerializer
from missions.models import Mission
from missions.serializers import MissionSerializer


@extend_schema(
    tags=["Cats"],
    summary="Create a spy cat",
    description=(
        "Creates a new spy cat. The `breed` is validated against TheCatAPI "
        "(`GET https://api.thecatapi.com/v1/breeds`). "
        "Returns **400** if the breed is unknown, **502** when the external registry is unavailable."
    ),
    request=SpyCatSerializer,
    responses={
        201: SpyCatSerializer,
        400: OpenApiResponse(description="Validation error (e.g., unknown breed)"),
        502: OpenApiResponse(description="Service unavailable, try again later."),
    },
    examples=[OpenApiExample(
        "Create SpyCat",
        value={
            "name": "СatName",
            "years_of_experience": 4,
            "breed": "British Shorthair",
            "salary": "3500.00"
        },
        request_only=True,
    )],
)
class CreateSpyCat(generics.CreateAPIView):
    queryset = SpyCat.objects.all()
    serializer_class = SpyCatSerializer

    def create(self, request, *args, **kwargs):
        breed = request.data.get("breed")
        if not breed:
            return Response(
                {"error": "Field 'breed' is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = requests.get("https://api.thecatapi.com/v1/breeds")
        if response.status_code != 200:
            return Response(
                {"error": "Service unavailable, try again later."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        breeds_data = response.json()

        all_names = []
        for breed_data in breeds_data:
            all_names.append(breed_data["name"].lower())
            if breed_data.get("alt_names"):
                for alt in breed_data["alt_names"].split(","):
                    all_names.append(alt.strip().lower())

        if breed.lower() not in all_names:
            return Response(
                {"error": f"Breed '{breed}' not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().create(request, *args, **kwargs)


@extend_schema(
    tags=["Cats"],
    summary="List spy cats",
    description="Returns a paginated list of cats.",
    responses={200: OpenApiResponse(response=SpyCatSerializer(many=True))},
)
class ListSpyCats(generics.ListAPIView):
    queryset = SpyCat.objects.all()
    serializer_class = SpyCatSerializer


@extend_schema(
    tags=["Cats", "Missions"],
    summary="List missions of a specific cat",
    description="Returns missions assigned to the given cat (path param `pk` is the cat ID).",
    parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Cat ID")],
    responses={200: OpenApiResponse(response=MissionSerializer(many=True))},
    examples=[OpenApiExample(
        "List missions of a cat (response trimmed)",
        value={"results": [{"id": 1, "cat": 7, "completed": False, "targets": []}]},
        response_only=True,
    )],
)
class ListCatMissions(generics.ListAPIView):
    serializer_class = MissionSerializer

    def get_queryset(self):
        cat_id = self.kwargs.get("pk")
        get_object_or_404(SpyCat, pk=cat_id)
        return Mission.objects.filter(cat_id=cat_id).select_related("cat").prefetch_related("targets__note")


class RetrieveUpdateRemoveSpyCat(generics.RetrieveUpdateDestroyAPIView):
    queryset = SpyCat.objects.all()

    def get_serializer_class(self):
        if self.request.method.lower() == "patch":
            return UpdateSpyCatSerializer
        return SpyCatSerializer

    @extend_schema(
        tags=["Cats"],
        summary="Retrieve a spy cat",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Cat ID")],
        responses={200: SpyCatSerializer, 404: OpenApiResponse(description="Not found")},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["Cats"],
        summary="Delete a spy cat",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Cat ID")],
        responses={204: OpenApiResponse(description="Deleted"), 404: OpenApiResponse(description="Not found")},
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    @extend_schema(
        tags=["Cats"],
        summary="Update a spy cat",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Cat ID")],
        request=UpdateSpyCatSerializer,
        responses={200: SpyCatSerializer, 404: OpenApiResponse(description="Not found")},
        examples=[OpenApiExample(
            "Update SpyCat",
            value={
                "name": "CatName 2",
                "years_of_experience": 5,
                "salary": "4200.00"
            },
            request_only=True,
        )],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)