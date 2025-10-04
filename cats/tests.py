import pytest
from decimal import Decimal


@pytest.mark.django_db
def test_create_spycat_success_official_name(api_client, breed_api_success):
    payload = {
        "name": "Cat One",
        "years_of_experience": 4,
        "breed": "British Shorthair",
        "salary": "3500.00",
    }
    r = api_client.post("/cats/create/", payload, format="json")
    assert r.status_code == 201, r.data
    assert r.data["name"] == "Cat One"


@pytest.mark.django_db
def test_create_spycat_success_alt_name(api_client, breed_api_success):
    # alt name present in mocked payload: "Brit"
    payload = {
        "name": "Alt Name Cat",
        "years_of_experience": 2,
        "breed": "Brit",
        "salary": "2100.00",
    }
    r = api_client.post("/cats/create/", payload, format="json")
    assert r.status_code == 201, r.data


@pytest.mark.django_db
def test_create_spycat_unknown_breed_400(api_client, breed_api_success):
    payload = {
        "name": "Unknown Breed Cat",
        "years_of_experience": 1,
        "breed": "Totally Unknown Breed",
        "salary": "1500.00",
    }
    r = api_client.post("/cats/create/", payload, format="json")
    assert r.status_code == 400
    assert "not found" in r.data["error"].lower()


@pytest.mark.django_db
def test_create_spycat_breed_api_502(api_client, breed_api_unavailable):
    payload = {
        "name": "Network Cat",
        "years_of_experience": 5,
        "breed": "British Shorthair",
        "salary": "4200.00",
    }
    r = api_client.post("/cats/create/", payload, format="json")
    assert r.status_code == 502


@pytest.mark.django_db
def test_create_spycat_missing_breed_400(api_client):
    payload = {
        "name": "No Breed Cat",
        "years_of_experience": 3,
        "salary": "2000.00",
    }
    r = api_client.post("/cats/create/", payload, format="json")
    assert r.status_code == 400
    assert "breed" in r.data["error"].lower()


@pytest.mark.django_db
def test_list_spycats(api_client, make_cat):
    make_cat(name="A")
    make_cat(name="B")
    r = api_client.get("/cats/?ordering=id")
    assert r.status_code == 200

    if isinstance(r.data, dict) and "results" in r.data:
        names = [c["name"] for c in r.data["results"]]
        assert set(names) >= {"A", "B"}
    else:
        names = [c["name"] for c in r.data]
        assert set(names) >= {"A", "B"}


@pytest.mark.django_db
def test_retrieve_and_delete_spycat(api_client, make_cat):
    cat = make_cat(name="ToDelete")
    # retrieve
    r1 = api_client.get(f"/cats/{cat.id}/")
    assert r1.status_code == 200
    assert r1.data["name"] == "ToDelete"
    # delete
    r2 = api_client.delete(f"/cats/{cat.id}/")
    assert r2.status_code in (200, 202, 204)
    # ensure deleted
    r3 = api_client.get(f"/cats/{cat.id}/")
    assert r3.status_code == 404


@pytest.mark.django_db
def test_update_spycat_patch(api_client, make_cat):
    cat = make_cat(name="OldName", salary=Decimal("1000.00"))
    payload = {"salary": "1250.50"}
    r = api_client.patch(f"/cats/{cat.id}/", payload, format="json")
    assert r.status_code == 200
    assert r.data["salary"] == "1250.50"


@pytest.mark.django_db
def test_list_cat_missions_only_for_that_cat(api_client, make_cat, make_mission, make_target):
    cat1 = make_cat(name="Cat1")
    cat2 = make_cat(name="Cat2")
    m1 = make_mission(cat=cat1)
    _ = make_target(mission=m1, name="T1", country="US")
    _ = make_mission(cat=cat2)

    r = api_client.get(f"/cats/{cat1.id}/missions/?ordering=id")
    assert r.status_code == 200

    if isinstance(r.data, dict) and "results" in r.data:
        items = r.data["results"]
    else:
        items = r.data
    assert len(items) >= 1
    assert all(item["cat"] == cat1.id for item in items)
