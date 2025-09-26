import streamlit as st
import requests

st.set_page_config(page_title="Schedule Audit", layout="wide")

st.title("🗓️ Schedule a New Audit")
st.markdown("Select a project and the specific compliance checks you want to perform. This will create a focused audit scope.")

# --- API Communication ---
BACKEND_URL = "http://127.0.0.1:8000"

def fetch_projects():
    try:
        response = requests.get(f"{BACKEND_URL}/projects/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        st.error("Could not connect to the backend to fetch projects. Please ensure the backend is running.")
        return {}

def add_project(company, new_project_name):
    if not new_project_name.strip():
        st.warning("Project name cannot be empty.")
        return
    try:
        payload = {"company_name": company, "project_name": new_project_name}
        response = requests.post(f"{BACKEND_URL}/projects/", json=payload)
        response.raise_for_status()
        st.success(f"Successfully added project '{new_project_name}'!")
        st.rerun() # Rerun the page to update the project list
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to add project: {e.response.json().get('detail', 'Unknown error')}")

# --- Static Data ---
COMPLIANCE_CHECKS = ["PCI", "GDPR", "Infosec", "CMMI", "ITSM"]
if 'audit_config' not in st.session_state:
    st.session_state.audit_config = None

# --- UI for Scheduling ---
projects_data = fetch_projects()

if projects_data:
    st.header("1. Select Project")
    company = "Google" # As requested, we are focusing on one company
    project_list = projects_data.get(company, [])
    
    project = st.selectbox(
        f"Select a Project for {company}:", 
        options=project_list,
        index=None,
        placeholder="Choose a project..."
    )
    
    with st.expander("Or, Add a New Project"):
        with st.form("new_project_form", clear_on_submit=True):
            new_project_name = st.text_input("New Project Name:")
            submitted = st.form_submit_button("Add Project")
            if submitted:
                add_project("Google", new_project_name)

    st.header("2. Select Audit Scope")
    checks = st.multiselect(
        "Select the compliance checks to perform for this audit:",
        options=COMPLIANCE_CHECKS,
        placeholder="Choose one or more checks..."
    )
    
    st.header("3. Confirm and Proceed")
    if st.button("Configure Audit & Proceed to Upload Documents"):
        # --- CHANGE: Validation now happens inside the button click ---
        if not project:
            st.warning("Please select a project before proceeding.")
        elif not checks:
            st.warning("Please select at least one compliance check.")
        else:
            st.session_state.audit_config = {
                "project_name": project,
                "compliance_checks": checks
            }
            # This automatically navigates the user to the next page
            st.switch_page("pages/2_Run_Audit.py")