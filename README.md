# 🤖 AI-Powered Audit Assistant

> An intelligent, multi-page application designed to revolutionize the audit workflow. This tool leverages a sophisticated AI agent to automate document analysis, manage findings, and generate actionable reports through a centralized, interactive dashboard.

This project was built to solve a critical business problem: manual audits are slow, prone to human error, and difficult to track. Our AI Assistant provides a scalable, efficient, and reliable solution.

## ✨ Key Features & Capabilities

* **Guided Multi-Page Workflow:** A professional, easy-to-use interface built with Streamlit that guides the user through a logical 4-step process.

* **Dynamic Audit Scheduling:**
    * A dedicated page to configure the scope of each audit.
    * Users can select from a list of projects managed in a central database and can **add new projects** directly from the UI without any code changes.
    * Audits can be precisely targeted to specific compliance areas (e.g., `PCI`, `GDPR`, `Infosec`).

* **Multi-Source Evidence Gathering:** Seamlessly process documents from multiple sources in a single audit run:
    * **SharePoint Integration:** Connect directly to SharePoint document libraries to pull official project files.
    * **GitHub Integration:** Connect to GitHub repositories to analyze code and documentation files (`README.md`, etc.).
    * **Local Uploads:** Full support for `.pdf`, `.docx`, and `.zip` files.

* **AI-Powered Analysis:** A sophisticated **LangChain agent** that:
    * Works through a filtered checklist based on the selected audit scope.
    * Provides nuanced, three-state answers: **"Yes"**, **"No"**, or **"Partial"**.

* **Multi-Score Summary Dashboard:**
    * A high-level dashboard that automatically calculates and displays compliance scores for each relevant category.
    * Features interactive **Plotly donut charts** showing the distribution of answers for a quick visual assessment.
    * Includes a "smart" auto-refresh that is only active when an audit is in progress.

* **Interactive Review & Remediation:** A detailed checklist page where auditors can:
    * Review every AI-generated finding.
    * Manually override the AI's answers and save changes back to the database.
    * **Add new, custom ad-hoc questions** to a completed audit run.
    * **Re-run analysis** on specific questions with new evidence to verify remediation.

* **Actionable Report Generation:** Download final audit results in two professional formats:
    * **Full Excel Report:** A complete data dump with scores and weights.
    * **Word Remediation Report:** An actionable to-do list containing only the "No" and "Partial" findings.

## 🏛️ Architecture Overview

The application is built on a modern, three-tier architecture to ensure a clear separation of concerns, making it scalable and maintainable.

>> **Frontend (Streamlit):** A multi-page Streamlit application serves as the user interface (`Home.py` + `pages/` directory).
>>
>> **Backend (FastAPI):** A robust FastAPI server (`irf_backend.py`) acts as the central API, communicating with a SQLite database to manage all data.
>>
>> **AI Core (LangChain):** The intelligence of the application, using an OpenAI model (`gpt-4-turbo`) and custom tools to perform its tasks.

## 🚀 Getting Started

Follow these steps to get the application up and running locally.

### Prerequisites

* Python 3.9+
* An OpenAI API Key
* A SharePoint account with credentials
* A GitHub account and a Personal Access Token (PAT) with `repo` scope.

### 1. Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://your-repo-url.com/](https://your-repo-url.com/)
    cd Your_Project_Folder
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure your environment:**
    * Create a file named `.env` in the root of the project folder.
    * Add the following variables, filling in your own secret keys:
        ```
        OPENAI_API_KEY="your-secret-api-key-goes-here"
        
        # SharePoint credentials
        SHAREPOINT_USERNAME="your-sharepoint-email@yourcompany.com"
        SHAREPOINT_PASSWORD="your-sharepoint-app-password"

        # GitHub credentials
        GITHUB_TOKEN="your-github-personal-access-token"
        ```

### 2. Running the Application

> **Important:** You need to run the backend and the frontend in **two separate terminals**. Before the first run, make sure to delete any old `audit_findings.db` file.

* **Terminal 1: Start the Backend Server**
    ```bash
    uvicorn irf_backend:app --reload
    ```
    >> The backend will be running at `http://127.0.0.1:8000`.

* **Terminal 2: Start the Streamlit Frontend**
    ```bash
    streamlit run Home.py
    ```
    >> The application will be running at `http://localhost:8501`.

## 📖 How to Use

The application is designed as a guided, 4-step workflow, accessible from the sidebar.

1.  **Schedule Audit:** Start on the `Schedule Audit` page. Here you can add new projects and select a project and the compliance checks you want to perform (e.g., PCI, Infosec).
2.  **Run Audit:** Proceed to the `Run Audit` page. Provide your evidence by connecting to SharePoint, GitHub, and/or uploading local files. Click "Start Audit Process" to begin the analysis.
3.  **Summary Dashboard:** After the audit is complete, navigate to the `Summary Dashboard` to see the high-level compliance scores and visual charts.
4.  **Review & Report:** Go to the `Review Checklist` page to see a detailed, interactive list of all findings. Here you can override the AI's answers, add new custom questions, and download the final reports.
