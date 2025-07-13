import streamlit as st
import fitz
import spacy
import pandas as pd
import re

nlp = spacy.load("en_core_web_sm")

st.set_page_config(page_title="PDF Content Query Assistant", layout="wide")
st.title("PDF Content Query Assistant")

if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

def clean_entity_text(text, label):
    text = text.strip()
    unwanted_keywords = ["Job Application", "Application Form", "Form", "Details"]
    for phrase in unwanted_keywords:
        text = text.replace(phrase, "")
    text = re.split(r"[\-–—:\|/,]", text)[0].strip()
    if label == "PERSON_NAME" and text.lower() in ["applicant name", "candidate name", "name"]:
        return None
    return text if len(text) > 0 else None

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
if uploaded_file:
    st.success("PDF loaded successfully.")
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = "".join(page.get_text() for page in doc)
    st.text_area("Extracted Preview", all_text, height=400)

    st.subheader("Ask a Question")
    with st.form("query_form"):
        user_query = st.text_input("Enter your question (e.g., Who is the applicant? What is the company name?)")
        submit_btn = st.form_submit_button("Ask")

    if submit_btn and user_query.strip():
        query_lower = user_query.lower()
        label, ner_label = None, None
        context_keywords = []

        if "who" in query_lower or "name" in query_lower:
            label, ner_label = "PERSON_NAME", "PERSON"
            context_keywords = ["applicant", "candidate", "name", "resume", "profile"]
        elif "company" in query_lower or "organization" in query_lower:
            label, ner_label = "COMPANY_NAME", "ORG"
            context_keywords = ["company", "organization", "technologies", "labs"]
        elif "email" in query_lower:
            label = "EMAIL"
        elif "phone" in query_lower or "contact" in query_lower:
            label = "PHONE_NUMBER"
        elif "website" in query_lower or "url" in query_lower:
            label = "URL"
        elif "price" in query_lower or "amount" in query_lower:
            label, ner_label = "PRICE", "MONEY"
            context_keywords = ["amount", "price"]
        elif "job title" in query_lower or "designation" in query_lower:
            label = "JOB_TITLE"
        elif "education" in query_lower or "degree" in query_lower:
            label = "EDUCATION"
        elif "skill" in query_lower or "technology" in query_lower:
            label = "SKILL"
        elif "when" in query_lower or "date" in query_lower:
            label, ner_label = "DATE", "DATE"
            context_keywords = ["submitted", "application", "on", "during"]
        elif "summary" in query_lower:
            label = "SUMMARY"
        elif "where" in query_lower or "location" in query_lower:
            label, ner_label = "ADDRESS", "GPE"
            context_keywords = ["location", "city", "state", "country"]

        raw_results = []

        if label and ner_label:
            doc_nlp = nlp(all_text)
            for ent in doc_nlp.ents:
                if ent.label_ == ner_label:
                    context = all_text[max(0, ent.start_char - 30):ent.end_char + 30].lower()
                    if any(kw in context for kw in context_keywords):
                        cleaned = clean_entity_text(ent.text, label)
                        if cleaned:
                            raw_results.append({"Label": label, "Text": cleaned})

            if label == "PERSON_NAME" and not raw_results:
                top_lines = all_text.splitlines()[:5]
                for line in top_lines:
                    name_line = line.strip()
                    if len(name_line.split()) >= 2 and not any(ch.isdigit() for ch in name_line):
                        raw_results.append({"Label": label, "Text": name_line})
                        break

        elif label:
            if label == "EMAIL":
                matches = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", all_text)
                raw_results = [{"Label": label, "Text": m} for m in matches]

            elif label == "PHONE_NUMBER":
                matches = re.findall(r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}', all_text)
                valid_phones = [p for p in matches if not re.search(r"\b(19|20)\d{2}[-–](19|20)\d{2}\b", p)]
                raw_results = [{"Label": label, "Text": m} for m in valid_phones]

            elif label == "URL":
                matches = re.findall(r"https?://[^\s]+", all_text)
                raw_results = [{"Label": label, "Text": m} for m in matches]

            elif label == "JOB_TITLE":
                titles = ["Software Engineer", "AI Developer", "Manager"]
                raw_results = [{"Label": label, "Text": t} for t in titles if t.lower() in all_text.lower()]

            elif label == "EDUCATION":
                degrees = ["B.Tech", "BCA", "M.Tech", "MCA", "MBA", "PhD", "Artificial Intelligence"]
                raw_results = [{"Label": label, "Text": d} for d in degrees if d.lower() in all_text.lower()]

            elif label == "SKILL":
                skills = ["Python", "TensorFlow", "Keras", "SQL", "NumPy"]
                raw_results = [{"Label": label, "Text": s} for s in skills if s.lower() in all_text.lower()]

            elif label == "SUMMARY":
                lines = all_text.splitlines()
                summary_lines = []
                capture = False
                stop_keywords = ["total", "amount", "fee", "price", "skills", "education", "work experience", "contact", "date", "project"]
                personal_keywords = ["@gmail", "@yahoo", "@outlook", "kerala", "india", "resume"]

                for line in lines:
                    line_stripped = line.strip()
                    if "summary" in line.lower():
                        capture = True
                        continue
                    if capture:
                        if (
                            line_stripped == ""
                            or line_stripped.lower().startswith(tuple(stop_keywords))
                            or line_stripped.lower().endswith(":")
                            or len(line_stripped.split()) <= 3
                            or any(pk in line_stripped.lower() for pk in personal_keywords)
                        ):
                            break
                        summary_lines.append(line_stripped)

                if summary_lines and not any(pk in summary_lines[0].lower() for pk in personal_keywords):
                    raw_results = [{"Label": label, "Text": " ".join(summary_lines)}]

        seen = set()
        unique_results = []
        for r in raw_results:
            if r["Text"] not in seen:
                seen.add(r["Text"])
                unique_results.append(r)

        st.session_state.qa_history.append({
            "question": user_query,
            "label": label,
            "results": unique_results
        })

if st.session_state.qa_history:
    st.subheader("Previous Questions & Answers")
    for qa in reversed(st.session_state.qa_history):
        with st.expander(f"{qa['question']}"):
            if qa["results"]:
                df = pd.DataFrame(qa["results"])
                st.success(f"Found {len(df)} result(s) for '{qa['label']}'")
                st.write(df)
            else:
                st.warning("No relevant results found.")

    all_rows = [
        {"Question": qa["question"], "Label": row["Label"], "Text": row["Text"]}
        for qa in st.session_state.qa_history for row in qa["results"]
    ]
    if all_rows:
        csv = pd.DataFrame(all_rows).to_csv(index=False).encode("utf-8")
        st.download_button("Download Q&A History", data=csv, file_name="history.csv", mime="text/csv")

    if st.button("Clear All"):
        st.session_state.qa_history = []
        st.success("History cleared.")
