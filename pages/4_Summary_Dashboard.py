import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh
from utils import (
    calculate_all_scores,
    get_answer_counts,
    create_donut_chart
)

st.set_page_config(page_title="Summary Dashboard", layout="wide")

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

def fetch_run_status(run_id):
    if not run_id: return None
    try:
        response = requests.get(f"{BACKEND_URL}/get_run_status/{run_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def get_run_scope(run_id):
    if not run_id: return []
    try:
        response = requests.get(f"{BACKEND_URL}/get_run_scope/{run_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []

st.title("📊 Summary Dashboard")

all_runs = fetch_runs()
if not all_runs:
    st.info("No audit runs found. Please run a new audit to see results here.")
else:
    if "custom_checklist" not in st.session_state:
        st.session_state.custom_checklist = []
        
    selected_run = st.selectbox("Select an Audit Run to view its summary:", options=all_runs)
    if selected_run:
        run_status = fetch_run_status(selected_run)
        if run_status == "in_progress":
            st.info("This audit is in progress. The dashboard will auto-refresh every 5 seconds.")
            st_autorefresh(interval=5000, key=f"refresh_{selected_run}")
        elif run_status == "completed":
            st.success("This audit is complete.")

        data = fetch_data_for_run(selected_run)
        findings_data = {finding['question']: finding for finding in data}
        
        st.header("Compliance Scores & Status")
        run_scope = get_run_scope(selected_run)
        all_scores = calculate_all_scores(findings_data, selected_run)
        
        # Only show scores for the compliance areas that were part of this run's scope
        if run_scope:
            # Add "Custom" to the scope if any custom questions exist for this run
            custom_questions_exist = any(
                "Custom" in item.get("tags", []) and item['question'] in findings_data
                for item in st.session_state.get("custom_checklist", [])
            )
            if custom_questions_exist and "Custom" not in run_scope:
                run_scope.append("Custom")

            # Create columns with a maximum of 3 charts per row
            num_areas_to_show = len([area for area in run_scope if all_scores.get(area, {}).get('max', 0) > 0])
            cols = st.columns(min(num_areas_to_show, 3))
            col_idx = 0
            
            for area in run_scope:
                score_data = all_scores.get(area)
                if score_data and score_data['max'] > 0:
                    with cols[col_idx % 3]:
                        st.metric(
                            label=f"{area} Score",
                            value=f"{score_data['percentage']:.2f}%",
                            help=f"Score: {score_data['achieved']:.1f} / {score_data['max']:.1f} points."
                        )
                        st.progress(score_data['percentage'] / 100)
                        answer_counts = get_answer_counts(findings_data, selected_run, area)
                        if sum(answer_counts.values()) > 0:
                            chart = create_donut_chart(answer_counts)
                            st.plotly_chart(chart, use_container_width=True, key=f"chart_{area}_{selected_run}")
                    col_idx += 1
        else:
            st.warning("Could not determine the scope for this audit run.")