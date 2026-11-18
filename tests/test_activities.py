import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import activities, app


class ActivityApiTests(unittest.TestCase):
    def setUp(self):
        test_activities = {
            "Chess Club": {
                "description": "Chess",
                "schedule": "Friday",
                "max_participants": 2,
                "participants": ["existing@example.com"],
            }
        }
        activities_patch = patch.dict(activities, test_activities, clear=True)
        activities_patch.start()
        self.addCleanup(activities_patch.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_root_redirects_to_frontend(self):
        response = self.client.get("/", follow_redirects=False)

        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], "/static/index.html")

    def test_list_activities_returns_activity_details(self):
        response = self.client.get("/activities")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "Chess Club": {
                    "description": "Chess",
                    "schedule": "Friday",
                    "max_participants": 2,
                    "participants": ["existing@example.com"],
                }
            },
        )

    def test_signup_adds_participant_and_is_visible_in_activity_listing(self):
        email = "student+chess@example.com"
        response = self.client.post("/activities/Chess%20Club/signup", params={"email": email})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": f"Signed up {email} for Chess Club"})
        self.assertEqual(
            self.client.get("/activities").json()["Chess Club"]["participants"],
            ["existing@example.com", email],
        )

    def test_signup_rejects_duplicate_without_changing_participants(self):
        response = self.client.post(
            "/activities/Chess%20Club/signup", params={"email": "existing@example.com"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Student already signed up for this activity")
        self.assertEqual(activities["Chess Club"]["participants"], ["existing@example.com"])

    def test_signup_rejects_full_activity_without_changing_participants(self):
        activities["Chess Club"]["participants"].append("second@example.com")
        response = self.client.post(
            "/activities/Chess%20Club/signup", params={"email": "another@example.com"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Activity is full")
        self.assertEqual(
            activities["Chess Club"]["participants"], ["existing@example.com", "second@example.com"]
        )

    def test_signup_rejects_unknown_activity(self):
        response = self.client.post("/activities/Unknown/signup", params={"email": "new@example.com"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Activity not found")
        self.assertEqual(activities["Chess Club"]["participants"], ["existing@example.com"])

    def test_signup_requires_email(self):
        response = self.client.post("/activities/Chess%20Club/signup")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"][0]["loc"], ["query", "email"])
        self.assertEqual(activities["Chess Club"]["participants"], ["existing@example.com"])


if __name__ == "__main__":
    unittest.main()
