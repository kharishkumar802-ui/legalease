from datetime import date
from pathlib import Path
import os

import requests
import streamlit as st


# =================================================
# PATHS
# =================================================

ROOT = Path(
    __file__
).resolve().parents[1]


API_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
)


# =================================================
# PAGE CONFIG
# =================================================

st.set_page_config(
    page_title="LegalEase",
    page_icon="⚖️",
    layout="wide",
)


# =================================================
# CUSTOM CSS
# =================================================

st.markdown(
    """
<style>

.document-preview {
    background: #111827;
    color: #f9fafb;

    padding: 28px;

    border-radius: 14px;

    min-height: 420px;
    max-height: 650px;

    overflow-y: auto;

    line-height: 1.65;

    font-family: Georgia, serif;
}

.document-preview h1,
.document-preview h2,
.document-preview h3 {
    color: #ffffff;
}

.small-note {
    color: #6b7280;
    font-size: 0.9rem;
}

</style>
""",
    unsafe_allow_html=True,
)


# =================================================
# LOGO
# =================================================

logo = (
    ROOT
    / "assets"
    / "logo.svg"
)


if logo.exists():

    st.image(
        str(logo),
        width=420,
    )

else:

    st.title(
        "LegalEase"
    )


st.caption(
    "AI-powered legal document "
    "drafting, editing and export"
)


# =================================================
# DISCLAIMER
# =================================================

st.warning(
    "LegalEase creates editable drafts "
    "and general legal information. "
    "Review important documents with a "
    "qualified legal professional before use."
)


# =================================================
# INPUT FORM
# =================================================

with st.form(
    "document_form"
):

    left, right = st.columns(2)

    # ---------------------------------------------
    # LEFT
    # ---------------------------------------------

    with left:

        document_type = st.selectbox(
            "Document Type",

            [
                "Employment Contract",
                "Non-Disclosure Agreement",
                "Lease Agreement",
                "Freelance Work Contract",
                "Service Agreement",
                "Offer Letter",
                "General Agreement",
            ],
        )

        effective_date = st.date_input(
            "Effective Date",
            value=date.today(),
        )

    # ---------------------------------------------
    # RIGHT
    # ---------------------------------------------

    with right:

        parties = st.text_area(
            "Parties Involved",

            placeholder=(
                "Jane Doe (Service Provider), "
                "TechNova Inc. (Client)"
            ),

            height=110,
        )

        terms = st.text_area(
            "Terms & Conditions",

            placeholder=(
                "Payment within 30 days; "
                "Confidentiality; "
                "Either party may terminate "
                "with 15 days notice"
            ),

            height=110,
        )

    submitted = st.form_submit_button(
        "Generate Document",
        type="primary",
        use_container_width=True,
    )


# =================================================
# GENERATION
# =================================================

if submitted:

    if not parties.strip():

        st.error(
            "Please provide the parties involved."
        )

    elif not terms.strip():

        st.error(
            "Please provide the terms and conditions."
        )

    else:

        payload = {
            "document_type": document_type,
            "parties": parties,
            "terms": terms,
            "effective_date":
                effective_date.isoformat(),
        }

        with st.spinner(
            "Generating your draft..."
        ):

            try:

                response = requests.post(
                    f"{API_URL}/generate",
                    json=payload,
                    timeout=90,
                )

                response.raise_for_status()

                data = response.json()

                st.session_state[
                    "document_type"
                ] = data[
                    "document_type"
                ]

                st.session_state[
                    "content"
                ] = data[
                    "content"
                ]

                st.session_state[
                    "model"
                ] = data[
                    "model"
                ]

                st.success(
                    "Document generated using "
                    f"{data['model']} mode."
                )

            except requests.RequestException as exc:

                detail = getattr(
                    getattr(
                        exc,
                        "response",
                        None,
                    ),
                    "text",
                    "",
                )

                st.error(
                    "Backend request failed. "
                    f"Is FastAPI running at "
                    f"{API_URL}? "
                    f"{detail or exc}"
                )


# =================================================
# EDITOR
# =================================================

if "content" in st.session_state:

    st.divider()

    st.subheader(
        "Editable Document"
    )

    edited = st.text_area(
        "Edit the generated document "
        "before exporting",

        value=st.session_state[
            "content"
        ],

        height=520,

        key="editable_content",
    )

    st.session_state[
        "content"
    ] = edited


    # =================================================
    # PREVIEW
    # =================================================

    st.subheader(
        "Preview"
    )

    safe_preview = (
        edited
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace(
            "\n",
            "<br>",
        )
    )

    st.markdown(
        f"""
        <div class="document-preview">
            {safe_preview}
        </div>
        """,
        unsafe_allow_html=True,
    )


    # =================================================
    # DOWNLOAD
    # =================================================

    st.subheader(
        "Download"
    )

    cols = st.columns(3)

    formats = [
        ("txt", "Download TXT"),
        ("docx", "Download DOCX"),
        ("pdf", "Download PDF"),
    ]


    for col, (fmt, label) in zip(
        cols,
        formats,
    ):

        with col:

            try:

                export_response = (
                    requests.post(
                        f"{API_URL}/export/{fmt}",

                        json={
                            "document_type":
                                st.session_state[
                                    "document_type"
                                ],

                            "content":
                                edited,
                        },

                        timeout=60,
                    )
                )

                export_response.raise_for_status()

                if fmt == "txt":

                    mime = (
                        "text/plain"
                    )

                elif fmt == "docx":

                    mime = (
                        "application/"
                        "vnd.openxmlformats-officedocument."
                        "wordprocessingml.document"
                    )

                else:

                    mime = (
                        "application/pdf"
                    )


                st.download_button(
                    label=label,

                    data=(
                        export_response.content
                    ),

                    file_name=(
                        f"legalease_document."
                        f"{fmt}"
                    ),

                    mime=mime,

                    use_container_width=True,

                    key=(
                        f"download_{fmt}"
                    ),
                )

            except requests.RequestException as exc:

                st.error(
                    f"{fmt.upper()} "
                    f"export failed: {exc}"
                )


# =================================================
# FOOTER
# =================================================

st.divider()

st.markdown(
    """
<p class="small-note">
LegalEase — AI-powered legal document
drafting reference application.
</p>
""",
    unsafe_allow_html=True,
)