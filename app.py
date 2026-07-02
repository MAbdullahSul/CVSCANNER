import re

import fitz  # PyMuPDF
import pandas as pd
import streamlit as st


KEYWORDS = [
    "excel",
    "communication",
    "leadership",
    "teamwork",
    "recruitment",
    "onboarding",
    "attendance",
    "payroll",
    "documentation",
    "confidentiality",
    "organization",
    "problem solving",
    "employee relations",
    "record management",
    "data entry",
]


def extract_pdf_text(uploaded_file):
    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""

    for page in pdf:
        text += page.get_text()

    pdf.close()
    return text


def keyword_found(keyword, text):
    pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
    return re.search(pattern, text.lower()) is not None


def scan_cv(uploaded_file, selected_keywords):
    text = extract_pdf_text(uploaded_file)

    matched = []
    missing = []

    for keyword in selected_keywords:
        if keyword_found(keyword, text):
            matched.append(keyword)
        else:
            missing.append(keyword)

    score = round((len(matched) / len(selected_keywords)) * 100)

    return {
        "CV Name": uploaded_file.name,
        "Score": score,
        "Matched Keywords": ", ".join(matched) if matched else "None",
        "Missing Keywords": ", ".join(missing) if missing else "None",
        "Extracted Text": text,
    }


st.set_page_config(
    page_title="Office CV Scanner",
    page_icon="📄",
    layout="wide",
)

st.title("Office CV Scanner")
st.write("Upload CV PDFs, scan them against HR keywords, and download the results.")

with st.sidebar:
    st.header("Settings")

    selected_keywords = st.multiselect(
        "Keywords to scan",
        KEYWORDS,
        default=KEYWORDS,
    )

    minimum_score = st.slider(
        "Highlight score from",
        min_value=0,
        max_value=100,
        value=50,
        step=5,
    )

    show_extracted_text = st.checkbox("Show extracted text", value=False)

st.text_area(
    "Job description / notes",
    height=160,
    placeholder="Paste the job description here for reference.",
)

uploaded_files = st.file_uploader(
    "Upload CV PDFs",
    type=["pdf"],
    accept_multiple_files=True,
)

if st.button("Scan CVs", type="primary"):
    if not selected_keywords:
        st.warning("Please select at least one keyword.")

    elif not uploaded_files:
        st.warning("Please upload at least one CV PDF.")

    else:
        results = []
        progress = st.progress(0)

        for index, uploaded_file in enumerate(uploaded_files):
            results.append(scan_cv(uploaded_file, selected_keywords))
            progress.progress((index + 1) / len(uploaded_files))

        results.sort(key=lambda result: result["Score"], reverse=True)

        df = pd.DataFrame(results)

        st.subheader("Summary")

        col1, col2, col3 = st.columns(3)
        col1.metric("CVs Scanned", len(results))
        col2.metric("Best Score", f"{df['Score'].max()}%")
        col3.metric("Average Score", f"{round(df['Score'].mean())}%")

        st.subheader("Ranking")

        st.dataframe(
            df[["CV Name", "Score", "Matched Keywords", "Missing Keywords"]],
            use_container_width=True,
            hide_index=True,
        )

        csv = df[["CV Name", "Score", "Matched Keywords", "Missing Keywords"]].to_csv(
            index=False
        )

        st.download_button(
            "Download results",
            data=csv,
            file_name="cv_scan_results.csv",
            mime="text/csv",
        )

        st.subheader("CV Details")

        for result in results:
            score = result["Score"]
            label = f"{result['CV Name']} - {score}% match"

            if score >= minimum_score:
                st.success(label)
            else:
                st.warning(label)

            with st.expander("View details"):
                st.write("Matched Keywords")
                st.write(result["Matched Keywords"])

                st.write("Missing Keywords")
                st.write(result["Missing Keywords"])

                if show_extracted_text:
                    st.text_area(
                        "Extracted Text",
                        result["Extracted Text"],
                        height=250,
                    )
