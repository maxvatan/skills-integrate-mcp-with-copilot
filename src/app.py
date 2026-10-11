"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")
teachers_file = Path(os.environ.get("TEACHERS_FILE", current_dir / "teachers.json"))
session_https_only = os.environ.get("SESSION_HTTPS_ONLY", "false").lower() in {
    "1", "true", "yes"
}
session_cookie = "teacher_session"
session_max_age = 8 * 60 * 60
teacher_sessions: dict[str, tuple[str, float]] = {}


class TeacherLogin(BaseModel):
    username: str
    password: str


def get_session_teacher(request: Request) -> Optional[str]:
    token = request.cookies.get(session_cookie)
    if not token:
        return None

    session_id = hashlib.sha256(token.encode()).hexdigest()
    session = teacher_sessions.get(session_id)
    if session is None:
        return None
    username, expires_at = session
    if expires_at <= time.time():
        teacher_sessions.pop(session_id, None)
        return None
    return username


def require_teacher(request: Request) -> str:
    username = get_session_teacher(request)
    if not username:
        raise HTTPException(status_code=401, detail="Teacher login required")
    return username


@app.post("/auth/login")
def teacher_login(credentials: TeacherLogin, response: Response):
    try:
        with teachers_file.open(encoding="utf-8") as file:
            config = json.load(file)
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Teacher accounts are not configured",
        )
    except (OSError, json.JSONDecodeError):
        raise HTTPException(
            status_code=503,
            detail="Teacher account configuration is unavailable",
        )

    teachers = config.get("teachers") if isinstance(config, dict) else None
    if not isinstance(teachers, dict):
        raise HTTPException(
            status_code=503,
            detail="Teacher account configuration is invalid",
        )

    stored_password = teachers.get(credentials.username)
    if not isinstance(stored_password, str) or not hmac.compare_digest(
        stored_password, credentials.password
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = secrets.token_urlsafe(32)
    session_id = hashlib.sha256(token.encode()).hexdigest()
    teacher_sessions[session_id] = (
        credentials.username,
        time.time() + session_max_age,
    )
    response.set_cookie(
        session_cookie,
        token,
        max_age=session_max_age,
        httponly=True,
        secure=session_https_only,
        samesite="lax",
        path="/",
    )
    return {"username": credentials.username}


@app.get("/auth/me")
def get_teacher_session(request: Request):
    username = get_session_teacher(request)
    return {"authenticated": bool(username), "username": username}


@app.post("/auth/logout")
def teacher_logout(request: Request, response: Response):
    token = request.cookies.get(session_cookie)
    if token:
        session_id = hashlib.sha256(token.encode()).hexdigest()
        teacher_sessions.pop(session_id, None)
    response.delete_cookie(
        session_cookie,
        secure=session_https_only,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return {"authenticated": False}

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    teacher: str = Depends(require_teacher),
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    teacher: str = Depends(require_teacher),
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
