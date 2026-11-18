import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import activities, app


class UnregisterTests(unittest.TestCase):
    def setUp(self):
        self.activities = {
            "Chess Club": {
                "description": "Chess",
                "schedule": "Friday",
                "max_participants": 3,
                "participants": ["student+chess@example.com", "other@example.com"],
            },
            "Art Club": {
                "description": "Art",
                "schedule": "Monday",
                "max_participants": 3,
                "participants": ["student+chess@example.com"],
            },
        }
        self.activities_patch = patch.dict(activities, self.activities, clear=True)
        self.activities_patch.start()
        self.addCleanup(self.activities_patch.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_unregister_removes_only_the_selected_activity_participant(self):
        response = self.client.delete(
            "/activities/Chess%20Club/signup", params={"email": "student+chess@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(activities["Chess Club"]["participants"], ["other@example.com"])
        self.assertEqual(activities["Art Club"]["participants"], ["student+chess@example.com"])

    def test_unregister_removes_duplicate_entries(self):
        activities["Chess Club"]["participants"].append("student+chess@example.com")

        response = self.client.delete(
            "/activities/Chess%20Club/signup", params={"email": "student+chess@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(activities["Chess Club"]["participants"], ["other@example.com"])

    def test_unregister_unknown_activity_or_participant(self):
        unknown_activity = self.client.delete(
            "/activities/Unknown/signup", params={"email": "student@example.com"}
        )
        unknown_participant = self.client.delete(
            "/activities/Chess%20Club/signup", params={"email": "missing@example.com"}
        )

        self.assertEqual(unknown_activity.status_code, 404)
        self.assertEqual(unknown_activity.json()["detail"], "Activity not found")
        self.assertEqual(unknown_participant.status_code, 404)
        self.assertEqual(
            unknown_participant.json()["detail"], "Student is not signed up for this activity"
        )
        self.assertEqual(
            activities["Chess Club"]["participants"],
            ["student+chess@example.com", "other@example.com"],
        )

    def test_unregister_requires_email(self):
        response = self.client.delete("/activities/Chess%20Club/signup")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"][0]["loc"], ["query", "email"])
        self.assertEqual(
            activities["Chess Club"]["participants"],
            ["student+chess@example.com", "other@example.com"],
        )


if __name__ == "__main__":
    unittest.main()
