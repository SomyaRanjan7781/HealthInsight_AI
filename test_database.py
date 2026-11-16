
import os
import tempfile
import unittest

from unittest.mock import patch

from database import (
    add_patient,
    delete_patient,
    get_patient,
    init_db,
    list_patients,
    update_patient_email,
    update_patient_remarks,
)


class DatabaseTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.db_path = os.path.join(
            self.temp_dir.name,
            "healthinsight_test.db",
        )

        self.env_patch = patch.dict(
            os.environ,
            {"DATABASE_PATH": self.db_path},
        )

        self.env_patch.start()
        init_db()

        self.patient = {
            "full_name": "Unit Test Patient",
            "dob": "1960-01-28",
            "email": "unit.test@assessment.invalid",
            "glucose": 120.0,
            "haemoglobin": 13.5,
            "cholesterol": 180.0,
        }

    def tearDown(self):
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def test_create_read_update_delete(self):

        first_id = add_patient(
            self.patient,
            "Pending",
            "Pending",
        )

        second_id = add_patient(
            self.patient,
            "Pending",
            "Pending",
        )

        self.assertEqual(
            (first_id, second_id),
            (1, 2),
        )

        self.assertEqual(
            len(list_patients()),
            2,
        )

        self.assertEqual(
            get_patient(first_id)["email"],
            self.patient["email"],
        )

        update_patient_email(
            first_id,
            "updated@assessment.invalid",
        )

        self.assertEqual(
            get_patient(first_id)["email"],
            "updated@assessment.invalid",
        )

        update_patient_remarks(
            first_id,
            "Informational remarks",
            "Generated",
        )

        self.assertEqual(
            get_patient(first_id)["ai_status"],
            "Generated",
        )

        delete_patient(second_id)

        self.assertEqual(
            [row["id"] for row in list_patients()],
            [first_id],
        )

    def test_id_resets_only_after_all_records_are_deleted(self):

        first_id = add_patient(
            self.patient,
            "Pending",
            "Pending",
        )

        second_id = add_patient(
            self.patient,
            "Pending",
            "Pending",
        )

        delete_patient(first_id)

        third_id = add_patient(
            self.patient,
            "Pending",
            "Pending",
        )

        self.assertEqual(third_id, 3)

        delete_patient(second_id)
        delete_patient(third_id)

        new_first_id = add_patient(
            self.patient,
            "Pending",
            "Pending",
        )

        self.assertEqual(new_first_id, 1)

    def test_init_db_resets_sequence_if_table_is_empty(self):

        first_id = add_patient(
            self.patient,
            "Pending",
            "Pending",
        )

        delete_patient(first_id)
        init_db()

        self.assertEqual(
            add_patient(
                self.patient,
                "Pending",
                "Pending",
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
