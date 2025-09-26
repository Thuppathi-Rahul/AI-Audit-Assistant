import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import List, Literal, Dict
import enum

# --- Database Setup ---
DATABASE_URL = "sqlite:///./audit_findings.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RunStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"

# --- SQLAlchemy Models ---
class AuditFinding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, index=True)
    question = Column(String, index=True)
    answer = Column(String)
    explanation = Column(String)
    timestamp = Column(DateTime)

class AuditRun(Base):
    __tablename__ = "audit_runs"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True, index=True)
    scope = Column(String)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(SQLAlchemyEnum(RunStatus), default=RunStatus.in_progress)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, default="Google")
    project_name = Column(String, unique=True, index=True)

Base.metadata.create_all(bind=engine)

# --- Pydantic Models ---
class ProjectCreate(BaseModel):
    company_name: str = "Google"
    project_name: str

class RunStartRequest(BaseModel):
    run_id: str
    scope: List[str]

class AuditResultCreate(BaseModel):
    run_id: str
    question: str
    answer: Literal["Yes", "No", "Partial", "N/A"]
    explanation: str
    timestamp: datetime.datetime

class AuditResultUpdate(BaseModel):
    answer: Literal["Yes", "No", "Partial", "N/A"]
    explanation: str

class AuditResultResponse(AuditResultCreate):
    id: int
    class Config:
        from_attributes = True

app = FastAPI(title="Real IRF Tool Backend", version="6.0.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---
@app.post("/projects/", response_model=ProjectCreate)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = db.query(Project).filter(Project.project_name == project.project_name).first()
    if db_project:
        raise HTTPException(status_code=400, detail="Project name already exists")
    db_project = Project(company_name=project.company_name, project_name=project.project_name)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=Dict[str, List[str]])
async def get_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    grouped_projects = {}
    if not projects: # Add default projects if the table is empty
        default_projects = ["Project_Alpha", "Project_Beta", "Project_Gamma"]
        for proj_name in default_projects:
            db_project = Project(company_name="Google", project_name=proj_name)
            db.add(db_project)
        db.commit()
        projects = db.query(Project).all()

    for project in projects:
        if project.company_name not in grouped_projects:
            grouped_projects[project.company_name] = []
        grouped_projects[project.company_name].append(project.project_name)
    return grouped_projects

@app.post("/start_run/")
async def start_run(run_request: RunStartRequest, db: Session = Depends(get_db)):
    scope_str = ",".join(run_request.scope)
    db_run = AuditRun(run_id=run_request.run_id, scope=scope_str, status=RunStatus.in_progress)
    db.add(db_run)
    db.commit()
    return {"message": "Run started", "run_id": run_request.run_id, "scope": run_request.scope, "status": "in_progress"}

@app.put("/complete_run/{run_id}")
async def complete_run(run_id: str, db: Session = Depends(get_db)):
    db_run = db.query(AuditRun).filter(AuditRun.run_id == run_id).first()
    if not db_run: raise HTTPException(status_code=404, detail="Run not found")
    db_run.status = RunStatus.completed
    db_run.end_time = datetime.datetime.utcnow()
    db.commit()
    return {"message": "Run completed", "run_id": run_id, "status": "completed"}

@app.get("/get_run_status/{run_id}", response_model=RunStatus)
async def get_run_status(run_id: str, db: Session = Depends(get_db)):
    db_run = db.query(AuditRun).filter(AuditRun.run_id == run_id).first()
    if not db_run: raise HTTPException(status_code=404, detail="Run not found")
    return db_run.status

@app.get("/get_run_scope/{run_id}", response_model=List[str])
async def get_run_scope(run_id: str, db: Session = Depends(get_db)):
    db_run = db.query(AuditRun).filter(AuditRun.run_id == run_id).first()
    if not db_run or not db_run.scope:
        return []
    return db_run.scope.split(',')

@app.post("/submit_finding/", response_model=AuditResultResponse)
async def submit_finding(result: AuditResultCreate, db: Session = Depends(get_db)):
    db_finding = AuditFinding(**result.dict())
    db.add(db_finding)
    db.commit()
    db.refresh(db_finding)
    print(f"--- ✅ Finding #{db_finding.id} (Run: {db_finding.run_id}) saved to database ---")
    return db_finding

@app.get("/get_findings/", response_model=List[AuditResultResponse])
async def get_findings(run_id: str = None, db: Session = Depends(get_db)):
    query = db.query(AuditFinding)
    if run_id: query = query.filter(AuditFinding.run_id == run_id)
    return query.order_by(AuditFinding.id.asc()).all()

@app.get("/get_runs/", response_model=List[str])
async def get_runs(db: Session = Depends(get_db)):
    runs = db.query(AuditRun.run_id).distinct().order_by(AuditRun.start_time.desc()).all()
    return [run[0] for run in runs]

@app.put("/update_finding/{finding_id}", response_model=AuditResultResponse)
async def update_finding(finding_id: int, result_update: AuditResultUpdate, db: Session = Depends(get_db)):
    db_finding = db.query(AuditFinding).filter(AuditFinding.id == finding_id).first()
    if db_finding is None: raise HTTPException(status_code=404, detail="Finding not found")
    db_finding.answer = result_update.answer
    db_finding.explanation = result_update.explanation
    db.commit()
    db.refresh(db_finding)
    print(f"--- 📝 Finding #{db_finding.id} updated in database ---")
    return db_finding

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)