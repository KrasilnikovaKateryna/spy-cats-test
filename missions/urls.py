from django.urls import path

from missions.views import CreateMission, AssignCatToMission, ListAllMissions, RetrieveRemoveMission, UpdateTarget, \
    CreateNote, UpdateNote

urlpatterns = [
    path("create/", CreateMission.as_view(), name="mission-create"),
    path("<int:pk>/assign-cat/", AssignCatToMission.as_view(), name="mission-assign-cat"),
    path("", ListAllMissions.as_view(), name="mission-list"),
    path("<int:pk>/", RetrieveRemoveMission.as_view(), name="mission-detail"),
    path("targets/<int:pk>/", UpdateTarget.as_view(), name="target-update"),
    path("targets/<int:pk>/note/create/", CreateNote.as_view(), name="target-note-create"),
    path("targets/<int:pk>/note/update/", UpdateNote.as_view(), name="target-note-update"),
]