# 🤖 Multi-API Agentic Monitoring System with Auto-Recovery

## 📋 Overview

This is an **intelligent, autonomous API monitoring system** that uses **LangGraph** and **OpenAI GPT-4** to:

1. **Monitor multiple FastAPI services** (Addition, Multiplication, Division APIs)
2. **Detect failures** automatically via health checks
3. **Generate human-readable incident reports** using AI
4. **Automatically restart failed APIs** without manual intervention
5. **Send email alerts** for downtime and recovery notifications
6. **Provide human-in-the-loop review** before sending emails

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Multi-API Monitor                         │
│                  (multi_api_monitor.py)                     │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │         LangGraph Workflow (StateGraph)          │     │
│  │                                                   │     │
│  │  1. check_health → Health check all APIs         │     │
│  │  2. agent_analyze → AI drafts alert email        │     │
│  │  3. human_review_alert → Human approval          │     │
│  │  4. send_alert_email → Email sent                │     │
│  │  5. attempt_restart → Auto-restart failed API    │     │
│  │  6. analyze_recovery → AI drafts success email   │     │
│  │  7. human_review_recovery → Human approval       │     │
│  │  8. send_recovery_email → Email sent             │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  Uses: OpenAI GPT-4o-mini for incident analysis            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   API Restart Manager                 │
        │   (api_restart_manager.py)            │
        │                                       │
        │   • Finds process on port (psutil)    │
        │   • Kills existing process            │
        │   • Starts new Uvicorn instance       │
        │   • Detached (survives Ctrl+C)        │
        │   • Verifies health after restart     │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   3 FastAPI Services                  │
        │                                       │
        │   • Addition API (port 8002)          │
        │   • Multiplication API (port 8001)    │
        │   • Division API (port 8003)          │
        │                                       │
        │   Each has: /health + operation route │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   Email Webhook                       │
        │   (email_webhook.py)                  │
        │                                       │
        │   • Gmail SMTP SSL (port 465)         │
        │   • Sends alerts + recovery emails    │
        └───────────────────────────────────────┘
```

---

## 📂 Project Structure

```
WebHook/
├── README.md                    # This file
├── .env                         # Environment variables (secrets)
├── .gitignore                   # Ignore .env, venv, __pycache__
├── requirements.txt             # Python dependencies
├── config.py                    # Centralized configuration
├── multi_api_monitor.py         # Main monitoring loop + LangGraph
├── api_restart_manager.py       # Auto-restart logic
├── email_webhook.py             # Email alert sender
├── addition_app.py              # FastAPI: Addition service
├── multiply_app.py              # FastAPI: Multiplication service
└── division_app.py              # FastAPI: Division service
```

---

## 🚀 Features

### 1. **Agentic AI Analysis**
- Uses **OpenAI GPT-4o-mini** to analyze API failures
- Generates professional incident reports automatically
- Drafts alert emails with root cause analysis
- Creates recovery confirmation emails after successful restarts

### 2. **Automatic API Recovery**
- Detects down APIs via health checks
- Kills stuck processes on specific ports
- Restarts APIs in **detached mode** (survives monitor shutdown)
- Verifies health after restart with configurable retry logic

### 3. **Human-in-the-Loop Email Review**
- AI drafts emails, but **human approves** before sending
- Options to:
  - ✅ Approve and send
  - ❌ Reject and cancel
  - ✏️ Edit subject or body
- Prevents duplicate emails (tracks sent status)

### 4. **Multi-API Monitoring**
- Monitors 3 independent FastAPI services
- Each API has its own port and health endpoint
- Sequential health checks with configurable intervals

### 5. **Email Notifications**
- **Alert emails** when APIs go down
- **Recovery emails** when APIs come back up
- Sent via Gmail SMTP (app password required)
- Multiple recipients supported

---

## ⚙️ Configuration

### `config.py`
```python
# API Services - Add/modify APIs here
API_SERVICES = {
    "Multiply API": {
        "port": 8001,
        "health_url": "http://localhost:8001/health",
        "app_module": "multiply_app:app"
    },
    # ... more APIs
}

# Monitoring Settings
MONITORING_CONFIG = {
    "check_interval": 15,           # Health check frequency (seconds)
    "restart_delay": 30,            # Wait before restart (seconds)
    "health_check_attempts": 10,    # Retry attempts after restart
    "health_check_wait": 3,         # Seconds between retries
    "health_check_timeout": 5       # Request timeout (seconds)
}

# AI Configuration
AI_CONFIG = {
    "model": "gpt-4o-mini",         # OpenAI model
    "temperature": 0.7              # Creativity level
}
```

### `.env` (Secrets)
```env
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
EMAIL_SENDER=your-email@gmail.com
EMAIL_APP_PASSWORD=your-gmail-app-password
EMAIL_RECIPIENTS=recipient1@gmail.com,recipient2@gmail.com
```

**⚠️ Security Notes:**
- Never commit `.env` to Git (already in `.gitignore`)
- Use Gmail **App Passwords**, not your regular password
- Rotate the OpenAI key shown in this repo (it's exposed)

---

## 🛠️ Installation

### 1. **Clone/Setup**
```bash
cd c:\Users\91955\Desktop\Anish\WebHook
python -m venv .venv
source .venv/bin/activate  # Linux/WSL
# OR
.venv\Scripts\activate     # Windows
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Configure Environment**
Create `.env` file:
```bash
cp .env.example .env  # If you have a template
nano .env             # Edit with your credentials
```

### 4. **Start APIs Manually (Optional)**
```bash
# Terminal 1
uvicorn multiply_app:app --host 0.0.0.0 --port 8001

# Terminal 2
uvicorn addition_app:app --host 0.0.0.0 --port 8002

# Terminal 3
uvicorn division_app:app --host 0.0.0.0 --port 8003
```

