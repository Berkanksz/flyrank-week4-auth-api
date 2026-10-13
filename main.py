import os
from fastapi import FastAPI
from dotenv import load_dotenv

import supabase_client

load_dotenv()

app = FastAPI(
    title="FlyRank Auth API",
    description="Authentication and protected routes using Supabase Auth and Bearer JWT",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"name": "Auth API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Server running and connected to Supabase on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
