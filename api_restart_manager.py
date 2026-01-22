import subprocess
import time
import requests
import psutil
import os
import sys
from config import API_SERVICES, MONITORING_CONFIG

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_MONITORING_CONFIG = {
    "health_check_attempts": 10,
    "health_check_wait": 3,
    "health_check_timeout": 5,
}

def _merged_monitoring_config():
    """Defaults overlaid with MONITORING_CONFIG; tolerate missing/invalid config objects."""
    cfg = dict(DEFAULT_MONITORING_CONFIG)
    try:
        if isinstance(MONITORING_CONFIG, dict):
            cfg.update({k: v for k, v in MONITORING_CONFIG.items() if v is not None})
    except Exception:
        pass
    return cfg

def _to_int(value, default):
    try:
        return int(value)
    except Exception:
        return default

def _to_float(value, default):
    try:
        return float(value)
    except Exception:
        return default

def find_process_on_port(port):
    """Find process using specific port"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            connections = proc.connections()
            if connections:
                for conn in connections:
                    if hasattr(conn, 'laddr') and conn.laddr.port == port:
                        return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None

def kill_api_on_port(port):
    """Kill API process on specific port"""
    proc = find_process_on_port(port)
    
    if proc:
        try:
            print(f"🔍 Found process: PID {proc.pid} on port {port}")
            proc.kill()
            proc.wait(timeout=5)
            print(f"✅ Process on port {port} terminated")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Failed to kill process on port {port}: {e}")
            return False
    print(f"ℹ️ No process found on port {port}")
    return True

def start_specific_api(api_name):
    """Start a specific API"""
    config = API_SERVICES.get(api_name)
    if not config:
        print(f"❌ Unknown API: {api_name}")
        return None

    try:
        python_exe = sys.executable

        cmd = [
            python_exe,
            "-m", "uvicorn",
            config["app_module"],
            "--host", "0.0.0.0",
            "--port", str(config["port"]),
        ]

        print(f"📂 Working directory: {SCRIPT_DIR}")
        print(f"🐍 Python executable: {python_exe}")
        print(f"🚀 Starting {api_name} on port {config['port']}...")

        # Detach child so stopping the monitor (Ctrl+C) won't stop the API.
        # Also avoid PIPEs; when parent exits, closed pipes can break the child.
        stdout_target = subprocess.DEVNULL
        stderr_target = subprocess.DEVNULL

        if os.name == "nt":
            process = subprocess.Popen(
                cmd,
                cwd=SCRIPT_DIR,
                stdout=stdout_target,
                stderr=stderr_target,
                creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            process = subprocess.Popen(
                cmd,
                cwd=SCRIPT_DIR,
                stdout=stdout_target,
                stderr=stderr_target,
                start_new_session=True,
            )

        print(f"✅ {api_name} restart initiated (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Failed to start {api_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def verify_api_health(api_name):
    """Verify if specific API is healthy after restart"""
    config = API_SERVICES.get(api_name)
    if not config:
        return False

    cfg = _merged_monitoring_config()
    max_attempts = _to_int(cfg.get("health_check_attempts"), DEFAULT_MONITORING_CONFIG["health_check_attempts"])
    wait_time = _to_float(cfg.get("health_check_wait"), DEFAULT_MONITORING_CONFIG["health_check_wait"])
    timeout = _to_float(cfg.get("health_check_timeout"), DEFAULT_MONITORING_CONFIG["health_check_timeout"])

    if max_attempts < 1:
        max_attempts = 1
    if wait_time < 0:
        wait_time = 0.0
    if timeout <= 0:
        timeout = float(DEFAULT_MONITORING_CONFIG["health_check_timeout"])

    print(f"\n⏳ Waiting for {api_name} to become healthy...")
    
    for attempt in range(1, max_attempts + 1):
        try:
            time.sleep(wait_time)
            response = requests.get(config["health_url"], timeout=timeout)
            
            if response.status_code == 200:
                print(f"✅ {api_name} is healthy after {attempt * wait_time} seconds")
                return True
            else:
                print(f"⏳ Attempt {attempt}/{max_attempts}: Status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"⏳ Attempt {attempt}/{max_attempts}: Connection refused (API starting...)")
        except Exception as e:
            print(f"⏳ Attempt {attempt}/{max_attempts}: {str(e)}")
    
    print(f"❌ {api_name} failed to recover")
    return False

def restart_specific_api(api_name):
    """Complete restart workflow for specific API"""
    config = API_SERVICES.get(api_name)
    if not config:
        print(f"❌ Unknown API: {api_name}")
        return False
    
    print("\n" + "="*70)
    print(f"🔄 INITIATING AUTOMATIC RESTART FOR {api_name}")
    print("="*70)
    
    print(f"\n1️⃣ Terminating existing process on port {config['port']}...")
    if not kill_api_on_port(config['port']):
        print("⚠️ Warning: Could not terminate existing process cleanly")
    
    print(f"\n2️⃣ Starting new {api_name} instance...")
    process = start_specific_api(api_name)
    
    if not process:
        print(f"❌ Failed to start {api_name} process")
        return False
    
    print(f"\n3️⃣ Verifying {api_name} health...")
    success = verify_api_health(api_name)
    
    if success:
        print("\n" + "="*70)
        print(f"✅ {api_name} RESTART SUCCESSFUL")
        print("="*70)
    else:
        print("\n" + "="*70)
        print(f"❌ {api_name} RESTART FAILED")
        print("="*70)
    
    return success
