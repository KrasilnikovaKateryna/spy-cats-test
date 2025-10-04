import pytest
from decimal import Decimal
from rest_framework.test import APIClient

from cats.models import SpyCat
from missions.models import Mission, Target, Note


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_cat(db):
    def _make_cat(**kw):
        defaults = dict(
            name="Cat 1",
            years_of_experience=3,
            breed="British Shorthair",
            salary=Decimal("3000.00"),
        )
        defaults.update(kw)
        return SpyCat.objects.create(**defaults)
    return _make_cat


@pytest.fixture
def make_mission(db):
    def _make_mission(cat=None):
        return Mission.objects.create(cat=cat)
    return _make_mission


@pytest.fixture
def make_target(db):
    def _make_target(mission, name="Target A", country="US", completed=False):
        return Target.objects.create(
            mission=mission, name=name, country=country, completed=completed
        )
    return _make_target


@pytest.fixture
def make_note(db):
    def _make_note(target, text="Observe north perimeter"):
        return Note.objects.create(target=target, text=text)
    return _make_note
