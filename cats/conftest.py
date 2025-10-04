import pytest
from decimal import Decimal
from rest_framework.test import APIClient

from cats.models import SpyCat
from missions.models import Mission, Target


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_cat(db):
    def _make_cat(**kwargs):
        defaults = dict(
            name="Cat 1",
            years_of_experience=3,
            breed="British Shorthair",
            salary=Decimal("3000.00"),
        )
        defaults.update(kwargs)
        return SpyCat.objects.create(**defaults)
    return _make_cat


@pytest.fixture
def make_mission(db):
    def _make_mission(cat=None, completed=False):
        return Mission.objects.create(cat=cat)
    return _make_mission


@pytest.fixture
def make_target(db):
    def _make_target(mission, name="Target A", country="US", completed=False):
        return Target.objects.create(
            mission=mission, name=name, country=country, completed=completed
        )
    return _make_target


class _DummyResp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or []

    def json(self):
        return self._payload


@pytest.fixture
def breed_api_success(monkeypatch):
    payload = [
        {"id": "bsho", "name": "British Shorthair", "alt_names": "Brit, Britannica"},
        {"id": "hili", "name": "Highlander", "alt_names": "Highland Straight, Britannica"},
    ]

    def _fake_get(url, *args, **kwargs):
        assert "thecatapi.com/v1/breeds" in url
        return _DummyResp(200, payload)

    import requests
    monkeypatch.setattr(requests, "get", _fake_get)


@pytest.fixture
def breed_api_unavailable(monkeypatch):
    def _fake_get(url, *args, **kwargs):
        return _DummyResp(500, [])
    import requests
    monkeypatch.setattr(requests, "get", _fake_get)
