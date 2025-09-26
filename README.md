# AI-Audit-Assistant
 AI Audit Assistant: A Production-Level Compliance Automation Platform


An intelligent, multi-page application designed to revolutionize the audit workflow. This tool leverages a sophisticated AI agent to automate document analysis against a comprehensive 41-point checklist, manage findings, and generate actionable reports, all through a centralized, interactive, and user-friendly dashboard.

This project was built to solve a critical business problem: manual audits are slow, prone to human error, and difficult to track over time. Our AI Assistant provides a scalable, efficient, and reliable solution.

✨ Key Features & Capabilities
This project is a complete three-tier application that demonstrates a professional, end-to-end audit management process.

Guided Multi-Page Workflow: A professional, easy-to-use interface built with Streamlit that guides the user through a logical 4-step process, from scheduling to final reporting.

Dynamic Audit Scheduling:

A dedicated page to configure the scope of each audit.

Users can select from a list of projects managed in a central database and can add new projects directly from the UI without any code changes.

Audits can be precisely targeted to specific compliance areas (e.g., PCI, GDPR, Infosec, etc.).

Multi-Source Evidence Gathering: Seamlessly process documents from multiple sources in a single audit run:

SharePoint Integration: Connect directly to SharePoint document libraries to pull official project files. Credentials are kept secure in an .env file.

Local Uploads: Full support for .pdf, .docx, and .zip files uploaded directly from the user's machine.

AI-Powered Analysis: A sophisticated LangChain agent that:

Works through the filtered checklist based on the selected audit scope.

Uses an intelligent fuzzy keyword matching system (thefuzz) to find relevant documents, making it robust against real-world variations in filenames.

Provides nuanced, three-state answers: "Yes" (compliant), "No" (non-compliant), or "Partial" (partially compliant).

Multi-Score Summary Dashboard:

A high-level dashboard that automatically calculates and displays compliance scores for each relevant category.

Features interactive Plotly donut charts showing the distribution of "Yes", "No", and "Partial" answers for a quick visual assessment.

Includes a "smart" auto-refresh that is only active when an audit is in progress.

Interactive Review & Remediation: A detailed checklist page where auditors can:

Review every AI-generated finding.

Manually override the AI's answers and save changes back to the database.

Add new, custom ad-hoc questions to a completed audit run.

Re-run analysis on specific questions with new evidence to verify remediation.

Actionable Report Generation: Download final audit results in two professional formats:

Full Excel Report: A complete data dump with scores, weights, and explanations, with auto-fitted and text-wrapped cells.

Word Remediation Report: An actionable to-do list containing only the "No" and "Partial" findings, perfect for sending to project teams.

🏛️ Architecture Overview
The application is built on a modern, three-tier architecture to ensure a clear separation of concerns, making it scalable and maintainable.

Frontend (Streamlit): A multi-page Streamlit application serves as the user interface.

Home.py: The main landing page.

pages/: A special folder containing each page of the application, which Streamlit automatically uses for navigation.

Backend (FastAPI): A robust FastAPI server acts as the central API.

It communicates with a SQLite database to manage projects, audit runs (including their scope), and findings.

It provides a set of REST endpoints for the frontend to consume.

AI Core (LangChain): The intelligence of the application.

It uses a LangChain agent powered by an OpenAI model (gpt-4-turbo).

The agent is equipped with a StructuredTool to interact with the backend, allowing it to save its findings directly to the database.

🚀 Getting Started
Follow these steps to get the application up and running locally.

Prerequisites
Python 3.9+

An OpenAI API Key

A SharePoint account (a free Microsoft 365 Developer account is recommended)

A GitHub account and a Personal Access Token (PAT) with repo scope.

1. Setup and Installation
Clone the repository:

git clone [https://your-repo-url.com/](https://your-repo-url.com/)
cd Your_Project_Folder

Install dependencies:

pip install -r requirements.txt

Configure your environment:

Create a file named .env in the root of the project folder.

Add the following variables, filling in your own secret keys:

OPENAI_API_KEY="your-secret-api-key-goes-here"

# SharePoint credentials (App Password or Modern Auth)
SHAREPOINT_USERNAME="your-sharepoint-email@yourcompany.com"
SHAREPOINT_PASSWORD="your-sharepoint-app-password"

# GitHub credentials
GITHUB_TOKEN="your-github-personal-access-token"

2. Running the Application
You need to run the backend and the frontend in two separate terminals.

Terminal 1: Start the Backend Server

uvicorn irf_backend:app --reload

The backend will be running at http://127.0.0.1:8000.

Terminal 2: Start the Streamlit Frontend

streamlit run Home.py
