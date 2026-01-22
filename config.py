"""
Centralized configuration for Multi-API Monitoring System
"""

# API Services Configuration
API_SERVICES = {
    "Multiply API": {
        "port": 8001,
        "health_url": "http://localhost:8001/health",
        "test_url": "http://localhost:8001/multiply?a=5&b=3",
        "app_module": "multiply_app:app"
    },
    "Addition API": {
        "port": 8002,
        "health_url": "http://localhost:8002/health",
        "test_url": "http://localhost:8002/addition?a=10&b=5",
        "app_module": "addition_app:app"
    },
    "Division API": {
        "port": 8003,
        "health_url": "http://localhost:8003/health",
        "test_url": "http://localhost:8003/division?a=20&b=4",
        "app_module": "division_app:app"
    }
}

# AI Agent Configuration
AI_CONFIG = {
    "model": "gpt-4o-mini",
    "temperature": 0.7
}

# Monitoring Configuration
MONITORING_CONFIG = {
    "check_interval": 15,  # seconds between health checks
    "restart_delay": 30,   # seconds to wait before restart
    "max_restart_attempts": 3,
    "health_check_attempts": 10,  # attempts to verify API health after restart
    "health_check_wait": 3,       # seconds between health check attempts during restart verification
    "health_check_timeout": 5
}

# Defensive defaults (prevents KeyError if config is partially modified elsewhere)
MONITORING_CONFIG.setdefault("health_check_attempts", 10)
MONITORING_CONFIG.setdefault("health_check_wait", 3)
MONITORING_CONFIG.setdefault("health_check_timeout", 5)
MONITORING_CONFIG.setdefault("restart_delay", 30)
MONITORING_CONFIG.setdefault("check_interval", 15)

# Email Configuration (loaded from .env)
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_CONFIG = {
    "sender": os.getenv("EMAIL_SENDER"),
    "password": os.getenv("EMAIL_APP_PASSWORD"),
    "recipients": os.getenv("EMAIL_RECIPIENTS", "").split(",")
}
