"""TEST-ONLY: formatos regionais de data sem Qt, Ollama ou arquivos do usuário."""
import unittest

from archivia.date_formats import parse_user_date, display_date, display_timestamp, DATE_FORMATS


class DateFormatsTests(unittest.TestCase):
    def test_parse_formats_into_same_iso_day(self):
        for key, value in [
            ("br", "31/12/2024"),
            ("iso", "2024-12-31"),
            ("us", "12/31/2024"),
        ]:
            with self.subTest(format=key):
                self.assertEqual(parse_user_date(value, key), "2024-12-31")
                self.assertEqual(display_date("2024-12-31", key), value)
        self.assertEqual(set(DATE_FORMATS), {"br", "iso", "us"})

    def test_display_timestamp_in_utc(self):
        original = "2024-12-31T20:15:30+00:00"
        self.assertEqual(display_timestamp(original, "br"), "31/12/2024 20:15:30 UTC")
        self.assertEqual(display_timestamp(original, "iso"), "2024-12-31 20:15:30 UTC")
        self.assertEqual(display_timestamp(original, "us"), "12/31/2024 20:15:30 UTC")

    def test_empty_date_and_reject_invalid_or_ambiguous(self):
        self.assertEqual(parse_user_date("", "br"), "")
        for value, key in [
            ("31/02/2024", "br"),
            ("13/12/2024", "us"),
            ("2024-12-31", "br"),
            ("01/01/24", "br"),
            ("2024-1-01", "iso"),
        ]:
            with self.subTest(value=value, format=key):
                with self.assertRaises(ValueError):
                    parse_user_date(value, key)
        with self.assertRaises(ValueError):
            parse_user_date("31/12/2024", "unknown")


if __name__ == "__main__":
    unittest.main()
