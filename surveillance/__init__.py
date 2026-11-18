# =============================================================================
# FILE:      surveillance/__init__.py
# LOCATION:  Intelligent_Tomato_Farm/surveillance/__init__.py
# PURPOSE:   Package initializer. Exposes surveillance_router so the main app
#            can mount it with one import.
# =============================================================================

from .router import surveillance_router  # noqa: F401
