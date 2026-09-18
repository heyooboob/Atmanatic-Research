import unittest

from atmanatic_research import TimestampError, parse_rfc3339


class Rfc3339TimestampTests(unittest.TestCase):
    def test_z_suffix_is_accepted_as_utc(self):
        parsed = parse_rfc3339("2026-09-17T12:00:00Z", "created_at")
        self.assertIsNotNone(parsed.tzinfo)

    def test_explicit_offset_is_accepted(self):
        parsed = parse_rfc3339("2026-09-17T12:00:00+05:00", "created_at")
        self.assertIsNotNone(parsed.tzinfo)

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaisesRegex(TimestampError, "explicit UTC offset"):
            parse_rfc3339("2026-09-17T12:00:00", "created_at")

    def test_non_string_is_rejected(self):
        with self.assertRaises(TimestampError):
            parse_rfc3339(12345, "created_at")

    def test_malformed_string_is_rejected(self):
        with self.assertRaises(TimestampError):
            parse_rfc3339("not-a-timestamp", "created_at")

    def test_empty_string_is_rejected(self):
        with self.assertRaises(TimestampError):
            parse_rfc3339("   ", "created_at")


if __name__ == "__main__":
    unittest.main()
