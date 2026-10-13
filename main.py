import os
from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv

from supabase_client import supabase

load_dotenv()

app = FastAPI(
    title="FlyRank Auth API",
    description="Authentication and protected routes using Supabase Auth and Bearer JWT tokens",
    version="1.0.0"
)

# HTTPBearer security scheme: adds Swagger UI Authorize padlock for bearer tokens
security = HTTPBearer(auto_error=False)


class AuthRequest(BaseModel):
    email: str | None = None
    password: str | None = None


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict:
    """Reusable auth guard: extracts Bearer token, verifies it via Supabase, and returns user dict."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Access token required"}
        )
    
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid or expired token"}
            )
        user = user_response.user
        return {
            "id": user.id,
            "email": user.email,
            "created_at": str(user.created_at) if user.created_at else None,
            "token": token
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"}
        )


@app.get("/")
def read_root():
    return {"name": "Auth API", "status": "running"}


@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def sign_up(body: AuthRequest):
    """Register a new user account with Supabase Auth."""
    if not body.email or not body.email.strip():
        raise HTTPException(status_code=400, detail={"error": "Email is required"})
    if not body.password or not body.password.strip():
        raise HTTPException(status_code=400, detail={"error": "Password is required"})

    try:
        response = supabase.auth.sign_up({
            "email": body.email.strip(),
            "password": body.password
        })
        if not response.user:
            raise HTTPException(status_code=400, detail={"error": "Signup failed"})
        
        user_dict = {
            "id": response.user.id,
            "email": response.user.email,
            "created_at": str(response.user.created_at) if response.user.created_at else None
        }
        return {"message": "User registered successfully", "user": user_dict}
    except Exception as e:
        err_msg = str(e)
        raise HTTPException(status_code=400, detail={"error": err_msg})


@app.post("/auth/login", status_code=status.HTTP_200_OK)
def log_in(body: AuthRequest):
    """Authenticate with Supabase and return JWT access and refresh tokens."""
    if not body.email or not body.email.strip():
        raise HTTPException(status_code=400, detail={"error": "Email is required"})
    if not body.password or not body.password.strip():
        raise HTTPException(status_code=400, detail={"error": "Password is required"})

    try:
        response = supabase.auth.sign_in_with_password({
            "email": body.email.strip(),
            "password": body.password
        })
        if not response.session or not response.session.access_token:
            raise HTTPException(status_code=401, detail={"error": "Invalid login credentials"})

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer",
            "user": {
                "id": response.user.id,
                "email": response.user.email
            }
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid login credentials"})


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def log_out(current_user: dict = Depends(get_current_user)):
    """End the user's session with Supabase. Protected route requiring Bearer token."""
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    return None


@app.get("/public/info", status_code=status.HTTP_200_OK)
def get_public_info():
    """Public lobby endpoint open to anyone with no authentication."""
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile", status_code=status.HTTP_200_OK)
def get_profile(current_user: dict = Depends(get_current_user)):
    """Protected endpoint: returns private profile data of the verified user."""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "created_at": current_user["created_at"]
    }


@app.get("/protected/dashboard", status_code=status.HTTP_200_OK)
def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Second protected endpoint: verifies guard reusability across routes."""
    return {
        "message": f"Welcome to your private dashboard, {current_user['email']}!",
        "user_id": current_user["id"],
        "features": ["SEO Audits", "Rank Tracking", "API Keys"]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Server running and connected to Supabase on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
