# PDF Content Label + Query UI

This project enables users to upload a PDF document and ask natural-language questions to extract specific information like names, dates, email addresses, company names, or summaries using NLP and pattern matching.

## Features
- Upload multi-page PDFs
- Extracts text using "PyMuPDF"
- Label content using:
  - Named Entity Recognition (spaCy)
  - Regex for phone, email, URL, etc.
- Ask queries like:
  - "Who is the applicant?"
  - "What is the phone number?"
  - "Give me the summary."
- Session-based Q&A history with CSV export

## Tech Stack
- Python
- Streamlit (UI)
- spaCy (NLP)
- PyMuPDF (fitz)
- Regex (built-in)
  
## Demo
 
[Click here to watch the demo](https://youtu.be/MHY_VjaY73s)
