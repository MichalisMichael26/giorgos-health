from datetime import date, time
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import MoodEntry


class MoodJournalTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(username="parent-mood-test", password="test-secret-2026")
        self.client.force_login(self.parent)

    def test_add_edit_and_delete_mood(self):
        response = self.client.post(reverse("mood_create"), {
            "date": "2026-10-10", "time": "15:25", "mood": "happy",
            "notes": "Χαμογελούσε και έπαιζε",
        })
        self.assertRedirects(response, reverse("mood_list"))
        entry = MoodEntry.objects.get()
        self.assertEqual(entry.created_by, self.parent)
        self.assertEqual(entry.mood, "happy")
        self.assertEqual(entry.time, time(15, 25))
        self.assertContains(self.client.get(reverse("mood_list")), "Χαμογελούσε")
        response = self.client.post(reverse("mood_edit", args=[entry.pk]), {
            "date": "2026-10-10", "time": "15:35", "mood": "calm", "notes": "",
        })
        self.assertRedirects(response, reverse("mood_list"))
        entry.refresh_from_db()
        self.assertEqual(entry.mood, "calm")
        self.assertEqual(entry.time, time(15, 35))
        response = self.client.post(reverse("mood_delete", args=[entry.pk]))
        self.assertRedirects(response, reverse("mood_list"))
        self.assertFalse(MoodEntry.objects.exists())

    def test_mood_choice_is_required(self):
        response = self.client.post(reverse("mood_create"), {
            "date": "2026-10-10", "time": "15:25", "mood": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MoodEntry.objects.count(), 0)

    def test_doctor_cannot_modify(self):
        doctor = User.objects.create_user(username="drsavvas", password="test-secret-2026")
        self.client.force_login(doctor)
        self.assertEqual(self.client.get(reverse("mood_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("mood_create")).status_code, 302)
        self.assertEqual(self.client.post(reverse("mood_create"), {
            "date": "2026-10-10", "time": "15:25", "mood": "happy",
        }).status_code, 403)
        self.assertFalse(MoodEntry.objects.exists())
