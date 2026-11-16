
from __future__ import annotations

import os
from datetime import date

import pandas as pd
import streamlit as st

from ai_service import (
    AIServiceError,
    clean_remarks_text,
    generate_health_remarks,
)
from database import (
    add_patient,
    delete_patient,
    get_patient,
    init_db,
    list_patients,
    update_patient_email,
    update_patient_remarks,
)
from validation import (
    calculate_age,
    validate_email_address,
    validate_patient_data,
)

DEFAULT_MODEL = "gemini-3.6-flash"

st.set_page_config(
    page_title="HealthInsight AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
        if value:
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, default).strip()


def display_date(iso_date: str) -> str:
    try:
        return date.fromisoformat(iso_date).strftime("%d.%m.%Y")
    except (TypeError, ValueError):
        return str(iso_date)


def safe_generate_remarks(patient: dict) -> tuple[str, str]:
    api_key = get_secret("GEMINI_API_KEY")
    model = get_secret("GEMINI_MODEL", DEFAULT_MODEL)

    if not api_key:
        return (
            "AI remarks are pending. Configure the Gemini API key, "
            "then retry from Patient Records.",
            "Pending",
        )

    try:
        ai_patient = dict(patient)

        if "age" not in ai_patient and ai_patient.get("dob"):
            ai_patient["age"] = calculate_age(ai_patient["dob"])

        return (
            generate_health_remarks(ai_patient, api_key, model),
            "Generated",
        )

    except AIServiceError as exc:
        return (
            "AI remarks could not be generated. The patient record "
            "is saved; retry from Patient Records after checking API access.",
            f"Failed: {exc.public_message}",
        )


def patient_label(patient: dict) -> str:
    return (
        f"ID {patient['id']} · "
        f"{patient['full_name']} · "
        f"{patient['email']}"
    )


def render_patient_table(records: list[dict]) -> None:
    if not records:
        st.info("No patient records have been created yet.")
        return

    rows = []

    for row in records:
        full_remarks = " ".join(
            clean_remarks_text(
                row["remarks"] or "Pending"
            ).split()
        )

        preview = (
            full_remarks
            if len(full_remarks) <= 115
            else full_remarks[:112].rstrip() + "..."
        )

        rows.append(
            {
                "ID": row["id"],
                "Full Name": row["full_name"],
                "Date of Birth": display_date(row["dob"]),
                "Email Address": row["email"],
                "Glucose": row["glucose"],
                "Haemoglobin": row["haemoglobin"],
                "Cholesterol": row["cholesterol"],
                "AI Remarks (Preview)": preview,
                "AI Status": row["ai_status"],
            }
        )

    frame = pd.DataFrame(rows)

    st.dataframe(
        frame,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn(
                "ID", width="small", format="%d"
            ),
            "Full Name": st.column_config.TextColumn(
                "Full Name", width="medium"
            ),
            "Date of Birth": st.column_config.TextColumn(
                "Date of Birth", width="small"
            ),
            "Email Address": st.column_config.TextColumn(
                "Email Address", width="medium"
            ),
            "Glucose": st.column_config.NumberColumn(
                "Glucose", width="small", format="%.2f"
            ),
            "Haemoglobin": st.column_config.NumberColumn(
                "Haemoglobin", width="small", format="%.2f"
            ),
            "Cholesterol": st.column_config.NumberColumn(
                "Cholesterol", width="small", format="%.2f"
            ),
            "AI Remarks (Preview)": st.column_config.TextColumn(
                "AI Remarks (Preview)", width="large"
            ),
            "AI Status": st.column_config.TextColumn(
                "AI Status", width="small"
            ),
        },
    )

    with st.expander("View complete AI remarks"):
        selected_record = st.selectbox(
            "Select a patient record",
            records,
            format_func=patient_label,
            key="full_remarks_patient",
        )

        st.write(
            clean_remarks_text(
                selected_record["remarks"] or "AI remarks are pending."
            )
        )


