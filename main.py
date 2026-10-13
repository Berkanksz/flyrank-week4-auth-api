import os
from fastapi import FastAPI, HTTPException, status, Header
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

from supabase_client import supabase

load_dotenv()

app = FastAPI(
    title="FlyRank Auth API",
    description="Authentication and protected routes using Supabase Auth and Bearer JWT",
    version="1.0.0"
)


class AuthRequest(BaseModel):
    email: str | None = None
    password: str | None = None


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


@app.get("/public/info", status_code=status.HTTP_200_OK)
def get_public_info():
    """Public lobby endpoint open to anyone with no authentication."""
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile")
def get_profile(authorization: str | None = Header(default=None)):
    """Stage 2: checks if an access token was provided in Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"error": "Access token required"})
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail={"error": "Access token required"})
    return {"message": "Access token received", "token_preview": token[:10] + "..."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Server running and connected to Supabase on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
