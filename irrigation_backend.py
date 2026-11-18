# =============================================================================
# FILE:      irrigation_backend.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation_backend.py
# PURPOSE:   Main FastAPI app for the whole project.
#            - Mounts the irrigation router (existing behavior)
#            - Mounts the surveillance router (new)
#            - Mounts the tomato router (new)
#            - Serves the frontend from /static and /
#            - Runs the recording sweeper on startup
#            - Runs uvicorn at 0.0.0.0:8000
# =============================================================================

from __future__ import annotations
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import os

import warnings
warnings.filterwarnings("ignore")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

import config
from irrigation import irrigation_router
from irrigation.router import register_websocket
from irrigation.models import load_ai_model, train_ai_model
from irrigation.neural import train_neural_network


# --- Optional new routers (import guarded so the app still boots if the
#     surveillance or tomato packages are not yet present during dev) --------
try:
    from surveillance import surveillance_router  # type: ignore
except Exception as e:
    print(f"[irrigation_backend] surveillance router unavailable: {e}")
    surveillance_router = None

try:
    from tomato import tomato_router  # type: ignore
except Exception as e:
    print(f"[irrigation_backend] tomato router unavailable: {e}")
    tomato_router = None


app = FastAPI(title="Intelligent Tomato Farm")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static frontend -------------------------------------------------------
os.makedirs(config.FRONTEND_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=config.FRONTEND_DIR), name="static")

# --- Routers ---------------------------------------------------------------
app.include_router(irrigation_router)
if surveillance_router is not None:
    app.include_router(surveillance_router)
if tomato_router is not None:
    app.include_router(tomato_router)

# --- WebSocket (single shared channel) -------------------------------------
register_websocket(app)


# --- Startup tasks ---------------------------------------------------------
@app.on_event("startup")
async def _startup():
    print("[irrigation_backend] Startup")

    if not load_ai_model():
        print("[irrigation_backend] Training initial irrigation AI model...")
        train_ai_model()

    print("[irrigation_backend] Training neural fallback model (if data)...")
    train_neural_network()

    # Start the recording sweeper in the background.
    try:
        from surveillance.recordings import sweeper_loop  # type: ignore
        asyncio.create_task(sweeper_loop())
        print("[irrigation_backend] Recording sweeper started.")
    except Exception as e:
        print(f"[irrigation_backend] Sweeper not started: {e}")

# -----------------------------------------------------------------------------
# FAVICON — silence the 404 in browser logs
# -----------------------------------------------------------------------------
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    icon_path = os.path.join("static", "favicon.ico")
    if os.path.isfile(icon_path):
        return FileResponse(icon_path)
    # Fallback: return a 204 No Content so the browser stops asking
    from fastapi import Response
    return Response(status_code=204)

@app.get("/api/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    print(config.describe())
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        #ssl_keyfile="certs/key.pem",
        #ssl_certfile="certs/cert.pem",
    )
