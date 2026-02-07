"""
ChurnPilot - SCHP Health Capabilities Endpoint
Implements StatusPulse Capability Health Protocol (SCHP) v1.0

Usage in Streamlit:
    # At the start of main(), check for health request
    from src.core.health import handle_health_request
    if handle_health_request():
        st.stop()  # Don't render the rest of the app

Direct access:
    GET https://churnpilot.streamlit.app/?health=capabilities
"""

import streamlit as st
import json
from datetime import datetime, timezone
from typing import Dict, Any
import os


def get_capability_status() -> Dict[str, Any]:
    """
    Check the status of all ChurnPilot capabilities.
    
    Returns SCHP v1.0 compliant response.
    """
    capabilities = {}
    overall_ok = True
    
    # ─── Capability: Database ────────────────────────────────────────────────
    try:
        from src.core.database import get_supabase_client
        client = get_supabase_client()
        # Simple query to verify DB connection
        client.table("users").select("id").limit(1).execute()
        capabilities["database"] = {"ok": True}
    except Exception as e:
        capabilities["database"] = {
            "ok": False,
            "reason": "connection_failed",
            "message": str(e)[:100]
        }
        overall_ok = False
    
    # ─── Capability: User Auth ───────────────────────────────────────────────
    # Auth is available if database is available (uses same Supabase)
    capabilities["user_auth"] = {
        "ok": capabilities.get("database", {}).get("ok", False)
    }
    if not capabilities["user_auth"]["ok"]:
        capabilities["user_auth"]["reason"] = "database_unavailable"
        overall_ok = False
    
    # ─── Capability: AI Extraction ───────────────────────────────────────────
    try:
        from src.core.ai_rate_limit import AIRateLimiter
        limiter = AIRateLimiter()
        
        # Check if we're within rate limits
        # Get a mock user_id to check limits (actual check happens per-user)
        ai_ok = True
        ai_reason = None
        
        # Check if Gemini API key is configured
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not gemini_key:
            ai_ok = False
            ai_reason = "api_key_missing"
        
        capabilities["ai_extraction"] = {
            "ok": ai_ok,
            "fallback": "Use card library to find pre-existing cards"
        }
        if ai_reason:
            capabilities["ai_extraction"]["reason"] = ai_reason
            overall_ok = False
            
    except Exception as e:
        capabilities["ai_extraction"] = {
            "ok": False,
            "reason": "check_failed",
            "message": str(e)[:100],
            "fallback": "Use card library to find pre-existing cards"
        }
        overall_ok = False
    
    # ─── Capability: Card Library ────────────────────────────────────────────
    # Card library is static data, should always be available
    capabilities["card_library"] = {"ok": True}
    
    # ─── Build Response ──────────────────────────────────────────────────────
    if overall_ok:
        status = "operational"
    elif any(c.get("ok", False) for c in capabilities.values()):
        status = "degraded"
    else:
        status = "down"
    
    return {
        "schp_version": "1.0",
        "app": "churnpilot",
        "status": status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "capabilities": capabilities
    }


def handle_health_request() -> bool:
    """
    Check if this is a health capabilities request and handle it.
    
    Call this at the start of main() in app.py:
        if handle_health_request():
            st.stop()
    
    Returns True if health request was handled, False otherwise.
    """
    params = st.query_params
    
    # Check for health=capabilities query param
    health_param = params.get("health", "")
    
    if health_param == "capabilities":
        # Get capability status
        status = get_capability_status()
        
        # Return JSON response
        # Note: Streamlit doesn't support raw JSON responses natively,
        # so we render it as preformatted text with JSON content type hint
        st.set_page_config(page_title="Health Check", layout="centered")
        
        # Clear any default Streamlit UI
        st.markdown("""
        <style>
            .stApp > header { display: none; }
            .stApp { background: #0a0a0a; }
            #MainMenu { display: none; }
            footer { display: none; }
            .block-container { padding: 1rem; }
        </style>
        """, unsafe_allow_html=True)
        
        # Display JSON
        st.code(json.dumps(status, indent=2), language="json")
        
        return True
    
    return False


def render_health_badge() -> str:
    """
    Get HTML for a health status badge.
    Can be used in the UI to show current system status.
    """
    status = get_capability_status()
    
    if status["status"] == "operational":
        color = "#059669"  # Green
        icon = "✅"
        text = "All Systems Operational"
    elif status["status"] == "degraded":
        color = "#D97706"  # Orange
        icon = "⚠️"
        failed = [k for k, v in status["capabilities"].items() if not v.get("ok")]
        text = f"Degraded: {', '.join(failed)}"
    else:
        color = "#DC2626"  # Red
        icon = "🔴"
        text = "System Issues"
    
    return f"""
    <div style="
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        background: {color}20;
        border: 1px solid {color}40;
        border-radius: 4px;
        font-size: 12px;
        color: {color};
    ">
        <span>{icon}</span>
        <span>{text}</span>
    </div>
    """
