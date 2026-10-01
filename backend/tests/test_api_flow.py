from pathlib import Path

SAMPLE = (Path(__file__).resolve().parents[2] / "samples" / "inventory_requirements_01.md").read_text(encoding="utf-8")


def test_full_pipeline(client):
    p = client.post("/api/projects", json={"name": "재고 데모", "domain": "inventory"}).json()
    pid = p["id"]
    assert client.post(f"/api/projects/{pid}/stages/features/generate").status_code == 400

    client.post(f"/api/projects/{pid}/documents/text", json={"text": SAMPLE})

    state = client.post(f"/api/projects/{pid}/stages/requirements/generate").json()
    types = [r["type"] for r in state["requirements"]]
    assert types.count("FUNCTIONAL") == 11 and types.count("NON_FUNCTIONAL") == 3

    state = client.post(f"/api/projects/{pid}/stages/features/generate").json()
    assert state["features"] and all(f["requirement_codes"] for f in state["features"])

    state = client.post(f"/api/projects/{pid}/stages/data_model/generate").json()
    tables = {e["table_name"] for e in state["entities"]}
    assert {"item", "warehouse", "inventory", "stock_transaction", "partner", "stock_count"} <= tables

    ddl = client.get(f"/api/projects/{pid}/export/ddl").text
    assert "CREATE TABLE stock_transaction" in ddl

    issues = client.post(f"/api/projects/{pid}/review").json()
    assert not [i for i in issues if i["rule_code"] in {"R05", "R06", "R09"}], issues

    trace = client.get(f"/api/projects/{pid}/trace").json()
    assert {t["requirement_code"] for t in trace} == {r["code"] for r in state["requirements"]}

    # 사용자 편집: 기능 하나 삭제 → 검토에서 R01 누락이 잡혀야 한다
    feats = state["features"][1:]
    removed_reqs = state["features"][0]["requirement_codes"]
    client.put(f"/api/projects/{pid}/design/features", json={"features": feats})
    issues = client.post(f"/api/projects/{pid}/review").json()
    assert {i["target_code"] for i in issues if i["rule_code"] == "R01"} >= set(removed_reqs)

    v = client.post(f"/api/projects/{pid}/stages/features/approve").json()
    assert v["version_no"] == 1
    assert client.get(f"/api/projects/{pid}").json()["stage_status"]["features"] == "APPROVED"


def test_ddl_execution_check_catches_bad_type(client):
    pid = client.post("/api/projects", json={"name": "오류", "domain": "inventory"}).json()["id"]
    body = {"entities": [{"table_name": "t1", "attributes": [{"name": "id", "data_type": "NOTATYPE", "is_pk": True}]}]}
    client.put(f"/api/projects/{pid}/design/data_model", json=body)
    issues = client.post(f"/api/projects/{pid}/review").json()
    assert any(i["rule_code"] == "R09" for i in issues)
