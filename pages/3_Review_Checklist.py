import streamlit as st
import requests
import time
import io
from itertools import groupby
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils import (
    AUDIT_CHECKLIST,
    extract_text_from_pdf,
    extract_text_from_docx,
    get_agent_executor,
    get_llm,
    generate_word_report,
    to_excel
)

st.set_page_config(page_title="Review Checklist", layout="wide")

# --- API COMMUNICATION ---
BACKEND_URL = "http://127.0.0.1:8000"

def fetch_runs():
    try:
        response = requests.get(f"{BACKEND_URL}/get_runs/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []

def fetch_data_for_run(run_id):
    if not run_id: return []
    try:
        response = requests.get(f"{BACKEND_URL}/get_findings/", params={"run_id": run_id})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to the IRF Backend: {e}")
        return []

def get_run_scope(run_id):
    if not run_id: return []
    try:
        response = requests.get(f"{BACKEND_URL}/get_run_scope/{run_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []

def save_changes(finding_id, answer, explanation):
    try:
        payload = {"answer": answer, "explanation": explanation}
        response = requests.put(f"{BACKEND_URL}/update_finding/{finding_id}", json=payload)
        response.raise_for_status()
        st.toast(f"Finding #{finding_id} saved successfully!", icon="✅")
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to save changes for finding #{finding_id}: {e}")

# --- MAIN UI ---
st.title("📝 Review & Edit Checklist")

all_runs = fetch_runs()
if not all_runs:
    st.info("No audit runs found. Please run a new audit to see results.")
else:
    if "custom_checklist" not in st.session_state:
        st.session_state.custom_checklist = []
    if 'extracted_docs' not in st.session_state:
        st.session_state.extracted_docs = {}

    selected_run = st.selectbox("Select an Audit Run to review:", options=all_runs)
    if selected_run:
        st.session_state.run_id = selected_run
        data = fetch_data_for_run(selected_run)
        findings_data = {finding['question']: finding for finding in data}

        st.header("Detailed Checklist Findings")

        run_scope = get_run_scope(selected_run)
        if run_scope:
            filtered_checklist = [item for item in AUDIT_CHECKLIST if any(tag in run_scope for tag in item.get("tags", []))]
        else:
            filtered_checklist = AUDIT_CHECKLIST

        current_checklist = filtered_checklist + [item for item in st.session_state.get("custom_checklist", []) if item['question'] in findings_data]
        grouped_checklist = {k: list(v) for k, v in groupby(current_checklist, key=lambda item: item.get('subject', 'Custom Questions'))}

        question_counter = 0
        for subject, items in grouped_checklist.items():
            with st.expander(f"**Audit Subject: {subject}**", expanded=True):
                for item in items:
                    question = item['question']
                    finding = findings_data.get(question)

                    st.markdown(f"**{question_counter + 1}. {question}** (Weight: {item.get('weight', 0)})")

                    col1, col2 = st.columns([1, 2])
                    with col1:
                        answer_options = ["Yes", "No", "Partial", "N/A"]
                        default_index = 3
                        if finding:
                            try: default_index = answer_options.index(finding['answer'])
                            except ValueError: default_index = 3
                        answer = st.selectbox("Answer", options=answer_options, index=default_index, key=f"answer_{question_counter}_{selected_run}", label_visibility="collapsed")

                    with col2:
                        default_explanation = finding['explanation'] if finding else ""
                        explanation = st.text_area("Explanation", value=default_explanation, key=f"explanation_{question_counter}_{selected_run}", label_visibility="collapsed")
                        if finding:
                            st.button("Save", key=f"save_{question_counter}_{selected_run}", on_click=save_changes, args=(finding['id'], answer, explanation))

                    st.divider()
                    question_counter += 1

        # --- REANALYSIS SECTION ---
        st.header("🔄 Reanalysis of Questions")
        st.markdown("If you have new documents or want to re-evaluate specific findings, select the questions and provide the updated evidence below.")
        
        with st.form(key="reanalysis_form"):
            q_numbers_str = st.text_input("Question numbers to re-run (comma-separated):", placeholder="e.g., 3, 5, 12")
            new_docs = st.file_uploader("Upload additional documents for reanalysis:", type=['pdf', 'docx'], accept_multiple_files=True)
            reanalyze_button = st.form_submit_button("Re-run Selected Questions")

            if reanalyze_button and q_numbers_str:
                try:
                    q_indices = [int(n.strip()) - 1 for n in q_numbers_str.split(',')]
                    
                    with st.spinner("Re-running analysis on selected questions..."):
                        original_docs_dict = st.session_state.get('extracted_docs', {})
                        new_docs_dict = {}
                        if new_docs:
                            for doc in new_docs:
                                file_bytes = doc.getvalue()
                                text = extract_text_from_docx(file_bytes) if doc.name.lower().endswith('.docx') else extract_text_from_pdf(file_bytes)
                                new_docs_dict[doc.name] = text

                        llm = get_llm()
                        prompt_template = PromptTemplate.from_template(
                            """
                            Based *only* on the provided DOCUMENT CONTEXT, answer the following AUDIT QUESTION.
                            Your response MUST be in two lines.
                            Line 1: Only one word: 'Yes', 'No', or 'Partial'.
                            Line 2: A brief, one-sentence explanation.

                            AUDIT QUESTION: {question}
                            DOCUMENT CONTEXT:\n---\n{context}\n---
                            YOUR ANSWER:
                            """
                        )
                        chain = prompt_template | llm | StrOutputParser()

                        for idx in q_indices:
                            if 0 <= idx < len(current_checklist):
                                item_to_rerun = current_checklist[idx]
                                question_text = item_to_rerun['question']
                                finding_to_update = findings_data.get(question_text)
                                
                                if not finding_to_update:
                                    st.warning(f"Skipping Question #{idx + 1} as it has no initial result to update.")
                                    continue

                                st.write(f"Processing Question #{idx + 1}: {question_text}")
                                
                                combined_docs = {**original_docs_dict, **new_docs_dict}
                                keywords = [kw.lower() for kw in item_to_rerun.get('keywords', [])]
                                matched_docs = {name: text for name, text in combined_docs.items() if any(kw in name.lower() for kw in keywords)}
                                
                                context = "\n\n".join([f"--- Content from {name} ---\n{text}" for name, text in matched_docs.items()]) or "No relevant documents were provided for this question."

                                response = chain.invoke({"question": question_text, "context": context})
                                
                                try:
                                    new_answer, new_explanation = response.strip().split('\n', 1)
                                    save_changes(finding_to_update['id'], new_answer.strip(), new_explanation.strip())
                                except Exception as e:
                                    st.error(f"Failed to parse AI response for question #{idx + 1}: {e}")

                    st.success("Reanalysis complete! The checklist has been updated.")
                    time.sleep(2)
                    st.rerun()

                except ValueError:
                    st.error("Invalid input. Please enter only numbers separated by commas (e.g., 2, 3, 5).")
        
        # --- ADD CUSTOM QUESTION SECTION ---
        st.header("➕ Add Custom Audit Question")
        with st.form(key="custom_question_form", clear_on_submit=True):
            custom_question = st.text_input("Enter your custom audit question:")
            custom_weight = st.number_input("Assign a weight for scoring (1-5):", min_value=1, max_value=5, value=3)
            custom_docs = st.file_uploader("Upload new documents for this question (optional):", type=['pdf', 'docx'], accept_multiple_files=True)
            
            submitted = st.form_submit_button("Analyze Custom Question")

            if submitted and custom_question:
                with st.spinner("Analyzing custom question..."):
                    agent_executor = get_agent_executor()
                    
                    custom_context_texts = []
                    if custom_docs:
                        for doc in custom_docs:
                            file_bytes = doc.getvalue()
                            if doc.name.endswith('.pdf'): text = extract_text_from_pdf(file_bytes)
                            elif doc.name.endswith('.docx'): text = extract_text_from_docx(file_bytes)
                            custom_context_texts.append(f"--- Content from {doc.name} ---\n{text}")
                    
                    document_context = "\n\n".join(custom_context_texts) if custom_context_texts else "No document provided."
                    
                    st.session_state.custom_checklist.append({"subject": "Custom Questions", "question": custom_question, "weight": custom_weight, "tags": ["PCI", "Custom"]})

                    agent_input = f"Answer the audit question based *only* on the provided document content. Your answer MUST be 'Yes', 'No', or 'Partial'. After determining your answer, use the 'SubmitAuditFinding' tool.\n\nAUDIT QUESTION:\n{custom_question}\n\nDOCUMENT CONTENT:\n---\n{document_context}\n---"
                    
                    response = agent_executor.invoke({"input": agent_input})
                    st.success("Custom question analyzed and added to the run!")
                    time.sleep(1)
                    st.rerun()
        
        # --- REPORT GENERATION SECTION ---
        st.divider()
        st.header("📄 Generate Reports")
        col1, col2 = st.columns(2)
        with col1:
            if data:
                excel_data = to_excel(data)
                st.download_button("📥 Download Full Report (Excel)", data=excel_data, file_name=f"{selected_run}_full_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with col2:
            if data:
                report_bytes = generate_word_report(selected_run, data)
                st.download_button("📝 Download Remediation Report (Word)", data=report_bytes, file_name=f"remediation_report_{selected_run}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")