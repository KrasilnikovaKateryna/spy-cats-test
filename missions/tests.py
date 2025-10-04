import pytest


def extract_results(resp):
    """Return list of items for both paginated and non-paginated responses."""
    if isinstance(resp.data, dict) and "results" in resp.data:
        return resp.data["results"]
    return resp.data


@pytest.mark.django_db
def test_create_mission_success_with_targets(api_client, make_cat):
    cat = make_cat()
    payload = {
        "cat": cat.id,
        "targets": [
            {"name": "Mission 1", "country": "US"},
            {"name": "Mission 2", "country": "UA"},
        ]
    }
    r = api_client.post("/missions/create/", payload, format="json")
    assert r.status_code == 201, r.data
    assert r.data["cat"] == cat.id
    assert len(r.data["targets"]) == 2
    assert {t["name"] for t in r.data["targets"]} == {"Mission 1", "Mission 2"}


@pytest.mark.django_db
def test_create_mission_no_targets_400(api_client, make_cat):
    cat = make_cat()
    payload = {"cat": cat.id, "targets": []}
    r = api_client.post("/missions/create/", payload, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_create_mission_more_than_3_targets_400(api_client, make_cat):
    cat = make_cat()
    payload = {
        "cat": cat.id,
        "targets": [
            {"name": "T1", "country": "US"},
            {"name": "T2", "country": "UA"},
            {"name": "T3", "country": "GB"},
            {"name": "T4", "country": "PL"},
        ]
    }
    r = api_client.post("/missions/create/", payload, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_list_all_missions_includes_targets_and_note(api_client, make_cat, make_mission, make_target, make_note):
    cat = make_cat()
    m = make_mission(cat=cat)
    t1 = make_target(mission=m, name="T1", country="US")
    make_note(t1, text="n1")
    make_target(mission=m, name="T2", country="UA")

    r = api_client.get("/missions/?ordering=id")
    assert r.status_code == 200
    items = extract_results(r)
    assert len(items) >= 1
    found = next(x for x in items if x["id"] == m.id)
    assert len(found["targets"]) == 2

    t_by_name = {t["name"]: t for t in found["targets"]}
    assert t_by_name["T1"]["note"]["text"] == "n1"
    assert t_by_name["T2"]["note"] is None


@pytest.mark.django_db
def test_retrieve_mission(api_client, make_cat, make_mission, make_target):
    cat = make_cat()
    m = make_mission(cat=cat)
    make_target(mission=m, name="T1")
    r = api_client.get(f"/missions/{m.id}/")
    assert r.status_code == 200
    assert r.data["id"] == m.id
    assert r.data["cat"] == cat.id
    assert len(r.data["targets"]) == 1


@pytest.mark.django_db
def test_delete_mission_without_cat_204_and_cascade(api_client, make_mission, make_target, make_note):
    m = make_mission(cat=None)
    t = make_target(mission=m, name="T1")
    _ = make_note(t, "n1")

    r = api_client.delete(f"/missions/{m.id}/")
    assert r.status_code in (200, 202, 204)

    r2 = api_client.get(f"/missions/{m.id}/")
    assert r2.status_code == 404


@pytest.mark.django_db
def test_delete_mission_with_cat_forbidden(api_client, make_cat, make_mission):
    cat = make_cat()
    m = make_mission(cat=cat)
    r = api_client.delete(f"/missions/{m.id}/")
    assert r.status_code == 400


@pytest.mark.django_db
def test_assign_cat_to_unassigned_mission(api_client, make_cat, make_mission, make_target):
    m = make_mission(cat=None)
    t = make_target(mission=m)
    cat = make_cat()
    r = api_client.patch(f"/missions/{m.id}/assign-cat/", {"cat": cat.id}, format="json")
    assert r.status_code == 200, r.data
    assert r.data["cat"] == cat.id


@pytest.mark.django_db
def test_assign_cat_that_already_has_active_mission_conflict(api_client, make_cat, make_mission):
    cat = make_cat()
    m1 = make_mission(cat=cat)
    m2 = make_mission(cat=None)

    r = api_client.patch(f"/missions/{m2.id}/assign-cat/", {"cat": cat.id}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_update_target_requires_assigned_cat(api_client, make_mission, make_target, make_cat):
    m = make_mission(cat=None)
    t = make_target(mission=m, name="T1")

    # not assigned -> 400
    r1 = api_client.patch(f"/missions/targets/{t.id}/", {"completed": True}, format="json")
    assert r1.status_code == 400

    cat = make_cat()
    r2 = api_client.patch(f"/missions/{m.id}/assign-cat/", {"cat": cat.id}, format="json")
    assert r2.status_code == 200

    r3 = api_client.patch(f"/missions/targets/{t.id}/", {"completed": True}, format="json")
    assert r3.status_code == 200
    assert r3.data["completed"] is True


@pytest.mark.django_db
def test_create_note_success_and_conflict(api_client, make_mission, make_target):
    m = make_mission()
    t = make_target(mission=m, name="T1")

    # create
    r1 = api_client.post(f"/missions/targets/{t.id}/note/create/", {"text": "n1"}, format="json")
    assert r1.status_code == 201, r1.data
    assert r1.data["text"] == "n1"

    # second create
    r2 = api_client.post(f"/missions/targets/{t.id}/note/create/", {"text": "n2"}, format="json")
    assert r2.status_code == 400


@pytest.mark.django_db
def test_create_note_forbidden_if_completed(api_client, make_mission, make_target):
    m = make_mission()
    t = make_target(mission=m, name="T1", completed=True)

    r = api_client.post(f"/missions/targets/{t.id}/note/create/", {"text": "n1"}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_update_note_success(api_client, make_mission, make_target, make_note):
    m = make_mission()
    t = make_target(mission=m, name="T1")
    note = make_note(t, "n1")

    r = api_client.patch(f"/missions/targets/{t.id}/note/update/", {"text": "n2"}, format="json")
    assert r.status_code == 200
    assert r.data["text"] == "n2"


@pytest.mark.django_db
def test_update_note_forbidden_if_target_or_mission_completed(api_client, make_mission, make_target, make_note):
    # mission completed
    m = make_mission()
    t = make_target(mission=m, name="T1", completed=True)
    make_note(t, "n1")
    r1 = api_client.patch(f"/missions/targets/{t.id}/note/update/", {"text": "nX"}, format="json")
    assert r1.status_code == 400

    # target completed
    m2 = make_mission()
    t2 = make_target(mission=m2, name="T2", completed=True)
    _ = make_target(mission=m2, name="T2", completed=False)
    make_note(t2, "n2")
    r2 = api_client.patch(f"/missions/targets/{t2.id}/note/update/", {"text": "nY"}, format="json")
    assert r2.status_code == 400
