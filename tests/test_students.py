from datetime import date, timedelta
from app.models import Student


def test_create_valid_student(client):
    payload = {
        "name": "Ananya Sharma",
        "date_of_birth": "2003-05-15",
        "email": "ananya.sharma@example.com",
        "phone": "+91 98765 43210",
        "course": "Artificial Intelligence & ML",
        "address": "Bangalore, Karnataka",
        "enrollment_date": "2024-07-01",
    }
    resp = client.post("/students", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Ananya Sharma"
    assert data["email"] == "ananya.sharma@example.com"
    assert data["id"] is not None


def test_create_student_with_only_email(client):
    payload = {
        "name": "Kiran Kumar",
        "date_of_birth": "2002-04-10",
        "email": "kiran.kumar@example.com",
    }
    resp = client.post("/students", json=payload)
    assert resp.status_code == 201
    assert resp.json()["phone"] is None


def test_create_student_with_only_phone(client):
    payload = {
        "name": "Priya Nair",
        "date_of_birth": "2004-01-20",
        "phone": "+91 91234 56789",
    }
    resp = client.post("/students", json=payload)
    assert resp.status_code == 201
    assert resp.json()["email"] is None


def test_reject_missing_name(client):
    payload = {
        "name": "   ",
        "date_of_birth": "2003-05-15",
        "email": "valid@example.com",
    }
    resp = client.post("/students", json=payload)
    assert resp.status_code == 422


def test_reject_invalid_email(client):
    payload = {
        "name": "Test Student",
        "date_of_birth": "2003-05-15",
        "email": "not-a-valid-email",
    }
    resp = client.post("/students", json=payload)
    assert resp.status_code == 422


def test_reject_future_date_of_birth(client):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    payload = {
        "name": "Future Baby",
        "date_of_birth": tomorrow,
        "email": "future@example.com",
    }
    resp = client.post("/students", json=payload)
    assert resp.status_code == 422


def test_reject_missing_both_email_and_phone(client):
    payload = {
        "name": "No Contact",
        "date_of_birth": "2002-03-03",
        "course": "DevOps",
    }
    resp = client.post("/students", json=payload)
    assert resp.status_code == 422


def test_reject_duplicate_email(client):
    payload = {
        "name": "Student One",
        "date_of_birth": "2001-01-01",
        "email": "unique.email@example.com",
    }
    r1 = client.post("/students", json=payload)
    assert r1.status_code == 201

    payload2 = {
        "name": "Student Two",
        "date_of_birth": "2002-02-02",
        "email": "unique.email@example.com",
    }
    r2 = client.post("/students", json=payload2)
    assert r2.status_code == 400


def test_list_students_and_pagination(client):
    for i in range(5):
        client.post(
            "/students",
            json={
                "name": f"Batch Student {i}",
                "date_of_birth": "2002-01-01",
                "email": f"batch_{i}@example.com",
            },
        )
    resp = client.get("/students?page=1&limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["limit"] == 2


def test_search_by_name_case_insensitive(client):
    client.post(
        "/students",
        json={
            "name": "Vikramaditya Rao",
            "date_of_birth": "2000-10-10",
            "email": "vikram@example.com",
        },
    )
    resp = client.get("/students?search=vikram")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("Vikramaditya" in s["name"] for s in items)


def test_filter_by_course(client):
    client.post(
        "/students",
        json={
            "name": "AI Specialist",
            "date_of_birth": "2002-05-05",
            "email": "ai.expert@example.com",
            "course": "Robotics & AI",
        },
    )
    resp = client.get("/students?course=Robotics & AI")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(s["course"] == "Robotics & AI" for s in items)


def test_get_student_by_id(client):
    create_res = client.post(
        "/students",
        json={
            "name": "Fetch Me",
            "date_of_birth": "2003-03-03",
            "email": "fetch@example.com",
        },
    )
    s_id = create_res.json()["id"]

    resp = client.get(f"/students/{s_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Fetch Me"


def test_get_nonexistent_student_returns_404(client):
    resp = client.get("/students/999999")
    assert resp.status_code == 404


def test_update_student_put(client):
    create_res = client.post(
        "/students",
        json={
            "name": "Original Name",
            "date_of_birth": "2002-02-02",
            "email": "put.test@example.com",
        },
    )
    s_id = create_res.json()["id"]

    put_payload = {
        "name": "Updated Name",
        "date_of_birth": "2001-01-01",
        "email": "put.test@example.com",
        "phone": "+91 99999 88888",
        "course": "Updated Course",
    }
    resp = client.put(f"/students/{s_id}", json=put_payload)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"
    assert resp.json()["course"] == "Updated Course"


def test_patch_student_partial_update(client):
    create_res = client.post(
        "/students",
        json={
            "name": "Patch Target",
            "date_of_birth": "2003-07-07",
            "email": "patch.target@example.com",
            "course": "Old Course",
        },
    )
    s_id = create_res.json()["id"]

    patch_payload = {"course": "New Course"}
    resp = client.patch(f"/students/{s_id}", json=patch_payload)
    assert resp.status_code == 200
    assert resp.json()["course"] == "New Course"
    assert resp.json()["name"] == "Patch Target"


def test_patch_student_rejects_removing_all_contacts(client):
    create_res = client.post(
        "/students",
        json={
            "name": "Contact Holder",
            "date_of_birth": "2003-07-07",
            "email": "holder@example.com",
        },
    )
    s_id = create_res.json()["id"]

    resp = client.patch(f"/students/{s_id}", json={"email": None, "phone": None})
    assert resp.status_code == 422


def test_delete_student_and_subsequent_get(client):
    create_res = client.post(
        "/students",
        json={
            "name": "To Delete",
            "date_of_birth": "2004-04-04",
            "email": "delete.me@example.com",
        },
    )
    s_id = create_res.json()["id"]

    del_resp = client.delete(f"/students/{s_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/students/{s_id}")
    assert get_resp.status_code == 404


def test_delete_nonexistent_student_returns_404(client):
    resp = client.delete("/students/999999")
    assert resp.status_code == 404


def test_get_stats_summary(client):
    resp = client.get("/students/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_students" in data
    assert "total_courses" in data
    assert "course_distribution" in data


def test_database_persistence_across_reconnection(db_session):
    student = Student(
        name="Persistence Test",
        date_of_birth=date(2000, 1, 1),
        email="persist@example.com",
        course="Systems Engineering",
    )
    db_session.add(student)
    db_session.commit()
    s_id = student.id

    fetched = db_session.query(Student).filter(Student.id == s_id).first()
    assert fetched is not None
    assert fetched.name == "Persistence Test"
