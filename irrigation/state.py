# =============================================================================
# FILE:      irrigation/state.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/state.py
# PURPOSE:   Shared mutable runtime state for the irrigation subsystem.
#            Every route imports state from this single module so there are
#            no circular imports.
# =============================================================================

from __future__ import annotations
from datetime import datetime
from typing import Optional, Any

# Pump / override
manual_override: bool = False
pump_status: bool = False

# Model bookkeeping
last_trained_count: int = 0
ai_model: Any = None
scaler: Any = None
model_accuracy: float = 0.0

# Admin lock
admin_lock: bool = False
admin_lock_user: Optional[str] = None
admin_lock_time: Optional[datetime] = None

# Neural / fuzzy
nn_model: Any = None
nn_trained: bool = False
fuzzy_decider: Any = None
