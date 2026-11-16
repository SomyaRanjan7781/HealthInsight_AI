
from __future__ import annotations

import re

from google import genai
from google.genai import types


class AIServiceError(Exception):
    def __init__(self, public_message: str) -> None:
        super().__init__(public_message)
        self.public_message = public_message


def build_health_prompt(patient: dict) -> str:
    age = int(patient["age"])
    glucose = float(patient["glucose"])
    haemoglobin = float(patient["haemoglobin"])
    cholesterol = float(patient["cholesterol"])

    return f"""Prepare concise, cautious, educational remarks for a fictional health-record software assessment.

Measurements supplied:
Age: {age} years
Glucose: {glucose:g} mg/dL
Haemoglobin: {haemoglobin:g} g/dL
Total cholesterol: {cholesterol:g} mg/dL

The assessment data does not specify measurement units, fasting status, sex, symptoms, medical history, medication, or laboratory reference ranges. The units shown above are assumptions for this demonstration and must be confirmed against the original laboratory report.

Do not diagnose any disease, prescribe medication, recommend a dosage, calculate a clinical risk score, or invent missing information. Explain that glucose interpretation depends on fasting status and clinical context; haemoglobin interpretation depends on relevant patient context and laboratory ranges; and total cholesterol alone is not enough for a complete cardiovascular risk assessment. Describe potentially concerning values only as reasons to seek qualified professional review.

Write plain text only. Do not use Markdown, hash symbols, asterisks, bold formatting, bullet symbols, tables, or code fences. Use these five numbered section titles on separate lines:
1. Informational Summary
2. Possible Risk Considerations
3. Missing Clinical Context
4. Suggested Next Step
5. Safety Disclaimer

Keep the tone professional, calm, and non-alarming. State that the output is informational, is not a diagnosis, and requires review by a qualified healthcare professional."""


def clean_remarks_text(text: str) -> str:
    text = text.replace("```", "")
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"(?m)^\s*[-*•]\s+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def generate_health_remarks(
    patient: dict,
    api_key: str,
    model: str = "gemini-3.6-flash",
) -> str:
    if not api_key or not api_key.strip():
        raise AIServiceError("Gemini API key is not configured.")

    client = None

    try:
        client = genai.Client(
            api_key=api_key.strip(),
            http_options=types.HttpOptions(timeout=90000),
        )

        response = client.models.generate_content(
            model=model,
            contents=build_health_prompt(patient),
            config=types.GenerateContentConfig(
                max_output_tokens=1200,
                temperature=0.2,
                thinking_config=types.ThinkingConfig(
                    thinking_level="minimal"
                ),
            ),
        )

        remarks = clean_remarks_text(response.text or "")

        if not remarks:
            raise AIServiceError(
                "Gemini returned no readable remarks. Please retry the request."
            )

        return remarks

    except AIServiceError:
        raise

    except Exception as exc:
        error_type = type(exc).__name__

        raise AIServiceError(
            f"Gemini request failed ({error_type}). "
            "Check API access, model availability, connection, and quota."
        ) from exc

    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
