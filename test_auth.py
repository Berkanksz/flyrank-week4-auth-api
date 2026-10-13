"""Comprehensive end-to-end tests for the Auth API.

Run with:  python test_auth.py
"""
import uuid
import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_public_info():
    r = client.get("/public/info")
    assert r.status_code == 200
    assert r.json() == {"message": "Welcome stranger! This info is public."}


def test_protected_routes_without_token():
    assert client.get("/protected/profile").status_code == 401
    assert client.get("/protected/dashboard").status_code == 401
    assert client.post("/auth/logout").status_code == 401


def test_protected_routes_with_forged_token():
    headers = {"Authorization": "Bearer totally_fake_forged_token"}
    r = client.get("/protected/profile", headers=headers)
    assert r.status_code == 401
    assert r.json() == {"detail": {"error": "Invalid or expired token"}}


def test_validation_errors():
    # Empty signup
    assert client.post("/auth/signup", json={}).status_code == 400
    assert client.post("/auth/signup", json={"email": "only@email.com"}).status_code == 400
    assert client.post("/auth/signup", json={"password": "onlypass"}).status_code == 400

    # Empty login
    assert client.post("/auth/login", json={}).status_code == 400
    assert client.post("/auth/login", json={"email": "wrong@example.com", "password": "wrong"}).status_code == 401


def test_full_auth_lifecycle():
    # Generate unique email for reproducible test run
    unique_email = f"berkan.test.{uuid.uuid4().hex[:6]}@gmail.com"
    password = "StrongPassword123!"

    # 1. Sign up
    r_signup = client.post("/auth/signup", json={"email": unique_email, "password": password})
    assert r_signup.status_code == 201, f"Signup failed: {r_signup.text}"
    signup_data = r_signup.json()
    assert "user" in signup_data
    assert signup_data["user"]["email"] == unique_email
    print(f"1. Signed up user successfully: {unique_email}")

    # 2. Log in
    r_login = client.post("/auth/login", json={"email": unique_email, "password": password})
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    login_data = r_login.json()
    assert "access_token" in login_data
    token = login_data["access_token"]
    print("2. Logged in and received access_token successfully")

    # 3. Access protected profile
    headers = {"Authorization": f"Bearer {token}"}
    r_profile = client.get("/protected/profile", headers=headers)
    assert r_profile.status_code == 200, f"Profile failed: {r_profile.text}"
    profile = r_profile.json()
    assert profile["email"] == unique_email
    assert "id" in profile
    print(f"3. Accessed protected profile: ID {profile['id']}")

    # 4. Access second protected route (dashboard)
    r_dash = client.get("/protected/dashboard", headers=headers)
    assert r_dash.status_code == 200
    assert "Welcome to your private dashboard" in r_dash.json()["message"]
    print("4. Accessed protected dashboard using the same middleware guard")

    # 5. Log out
    r_logout = client.post("/auth/logout", headers=headers)
    assert r_logout.status_code == 204
    print("5. Logged out successfully (204 No Content)")


if __name__ == "__main__":
    test_public_info()
    test_protected_routes_without_token()
    test_protected_routes_with_forged_token()
    test_validation_errors()
    test_full_auth_lifecycle()
    print("\nAll auth tests passed successfully!")
