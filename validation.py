
from __future__ import annotations

import math
import re

from datetime import date, datetime
from typing import Any


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def validate_email_address(
    value: Any,
) -> tuple[str | None, str | None]:

    email = str(value or "").strip()

    if not email:
        return None, "Email Address is required."

    if len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
        return None, "Please enter a valid email address."

    return email, None


def parse_date_of_birth(
    value: Any,
) -> tuple[str | None, str | None]:

    raw = str(value or "").strip()

    if not raw:
        return None, "Date of Birth is required."

    parsed = None

    for date_format in ("%d.%m.%Y", "%d/%m/%Y"):
        try:
            parsed = datetime.strptime(raw, date_format).date()
            break
        except ValueError:
            continue

    if parsed is None:
        return None, (
            "Date of Birth must be a real date in "
            "DD.MM.YYYY or DD/MM/YYYY format."
        )

    if parsed > date.today():
        return None, "Date of Birth cannot be in the future."

    return parsed.isoformat(), None


def parse_positive_number(
    value: Any,
    field_name: str,
) -> tuple[float | None, str | None]:

    if value is None or str(value).strip() == "":
        return None, f"{field_name} is required."

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, f"{field_name} must be numeric."

    if not math.isfinite(number):
        return None, f"{field_name} must be a finite number."

    if number <= 0:
        return None, f"{field_name} must be greater than zero."

    return number, None


def validate_patient_data(
    data: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:

    errors: list[str] = []
    cleaned: dict[str, Any] = {}

    full_name = str(data.get("full_name", "")).strip()

    if len(full_name) < 2:
        errors.append(
            "Full Name must contain at least two characters."
        )
    else:
        cleaned["full_name"] = full_name

    dob, dob_error = parse_date_of_birth(data.get("dob"))

    if dob_error:
        errors.append(dob_error)
    else:
        cleaned["dob"] = dob

    email, email_error = validate_email_address(
        data.get("email")
    )

    if email_error:
        errors.append(email_error)
    else:
        cleaned["email"] = email

    for field in ("glucose", "haemoglobin", "cholesterol"):
        number, error = parse_positive_number(
            data.get(field),
            field.capitalize(),
        )

        if error:
            errors.append(error)
        else:
            cleaned[field] = number

    return cleaned, errors


def calculate_age(
    iso_dob: str,
    reference_date: date | None = None,
) -> int:

    dob = date.fromisoformat(iso_dob)
    today = reference_date or date.today()

    return (
        today.year
        - dob.year
        - ((today.month, today.day) < (dob.month, dob.day))
    )
