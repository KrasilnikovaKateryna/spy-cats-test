from django.urls import path

from cats.views import RetrieveUpdateRemoveSpyCat, ListCatMissions, CreateSpyCat, ListSpyCats

urlpatterns = [
    path("create/", CreateSpyCat.as_view(), name="cat-create"),
    path("", ListSpyCats.as_view(), name="cat-list"),
    path("<int:pk>/missions/", ListCatMissions.as_view(), name="cat-missions"),
    path("<int:pk>/", RetrieveUpdateRemoveSpyCat.as_view(), name="cat-detail"),
]