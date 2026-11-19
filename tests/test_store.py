from job_application_tracker.models import Application
from job_application_tracker.store import ApplicationStore


def test_add_inserts_newest_first_and_logs():
    store = ApplicationStore()
    first = store.add(Application(company="A", position="Dev"))
    second = store.add(Application(company="B", position="Lead"))
    assert [a.id for a in store.all()] == [2, 1]
    assert first.id == 1 and second.id == 2
    assert first.created_at and second.created_at
    assert len(store.activity) == 2
    assert store.activity[-1].action == "ADD"


def test_update_and_delete():
    store = ApplicationStore()
    app = store.add(Application(company="A", status="Pending"))
    store.update(app.id, {"status": "1st Interview"})
    assert app.status == "1st Interview"
    assert any("status" in entry.detail for entry in store.activity)

    assert store.delete(app.id) is True
    assert store.delete(app.id) is False
    assert len(store) == 0


def test_load_many_assigns_new_ids():
    store = ApplicationStore()
    count = store.load_many([Application(company="X"), Application(company="Y")])
    assert count == 2
    assert [a.id for a in store.all()] == [1, 2]
    assert store.activity[-1].action == "IMPORT"
