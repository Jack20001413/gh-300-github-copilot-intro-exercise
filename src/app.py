"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from urllib.parse import urlencode
from src.config import settings
from src import auth

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.APP_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Basketball": {
        "description": "Competitive basketball team and practice sessions",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 15,
        "participants": ["james@mergington.edu"]
    },
    "Tennis Club": {
        "description": "Tennis training and friendly matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
        "max_participants": 10,
        "participants": ["sarah@mergington.edu"]
    },
    "Drama Club": {
        "description": "Theater performances and acting workshops",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 25,
        "participants": ["lucas@mergington.edu", "isabella@mergington.edu"]
    },
    "Art Studio": {
        "description": "Painting, drawing, and sculpture classes",
        "schedule": "Mondays and Fridays, 3:30 PM - 4:30 PM",
        "max_participants": 18,
        "participants": ["grace@mergington.edu"]
    },
    "Science Club": {
        "description": "Hands-on experiments and STEM exploration",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 20,
        "participants": ["alex@mergington.edu", "mia@mergington.edu"]
    },
    "Debate Team": {
        "description": "Competitive debate and public speaking skills",
        "schedule": "Tuesdays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["tyler@mergington.edu"]
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
    }
}


# OAuth endpoints

@app.get("/auth/login")
async def login(request: Request):
    """Initiate OAuth login flow"""
    # Generate PKCE parameters
    code_verifier, code_challenge = auth.generate_pkce_pair()
    state = auth.generate_state()
    
    # Store PKCE verifier and state in session
    session_token = request.cookies.get("oauth_session") or auth.generate_state()
    auth.sessions[session_token] = {
        "code_verifier": code_verifier,
        "state": state,
        "expires": datetime.now(timezone.utc) + timedelta(minutes=10)
    }
    
    # Build authorization URL
    params = {
        "client_id": settings.OAUTH_CLIENT_ID,
        "redirect_uri": settings.OAUTH_REDIRECT_URI,
        "scope": "user:email",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    auth_url = f"{settings.OAUTH_AUTHORIZE_URL}?{urlencode(params)}"
    
    response = RedirectResponse(url=auth_url)
    # Set temporary oauth session cookie (expires in 10 minutes)
    # Note: secure flag should be True in production with HTTPS
    response.set_cookie(
        key="oauth_session",
        value=session_token,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite="lax",
        max_age=600
    )
    return response


@app.get("/auth/callback")
async def auth_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle OAuth callback"""
    if error:
        return RedirectResponse(url=f"/?error={error}")
    
    if not code or not state:
        return RedirectResponse(url="/?error=missing_parameters")
    
    # Verify state to prevent CSRF
    oauth_session_token = request.cookies.get("oauth_session")
    if not oauth_session_token:
        return RedirectResponse(url="/?error=no_session")
    
    session_data = auth.sessions.get(oauth_session_token)
    if not session_data or session_data.get("state") != state:
        return RedirectResponse(url="/?error=invalid_state")
    
    # Exchange code for token
    code_verifier = session_data.get("code_verifier")
    token_response = await auth.exchange_code_for_token(code, code_verifier)
    
    if not token_response or "access_token" not in token_response:
        return RedirectResponse(url="/?error=token_exchange_failed")
    
    # Get user info
    user_info = await auth.get_oauth_user_info(token_response["access_token"])
    if not user_info:
        return RedirectResponse(url="/?error=user_info_failed")
    
    # Create user session
    user = {
        "email": user_info.get("email") or f"{user_info.get('login')}@github.user",
        "name": user_info.get("name") or user_info.get("login"),
        "id": str(user_info.get("id")),
        "avatar_url": user_info.get("avatar_url")
    }
    
    response = RedirectResponse(url="/")
    auth.create_session(user, response)
    
    # Clean up OAuth session
    if oauth_session_token in auth.sessions:
        del auth.sessions[oauth_session_token]
    response.delete_cookie(key="oauth_session")
    
    return response


@app.get("/auth/user")
async def get_current_user(request: Request):
    """Get current authenticated user"""
    user = auth.get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@app.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    """Refresh access token using refresh token"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    user_id = auth.verify_refresh_token(refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # For simplicity, we'll just extend the session
    # In production, you would regenerate tokens
    user = auth.get_session_user(request)
    if user:
        auth.create_session(user, response)
        return {"message": "Token refreshed"}
    
    raise HTTPException(status_code=401, detail="Session expired")


@app.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session"""
    auth.clear_session(request, response)
    return {"message": "Logged out successfully"}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, request: Request):
    """Sign up a student for an activity (requires authentication)"""
    # Check authentication
    user = auth.get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    email = user["email"]
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student already signed up for this activity")

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, request: Request, email: str = None):
    """Unregister a student from an activity (requires authentication)"""
    # Check authentication
    user = auth.get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Use authenticated user's email if not provided
    if not email:
        email = user["email"]
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
