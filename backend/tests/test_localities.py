"""National authorities + localities directory and resolution tests."""


def test_authorities_seeded(client, auth):
    r = client.get("/api/v1/municipalities", params={"limit": 500}, headers=auth)
    assert r.status_code == 200, r.text
    munis = r.json()
    assert len(munis) >= 250  # national list ~261
    # New fields are present on the model.
    sample = munis[0]
    assert "vet_name" in sample and "license_number" in sample


def test_localities_seeded_and_searchable(client, auth):
    r = client.get("/api/v1/localities", params={"search": "תל אביב"}, headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 1
    names = [x["name"] for x in body["items"]]
    assert any("תל אביב" in n for n in names)


def test_resolve_city_to_authority(client, auth):
    r = client.get("/api/v1/localities/resolve", params={"city": "חיפה"}, headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["resolved"] is True
    assert body["authority"] is not None
    assert body["authority"]["email"]


def test_resolve_regional_council_member(client, auth):
    """A small locality inside a regional council resolves to the council's vet."""
    # Find any locality that is linked but whose name differs from its authority.
    page = client.get("/api/v1/localities", params={"search": "כפר", "limit": 50}, headers=auth).json()
    linked = [x for x in page["items"] if x["municipality_id"] and not x["needs_review"]]
    assert linked, "expected some linked localities"
    name = linked[0]["name"]
    r = client.get("/api/v1/localities/resolve", params={"city": name}, headers=auth).json()
    assert r["resolved"] is True
    assert r["authority"] is not None


def test_needs_review_queue_and_manual_assign(client, auth):
    queue = client.get("/api/v1/localities", params={"needs_review": True, "limit": 1000}, headers=auth).json()
    assert queue["total"] >= 1  # ~63 unmatched localities
    loc = queue["items"][0]
    assert loc["needs_review"] is True

    muni_id = client.get("/api/v1/municipalities", params={"limit": 1}, headers=auth).json()[0]["id"]
    r = client.patch(f"/api/v1/localities/{loc['id']}", json={"municipality_id": muni_id}, headers=auth)
    assert r.status_code == 200, r.text
    assert r.json()["municipality_id"] == muni_id
    assert r.json()["needs_review"] is False


def test_resolve_unknown_city(client, auth):
    r = client.get("/api/v1/localities/resolve", params={"city": "עיר שלא קיימת בכלל"}, headers=auth).json()
    assert r["resolved"] is False
    assert r["authority"] is None


def test_localities_require_auth(client):
    assert client.get("/api/v1/localities").status_code == 401
    assert client.get("/api/v1/localities/resolve", params={"city": "חיפה"}).status_code == 401
