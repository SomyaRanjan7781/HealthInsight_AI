
import unittest

from datetime import date, timedelta

from validation import (
    calculate_age,
    parse_date_of_birth,
    validate_email_address,
    validate_patient_data,
)


class ValidationTests(unittest.TestCase):

    def valid_record(self):
        return {
            "full_name": "Assessment Patient",
            "dob": "28.01.1960",
            "email": "patient@example.com",
            "glucose": 120,
            "haemoglobin": 13.5,
            "cholesterol": 180,
        }

    def test_valid_patient_record(self):
        cleaned, errors = validate_patient_data(
            self.valid_record()
        )

        self.assertEqual(errors, [])
        self.assertEqual(cleaned["full_name"], "Assessment Patient")
        self.assertEqual(cleaned["dob"], "1960-01-28")
        self.assertEqual(cleaned["email"], "patient@example.com")
        self.assertEqual(cleaned["glucose"], 120.0)

    def test_accepts_slash_date_format(self):
        parsed, error = parse_date_of_birth("28/01/1960")

        self.assertEqual(parsed, "1960-01-28")
        self.assertIsNone(error)

    def test_rejects_invalid_email(self):
        email, error = validate_email_address("hunter@gmail")

        self.assertIsNone(email)
        self.assertIsNotNone(error)

    def test_rejects_email_without_at_symbol(self):
        email, error = validate_email_address(
            "Kris.wu.gmail.com"
        )

        self.assertIsNone(email)
        self.assertIsNotNone(error)

    def test_rejects_impossible_calendar_date(self):
        parsed, error = parse_date_of_birth("31.11.2001")

        self.assertIsNone(parsed)
        self.assertIsNotNone(error)

    def test_rejects_future_date(self):
        future_date = date.today() + timedelta(days=30)
        future_date_text = future_date.strftime("%d.%m.%Y")

        parsed, error = parse_date_of_birth(future_date_text)

        self.assertIsNone(parsed)
        self.assertIn("future", error.lower())

    def test_allows_duplicate_email_values(self):
        first = self.valid_record()
        second = self.valid_record()

        first_cleaned, first_errors = validate_patient_data(first)
        second_cleaned, second_errors = validate_patient_data(second)

        self.assertEqual(first_errors, [])
        self.assertEqual(second_errors, [])
        self.assertEqual(
            first_cleaned["email"],
            second_cleaned["email"],
        )

    def test_calculates_age_correctly(self):
        reference_date = date(2026, 11, 15)

        age_before_birthday = calculate_age(
            "2000-11-16",
            reference_date,
        )

        age_after_birthday = calculate_age(
            "2000-11-14",
            reference_date,
        )

        self.assertEqual(age_before_birthday, 25)
        self.assertEqual(age_after_birthday, 26)


if __name__ == "__main__":
    unittest.main()