def handle_ai_retry(patient_id: int) -> None:
    patient = get_patient(patient_id)

    if patient is None:
        st.error("The selected patient record no longer exists.")
        return

    with st.spinner("Requesting Gemini AI remarks..."):
        remarks, status = safe_generate_remarks(patient)

        update_patient_remarks(
            patient_id,
            remarks,
            status,
        )

    if status == "Generated":
        st.success("AI remarks generated and saved.")
    else:
        st.warning(remarks)

    st.rerun()


init_db()

if st.session_state.pop("_clear_add_patient_form", False):
    st.session_state["add_full_name"] = ""
    st.session_state["add_dob"] = ""
    st.session_state["add_email"] = ""
    st.session_state["add_glucose"] = 0.0
    st.session_state["add_haemoglobin"] = 0.0
    st.session_state["add_cholesterol"] = 0.0


st.markdown(
    """
    <style>
      .stApp {
          background:
              radial-gradient(
                  circle at 8% 0%,
                  rgba(44, 95, 170, .13),
                  transparent 30%
              ),
              radial-gradient(
                  circle at 95% 8%,
                  rgba(18, 150, 151, .08),
                  transparent 26%
              );
      }

      .block-container {
          max-width: 1480px;
          padding-top: 1.4rem;
          padding-bottom: 2.8rem;
      }

      [data-testid="stSidebar"] {
          background: linear-gradient(
              180deg,
              #111b2b 0%,
              #101722 100%
          );
          border-right: 1px solid rgba(148, 163, 184, .13);
      }

      [data-testid="stSidebar"] h1 {
          font-size: 1.25rem;
          letter-spacing: -.025em;
      }

      [data-testid="stSidebar"] [data-testid="stRadio"] label {
          padding-top: .18rem;
          padding-bottom: .18rem;
      }

      .app-hero {
          padding: 1.55rem 1.8rem 1.45rem;
          margin: .15rem 0 1.6rem;
          border: 1px solid rgba(125, 178, 220, .22);
          border-radius: 18px;
          background: linear-gradient(
              112deg,
              rgba(24, 48, 82, .96) 0%,
              rgba(23, 57, 83, .94) 58%,
              rgba(18, 75, 79, .90) 100%
          );
          box-shadow: 0 12px 32px rgba(0, 0, 0, .16);
      }

      .app-hero-eyebrow {
          color: #72e0d4;
          font-size: .72rem;
          font-weight: 750;
          letter-spacing: .16em;
          text-transform: uppercase;
          margin-bottom: .45rem;
      }

      .app-hero-title {
          color: #f8fbff;
          font-size: clamp(1.8rem, 3vw, 2.55rem);
          line-height: 1.15;
          font-weight: 800;
          letter-spacing: -.04em;
      }

      .app-hero-subtitle {
          color: #c1d6e8;
          margin-top: .55rem;
          font-size: .98rem;
      }

      h2, h3 {
          letter-spacing: -.025em;
      }

      [data-testid="stMetric"] {
          padding: 1rem 1.05rem;
          border: 1px solid rgba(125, 155, 190, .20);
          border-radius: 15px;
          background: linear-gradient(
              145deg,
              rgba(37, 53, 75, .62),
              rgba(23, 34, 50, .72)
          );
          box-shadow: 0 5px 18px rgba(0, 0, 0, .10);
      }

      [data-testid="stMetricLabel"] p {
          color: #a9c3dc;
          font-weight: 600;
      }

      [data-testid="stMetricValue"] {
          font-weight: 750;
          letter-spacing: -.035em;
      }

      div[data-testid="stForm"] {
          border: 1px solid rgba(125, 155, 190, .20);
          border-radius: 15px;
          padding: 1.15rem 1.2rem 1rem;
          background: rgba(30, 43, 61, .22);
      }

      div[data-testid="stTextInput"] input,
      div[data-testid="stNumberInput"] input,
      div[data-testid="stSelectbox"] > div,
      div[data-testid="stDateInput"] input {
          border-radius: 9px;
      }

      div.stButton > button,
      div[data-testid="stFormSubmitButton"] > button {
          border-radius: 10px;
          font-weight: 650;
          min-height: 2.65rem;
          transition: transform .15s ease, box-shadow .15s ease;
      }

      div.stButton > button:hover,
      div[data-testid="stFormSubmitButton"] > button:hover {
          transform: translateY(-1px);
          box-shadow: 0 5px 14px rgba(20, 120, 150, .18);
      }

      [data-testid="stDataFrame"] {
          border: 1px solid rgba(125, 155, 190, .18);
          border-radius: 12px;
          overflow: hidden;
      }

      hr {
          border-color: rgba(148, 163, 184, .16);
      }

      .app-footer {
          color: #8194a8;
          font-size: .82rem;
          padding-top: .25rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.title("🩺 HealthInsight AI")
    st.caption("Patient Records & AI-Assisted Health Insights")
    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Add Patient",
            "Patient Records",
            "About & Safety",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("Python · Streamlit · SQLite · Gemini")


st.markdown(
    """
    <div class="app-hero">
      <div class="app-hero-eyebrow">
        Patient management workspace
      </div>
      <div class="app-hero-title">
        🩺 HealthInsight AI
      </div>
      <div class="app-hero-subtitle">
        Patient records, streamlined workflows, and AI-assisted health insights.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


records = list_patients()


if page == "Overview":

    generated_count = sum(
        row["ai_status"] == "Generated"
        for row in records
    )

    pending_count = len(records) - generated_count

    col1, col2, col3 = st.columns(3)

    col1.metric("Total patient records", len(records))
    col2.metric("AI remarks generated", generated_count)
    col3.metric("Pending / failed AI", pending_count)

    st.subheader("Recent patient records")
    render_patient_table(records[:8])


elif page == "Add Patient":

    st.subheader("Add a new patient")

    st.caption(
        "Date of Birth accepts DD.MM.YYYY or DD/MM/YYYY."
    )

    last_result = st.session_state.pop(
        "last_add_patient_result",
        None,
    )

    if last_result:
        st.success(
            f"Patient record #{last_result['id']} saved successfully."
        )

        if last_result["status"] == "Generated":
            st.success("Gemini AI remarks generated successfully.")
            st.markdown("**Generated remarks**")
            st.text(clean_remarks_text(last_result["remarks"]))
        else:
            st.warning(last_result["remarks"])

    with st.form(
        "add_patient_form",
        clear_on_submit=False,
    ):
        col1, col2 = st.columns(2)

        with col1:
            full_name = st.text_input(
                "Full Name",
                key="add_full_name",
            )

            dob_text = st.text_input(
                "Date of Birth",
                placeholder="DD.MM.YYYY",
                key="add_dob",
            )

            email = st.text_input(
                "Email Address",
                key="add_email",
            )

            glucose = st.number_input(
                "Glucose",
                min_value=0.0,
                value=0.0,
                step=1.0,
                format="%.2f",
                key="add_glucose",
            )

        with col2:
            haemoglobin = st.number_input(
                "Haemoglobin",
                min_value=0.0,
                value=0.0,
                step=0.1,
                format="%.2f",
                key="add_haemoglobin",
            )

            cholesterol = st.number_input(
                "Cholesterol",
                min_value=0.0,
                value=0.0,
                step=1.0,
                format="%.2f",
                key="add_cholesterol",
            )

            st.markdown("**AI Remarks**")
            st.caption(
                "Generated after valid patient details are saved."
            )

        submitted = st.form_submit_button(
            "Save Patient & Generate AI Remarks",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        payload = {
            "full_name": full_name,
            "dob": dob_text,
            "email": email,
            "glucose": glucose,
            "haemoglobin": haemoglobin,
            "cholesterol": cholesterol,
        }

        cleaned, errors = validate_patient_data(payload)

        if errors:
            st.error(
                "Please correct the following validation errors:"
            )

            for error in errors:
                st.write(f"• {error}")

        else:
            pending_remarks = (
                "AI remarks are being generated. If the request "
                "fails, retry from Patient Records."
            )

            new_id = add_patient(
                cleaned,
                pending_remarks,
                "Pending",
            )

            ai_payload = {
                **cleaned,
                "age": calculate_age(cleaned["dob"]),
            }

            with st.spinner(
                f"Patient record #{new_id} is saved. "
                "Requesting Gemini AI remarks..."
            ):
                remarks, ai_status = safe_generate_remarks(
                    ai_payload
                )

                update_patient_remarks(
                    new_id,
                    remarks,
                    ai_status,
                )

            st.session_state["last_add_patient_result"] = {
                "id": new_id,
                "remarks": remarks,
                "status": ai_status,
            }

            st.session_state["_clear_add_patient_form"] = True
            st.rerun()


elif page == "Patient Records":

    st.subheader("Patient records")

    st.caption(
        "Each saved entry has a unique record ID. "
        "Repeated names and email addresses are allowed."
    )

    records = list_patients()
    render_patient_table(records)

    if records:
        st.divider()
        st.subheader("Update a patient email")

        selected_for_edit = st.selectbox(
            "Choose a record to update",
            records,
            format_func=patient_label,
            key="edit_patient_select",
        )

        with st.form("edit_email_form"):
            new_email = st.text_input(
                "New Email Address",
                value=selected_for_edit["email"],
            )

            update_submitted = st.form_submit_button(
                "Update Email",
                type="primary",
            )

        if update_submitted:
            email_value, email_error = validate_email_address(
                new_email
            )

            if email_error:
                st.error(email_error)
            else:
                update_patient_email(
                    selected_for_edit["id"],
                    email_value,
                )

                st.success(
                    f"Email updated for record #{selected_for_edit['id']}."
                )
                st.rerun()

        st.divider()
        st.subheader("Delete a patient record")

        selected_for_delete = st.selectbox(
            "Choose a record to delete",
            records,
            format_func=patient_label,
            key="delete_patient_select",
        )

        confirm_delete = st.checkbox(
            f"I confirm deletion of record "
            f"#{selected_for_delete['id']}."
        )

        if st.button(
            "Delete Selected Record",
            type="secondary",
            disabled=not confirm_delete,
        ):
            delete_patient(selected_for_delete["id"])
            st.success(
                f"Record #{selected_for_delete['id']} deleted."
            )
            st.rerun()

        st.divider()
        st.subheader("Generate or retry AI remarks")

        ai_candidates = [
            row
            for row in records
            if row["ai_status"] != "Generated"
        ]

        if ai_candidates:
            retry_patient = st.selectbox(
                "Choose a record",
                ai_candidates,
                format_func=patient_label,
                key="retry_patient_select",
            )

            if st.button(
                "Regenerate AI Remarks",
                type="primary",
            ):
                handle_ai_retry(retry_patient["id"])

        else:
            st.caption(
                "All current records have generated AI remarks."
            )


elif page == "About & Safety":

    st.subheader("Application overview")

    st.write(
        "HealthInsight AI manages patient assessment records "
        "and generates informational remarks from blood-test "
        "values using an external Gemini API."
    )

    st.subheader("Data handling")

    st.markdown(
        "- The Gemini request receives age and numeric measurements only.\n"
        "- Patient name, email address, and full date of birth remain "
        "in the local database.\n"
        "- The assessment dataset does not specify measurement units. "
        "The demonstration assumptions are disclosed in each AI response.\n"
        "- AI remarks are not diagnoses or treatment instructions.\n"
        "- API failures do not delete saved records; remarks can be "
        "regenerated later."
    )

    st.subheader("Storage")

    st.write(
        "Patient records are stored in a local SQLite database. "
        "The database persists between local application runs. "
        "Hosted platforms may require a persistent database service "
        "to retain records across restarts."
    )


st.divider()

st.markdown(
    '<div class="app-footer">'
    "HealthInsight AI · Informational AI remarks require "
    "qualified professional review."
    "</div>",
    unsafe_allow_html=True,
)