### 5. **Start Monitor**
```bash
python multi_api_monitor.py
```

---

## 🎯 How It Works

### **Normal Operation Flow**

1. **Health Check Loop** (every 15 seconds by default)
   ```
   For each API:
     → GET /health endpoint
     → If status 200: ✅ API is healthy
     → If error: 🚨 Trigger alert workflow
   ```

2. **Alert Workflow** (when API is down)
   ```
   API Down Detected
     ↓
   AI Analyzes Issue (GPT-4o-mini)
     ↓
   Drafts Alert Email
     ↓
   Human Reviews & Approves
     ↓
   Email Sent to Recipients
     ↓
   Automatic Restart Initiated
     ↓
   Wait 30 seconds
     ↓
   Kill Process on Port
     ↓
   Start New Uvicorn Instance (Detached)
     ↓
   Verify Health (10 attempts, 3s apart)
   ```

3. **Recovery Workflow** (after successful restart)
   ```
   API Health Restored
     ↓
   AI Drafts Recovery Email
     ↓
   Human Reviews & Approves
     ↓
   Success Email Sent
   ```

---

## 🧪 Testing

### **Test API Endpoints**
```bash
# Multiply API
curl http://localhost:8001/multiply?a=5&b=3
# Response: {"result": 15, "operation": "multiplication"}

# Addition API
curl http://localhost:8002/addition?a=10&b=5
# Response: {"result": 15, "operation": "addition"}

# Division API
curl http://localhost:8003/division?a=20&b=4
# Response: {"result": 5.0, "operation": "division"}

# Health Check
curl http://localhost:8001/health
# Response: {"status": "UP", "service": "Multiply API"}
```

### **Simulate Failure**
```bash
# Kill an API to trigger auto-recovery
kill -9 $(lsof -t -i:8001)  # Linux/WSL
# OR
taskkill /F /PID <PID>      # Windows

# Monitor will:
# 1. Detect failure in next health check
# 2. Draft alert email (AI)
# 3. Ask for human approval
# 4. Send alert email
# 5. Auto-restart API
# 6. Draft recovery email (AI)
# 7. Ask for human approval
# 8. Send recovery email
```

---

## 🔧 Troubleshooting

### **Problem: APIs stop when monitor stops**
**Solution:** Already fixed! APIs now start in detached mode (`start_new_session=True` on Linux, `CREATE_NEW_PROCESS_GROUP` on Windows).

### **Problem: `KeyError: 'health_check_attempts'`**
**Solution:** Fixed with defensive config defaults in `_merged_monitoring_config()`.

### **Problem: Email not sending**
**Checklist:**
- ✅ Gmail App Password set (not regular password)
- ✅ `EMAIL_APP_PASSWORD` not empty in `.env`
- ✅ Gmail "Less secure app access" NOT needed (app passwords work)
- ✅ Check spam folder

### **Problem: OpenAI API errors**
**Solution:**
- Verify `OPENAI_API_KEY` is valid (rotate if exposed)
- Check billing/quota: https://platform.openai.com/account/usage

### **Problem: Port already in use**
```bash
# Find process on port
lsof -i :8001        # Linux/WSL
netstat -ano | findstr :8001  # Windows

# Kill process
kill -9 <PID>        # Linux/WSL
taskkill /F /PID <PID>  # Windows
```

---

## 🔐 Security Best Practices

1. **Never commit `.env` to Git**
   - Already in `.gitignore`
   - Use environment variables or secret managers in production

2. **Rotate Exposed Credentials**
   - The OpenAI key in this repo is **compromised** (visible in `.env`)
   - Generate new key: https://platform.openai.com/api-keys
   - Same for Gmail app password

3. **Use App Passwords for Gmail**
   - Enable 2FA on Google account
   - Create App Password: https://myaccount.google.com/apppasswords
   - Never use your real Gmail password

4. **Restrict API Access**
   - Currently APIs bind to `0.0.0.0` (all interfaces)
   - In production, use `127.0.0.1` or firewall rules

---

## 📊 Monitoring Metrics

| Metric | Value | Configurable In |
|--------|-------|-----------------|
| Health Check Interval | 15 seconds | `config.py` → `check_interval` |
| Restart Delay | 30 seconds | `config.py` → `restart_delay` |
| Health Verification Attempts | 10 | `config.py` → `health_check_attempts` |
| Health Verification Wait | 3 seconds | `config.py` → `health_check_wait` |
| Request Timeout | 5 seconds | `config.py` → `health_check_timeout` |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📜 License

This project is for educational/internal use. Modify as needed.

---

## 🙋 Support

For issues or questions:
1. Check **Troubleshooting** section above
2. Review logs in terminal output
3. Contact: anishkumarmaurya12@gmail.com

---

## 🎓 Tech Stack

- **FastAPI** - High-performance async web framework
- **Uvicorn** - ASGI server
- **LangGraph** - AI workflow orchestration
- **LangChain** - LLM integration framework
- **OpenAI GPT-4o-mini** - Natural language generation
- **psutil** - Process management
- **smtplib** - Email sending
- **python-dotenv** - Environment variable management

---

## 📈 Future Enhancements

- [ ] Web dashboard for monitoring status
- [ ] Prometheus/Grafana metrics integration
- [ ] Slack/Discord webhook support
- [ ] Database logging for incident history
- [ ] Support for Kubernetes/Docker deployments
- [ ] Automatic rollback if restart fails
- [ ] Load testing before declaring healthy
- [ ] Multi-region health checks

---

**Made with ❤️ by AI Agent + Human Collaboration**
