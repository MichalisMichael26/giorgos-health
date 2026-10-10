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
            "date": "2026-10-10", "time": "15:25",
            "moods": ["happy", "playful", "calm"],
            "notes": "Χαμογελούσε και έπαιζε",
        })
        self.assertRedirects(response, reverse("mood_list"))
        entry = MoodEntry.objects.get()
        self.assertEqual(entry.created_by, self.parent)
        self.assertEqual(entry.mood, "happy")
        self.assertEqual(entry.additional_moods, ["playful", "calm"])
        self.assertEqual([m["code"] for m in entry.mood_labels], ["playful", "happy", "calm"])
        self.assertEqual(entry.time, time(15, 25))
        self.assertContains(self.client.get(reverse("mood_list")), "Παιχνιδιάρης")
        self.assertContains(self.client.get(reverse("mood_list")), "Ήρεμος")
        response = self.client.post(reverse("mood_edit", args=[entry.pk]), {
            "date": "2026-10-10", "time": "15:35", "moods": ["calm", "scared"],
            "notes": "",
        })
        self.assertRedirects(response, reverse("mood_list"))
        entry.refresh_from_db()
        self.assertEqual(entry.mood, "calm")
        self.assertEqual(entry.additional_moods, ["scared"])
        self.assertEqual(entry.time, time(15, 35))
        response = self.client.post(reverse("mood_delete", args=[entry.pk]))
        self.assertRedirects(response, reverse("mood_list"))
        self.assertFalse(MoodEntry.objects.exists())

    def test_extended_infant_moods_are_saved(self):
        for code in ("scared", "sleepy", "crying", "uncomfortable", "playful", "very_playful"):
            with self.subTest(mood=code):
                response = self.client.post(reverse("mood_create"), {
                    "date": "2026-10-10", "time": "15:25", "moods": [code],
                })
                self.assertRedirects(response, reverse("mood_list"))
                entry = MoodEntry.objects.filter(mood=code).latest("pk")
                self.assertEqual(entry.get_mood_display(), dict(MoodEntry.MOOD_CHOICES)[code])

    def test_moods_are_grouped_from_playful_to_distressed(self):
        expected = [
            "very_playful", "playful", "happy",
            "calm", "sleepy",
            "restless", "fussy", "sad", "scared", "crying", "uncomfortable",
        ]
        self.assertEqual([code for code, _ in MoodEntry.MOOD_CHOICES], expected)
        response = self.client.get(reverse("mood_create"))
        self.assertContains(response, "🌞 Χαρά &amp; παιχνίδι")
        self.assertContains(response, "🌿 Ηρεμία &amp; κούραση")
        self.assertContains(response, "🌥️ Ανησυχία &amp; δυσφορία")
        markup = response.content.decode()
        self.assertLess(markup.index("Πολύ παιχνιδιάρης"), markup.index("Παιχνιδιάρης"))
        self.assertLess(markup.index("Παιχνιδιάρης"), markup.index("Ήρεμος"))
        self.assertLess(markup.index("Ήρεμος"), markup.index("Ανήσυχος"))
        self.assertLess(markup.index("Ανήσυχος"), markup.index("Δείχνει δυσφορία"))

    def test_existing_record_displays_in_hierarchy_without_changing_data(self):
        entry = MoodEntry.objects.create(
            date=date(2026, 10, 9), time=time(12, 0),
            mood="sad", additional_moods=["happy", "scared"],
        )
        self.assertEqual(
            [m["code"] for m in entry.mood_labels],
            ["happy", "sad", "scared"],
        )
        entry.refresh_from_db()
        self.assertEqual(entry.mood, "sad")
        self.assertEqual(entry.additional_moods, ["happy", "scared"])

    def test_requires_at_least_one_mood(self):
        response = self.client.post(reverse("mood_create"), {
            "date": "2026-10-10", "time": "15:25", "moods": [],
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "τουλάχιστον μία διάθεση")
        self.assertFalse(MoodEntry.objects.exists())

    def test_four_moods_rejected_on_server(self):
        response = self.client.post(reverse("mood_create"), {
            "date": "2026-10-10", "time": "15:25",
            "moods": ["happy", "calm", "fussy", "scared"],
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "το πολύ 3")
        self.assertFalse(MoodEntry.objects.exists())

    def test_existing_single_mood_is_preserved(self):
        entry = MoodEntry.objects.create(date=date(2026, 10, 9), time=time(10, 30), mood="calm")
        response = self.client.get(reverse("mood_edit", args=[entry.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "checked")
        self.assertEqual(entry.mood_labels, [{"code": "calm", "label": "😌 Ήρεμος"}])

    def test_doctor_cannot_modify(self):
        doctor = User.objects.create_user(username="drsavvas", password="test-secret-2026")
        self.client.force_login(doctor)
        self.assertEqual(self.client.get(reverse("mood_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("mood_create")).status_code, 302)
        self.assertEqual(self.client.post(reverse("mood_create"), {
            "date": "2026-10-10", "time": "15:25", "moods": ["happy", "calm"],
        }).status_code, 403)
        self.assertFalse(MoodEntry.objects.exists())
