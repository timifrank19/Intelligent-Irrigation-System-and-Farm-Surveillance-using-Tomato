# =============================================================================
# FILE:      surveillance/auth.py
# LOCATION:  Intelligent_Tomato_Farm/surveillance/auth.py
# PURPOSE:   Admin gate for surveillance and tomato endpoints.
#            The frontend stores the admin password in localStorage and
#            sends it on every protected request via the X-Admin-Key header.
# =============================================================================

from __future__ import annotations
from fastapi import Header, HTTPException

import config


def require_admin(x_admin_key: str = Header(default="")):
    """
    FastAPI dependency. Raises 401 if the header is missing or wrong.
    Use as:
        @router.post("/api/surveillance/recordings", dependencies=[Depends(require_admin)])
    """
    if x_admin_key != config.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="admin_required")
    return True
