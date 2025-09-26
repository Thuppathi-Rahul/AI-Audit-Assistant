import streamlit as st
import zipfile
import io
import datetime
import requests
import pandas as pd
from itertools import groupby
from thefuzz import fuzz # --- NEW IMPORT for fuzzy matching ---
from utils import (
    AUDIT_CHECKLIST,
    extract_text_from_pdf,
    extract_text_from_docx,
    get_agent_executor,
    fetch_sharepoint_docs,
    fetch_github_file_content 
)

st.set_page_config(page_title="Run Audit", layout="wide")

# --- HELPER FUNCTIONS ---
def notify_run_start(run_id, scope):
    try:
        payload = {"run_id": run_id, "scope": scope}
        requests.post(f"http://127.0.0.1:8000/start_run/", json=payload)
    except requests.exceptions.RequestException as e:
        st.error(f"Could not notify backend of run start: {e}")

def notify_run_complete(run_id):
    try:
        requests.put(f"http://127.0.0.1:8000/complete_run/{run_id}")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not notify backend of run completion: {e}")

st.title("⚙️ Run Configured Audit")

if 'audit_config' not in st.session_state or st.session_state.audit_config is None:
    st.warning("⬅️ Please configure an audit first on the 'Schedule Audit' page.")
    if st.button("Go to Scheduler"):
        st.switch_page("pages/1_🚀_Schedule_Audit.py")
    st.stop()

config = st.session_state.audit_config
project_name = config['project_name']
selected_checks = config['compliance_checks']

st.info(f"**Project:** {project_name} | **Selected Checks:** {', '.join(selected_checks)}")

filtered_checklist = [
    item for item in AUDIT_CHECKLIST if any(tag in selected_checks for tag in item.get("tags", []))
]

if 'extracted_docs' not in st.session_state:
    st.session_state.extracted_docs = {}

# --- Hybrid Document Input Section ---
st.header("1. Provide Evidence Sources")

# --- Tool Selection ---
TOOLS = {
    "SharePoint": "Connect to a SharePoint document library to pull audit evidence.",
    "GitHub": "Connect to a GitHub repository to analyze code or documentation.",
    "Jira": "Connect to a Jira project to analyze tickets (coming soon)."
}
selected_tools = st.multiselect(
    "Select Tools to Integrate (Optional):",
    options=list(TOOLS.keys()),
    help="You can select multiple tools to provide a comprehensive set of evidence."
)

# --- Conditional Input fields based on Tool Selection ---
if "SharePoint" in selected_tools:
    with st.container(border=True):
        st.subheader("SharePoint Configuration")
        st.text_input("SharePoint Site URL", placeholder="https://yourcompany.sharepoint.com/sites/YourSite", key="sp_site_url")
        st.text_input("Folder Path", placeholder="Shared Documents/Project Alpha", key="sp_folder_path")

if "GitHub" in selected_tools:
    with st.container(border=True):
        st.subheader("GitHub Configuration")
        st.info("A GITHUB_TOKEN must be set in your .env file for this to work.")
        st.text_input("GitHub Repository Name", placeholder="owner/repository-name", key="github_repo")

if "Jira" in selected_tools:
    st.warning("Jira integration is not yet available but will be added in a future update.")

st.subheader("Upload Local Documents")
uploaded_files = st.file_uploader(
    "You can always upload local documents in addition to any selected tool.",
    type=['pdf', 'docx', 'zip'],
    accept_multiple_files=True
)

if st.button("Process All Non-GitHub Documents"):
    st.session_state.extracted_docs = {}
    with st.spinner("Processing documents from SharePoint and local uploads..."):
        if "SharePoint" in selected_tools and st.session_state.sp_site_url and st.session_state.sp_folder_path:
            st.write("Connecting to SharePoint...")
            sharepoint_texts = fetch_sharepoint_docs(st.session_state.sp_site_url, st.session_state.sp_folder_path)
            if sharepoint_texts:
                st.session_state.extracted_docs.update(sharepoint_texts)
                st.success(f"Successfully processed {len(sharepoint_texts)} file(s) from SharePoint.")
        
        if uploaded_files:
            st.write("Processing locally uploaded files...")
            local_file_count = 0
            for uploaded_file in uploaded_files:
                file_name = uploaded_file.name
                if file_name in st.session_state.extracted_docs:
                    file_name = f"local_{file_name}"
                file_bytes = uploaded_file.getvalue()
                if file_name.lower().endswith(('.pdf', '.docx')):
                    text = extract_text_from_docx(file_bytes) if file_name.lower().endswith('.docx') else extract_text_from_pdf(file_bytes)
                    st.session_state.extracted_docs[file_name] = text
                    local_file_count += 1
                elif file_name.lower().endswith('.zip'):
                    with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                        for filename_in_zip in z.namelist():
                            if filename_in_zip.lower().endswith(('.pdf', '.docx')):
                                zip_file_name = filename_in_zip
                                if zip_file_name in st.session_state.extracted_docs:
                                    zip_file_name = f"local_zip_{zip_file_name}"
                                with z.open(filename_in_zip) as f:
                                    file_content_bytes = f.read()
                                    text = extract_text_from_docx(file_content_bytes) if zip_file_name.lower().endswith('.docx') else extract_text_from_pdf(file_content_bytes)
                                    st.session_state.extracted_docs[zip_file_name] = text
                                    local_file_count += 1
            st.success(f"Successfully processed {local_file_count} file(s) from local upload.")

    if not st.session_state.get('extracted_docs'):
        st.warning("No documents were processed from SharePoint or local upload.")
    else:
        st.success(f"Total SharePoint/local documents processed: {len(st.session_state.extracted_docs)}. You can now run the audit.")

st.divider()
st.header("2. Start Analysis")
default_run_name = f"{project_name.replace(' ', '_')}_{'_'.join(selected_checks).lower()}_{datetime.datetime.now().strftime('%Y%m%d')}"
run_name = st.text_input("Enter a Name for this Audit Run:", value=default_run_name)

if st.button("Start Audit Process", disabled=(not st.session_state.get('extracted_docs') and "GitHub" not in selected_tools) or not run_name):
    run_id = run_name.strip().lower().replace(" ", "_")
    st.session_state.run_id = run_id
    
    notify_run_start(run_id, selected_checks)
    st.session_state.audit_results = pd.DataFrame(columns=["Question", "Answer", "Explanation"])
    
    st.subheader("Live Audit Progress")
    st.divider()

    agent_executor = get_agent_executor()
    uploaded_docs_dict = st.session_state.extracted_docs
    question_counter = 1
    last_subject = None
    
    for item in filtered_checklist:
        question = item['question']
        subject = item['subject']
        source = item.get("source", "sharepoint_or_local")

        if subject != last_subject:
            st.subheader(f"📋 Audit Subject: {subject}")
            last_subject = subject
        
        placeholder = st.empty()
        placeholder.markdown(f"**{question_counter}. {question}**\n\n*Status: 🧠 Agent is processing...*")
        
        document_context = ""
        # --- Conditional logic to get context from the right source ---
        if source == "github":
            if "GitHub" in selected_tools and st.session_state.get('github_repo'):
                files_to_check = item['keywords']
                document_context = fetch_github_file_content(st.session_state.github_repo, files_to_check)
            else:
                document_context = "The GitHub tool was not selected or configured for this audit run, so this question cannot be answered."
        else: # This is the existing logic for SharePoint and local files
            required_keywords = item.get('keywords', [])
            matched_doc_names = []
            
            # --- FUZZY MATCHING LOGIC ---
            MATCH_THRESHOLD = 85 # Similarity score from 0 to 100
            for doc_name in uploaded_docs_dict.keys():
                for keyword in required_keywords:
                    similarity_score = fuzz.partial_ratio(keyword.lower(), doc_name.lower())
                    if similarity_score >= MATCH_THRESHOLD:
                        if doc_name not in matched_doc_names:
                            matched_doc_names.append(doc_name)
            
            with st.expander(f"Documents used for question #{question_counter}", expanded=False):
                if matched_doc_names: st.write(f"Found matching document(s): *{', '.join(matched_doc_names)}*")
                else: st.warning(f"No documents found with a high similarity match for keywords: {', '.join(required_keywords)}")

            context_texts = [f"--- Content from {doc_name} ---\n{uploaded_docs_dict[doc_name]}" for doc_name in matched_doc_names]
            document_context = "\n\n".join(context_texts) if context_texts else "No relevant documents were provided."
        
        agent_input = f"Answer the audit question based *only* on the provided document content. Your answer MUST be one of 'Yes', 'No', or 'Partial'. After determining your answer, use the 'SubmitAuditFinding' tool.\n\nAUDIT QUESTION:\n{question}\n\nDOCUMENT CONTENT:\n---\n{document_context}\n---"
        response = agent_executor.invoke({"input": agent_input})
        latest_result = st.session_state.audit_results.iloc[-1]
        answer, explanation = latest_result['Answer'], latest_result['Explanation']
        color = "green" if answer.lower() == 'yes' else "red" if answer.lower() == 'no' else "orange"
        placeholder.markdown(f"**{question_counter}. {question}**\n\n**Answer:** <span style='color:{color};'>{answer}</span>\n\n**Explanation:** {explanation}", unsafe_allow_html=True)
        st.divider()
        question_counter += 1

    notify_run_complete(run_id)
    st.success("✅ Audit process complete!")
    st.balloons()