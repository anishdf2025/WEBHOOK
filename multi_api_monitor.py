import time
import requests
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from email_webhook import send_email_alert
from api_restart_manager import restart_specific_api
from config import API_SERVICES, AI_CONFIG, MONITORING_CONFIG, EMAIL_CONFIG
import os
from dotenv import load_dotenv

load_dotenv()

# Define the state
class MonitorState(TypedDict):
    api_name: str
    api_url: str
    api_port: int
    api_status: str
    error_details: str
    agent_analysis: str
    email_subject: str
    email_body: str
    human_approval: str
    action_taken: str
    email_sent: bool
    restart_attempted: bool
    recovery_status: str
    recovery_email_sent: bool

# Initialize LLM with config (fallbacks avoid KeyError on partial config)
llm = ChatOpenAI(
    model=AI_CONFIG.get("model", "gpt-4o-mini"),
    temperature=AI_CONFIG.get("temperature", 0.7),
)

def check_api_health(state: MonitorState) -> MonitorState:
    """Node: Check API health status"""
    print(f"\n🔍 Checking {state['api_name']} (Port {state['api_port']})...")
    
    try:
        r = requests.get(state['api_url'], timeout=5)
        
        if r.status_code == 200:
            state["api_status"] = "healthy"
            state["error_details"] = f"{state['api_name']} is functioning normally on port {state['api_port']}"
        else:
            state["api_status"] = "unhealthy"
            state["error_details"] = f"Status Code: {r.status_code}\nResponse: {r.text}"
            
    except Exception as e:
        state["api_status"] = "down"
        state["error_details"] = f"Connection Error: {str(e)}\nPort: {state['api_port']}"
    
    state["email_sent"] = False
    state["restart_attempted"] = False
    state["recovery_email_sent"] = False
    return state

def agent_analyze(state: MonitorState) -> MonitorState:
    """Node: Agent analyzes the situation and drafts email"""
    print(f"\n🤖 AI Agent analyzing {state['api_name']} situation...")
    
    email_type = "recovery" if state.get("recovery_status") == "success" else "alert"
    
    if email_type == "alert":
        prompt = f"""
API Name: {state['api_name']}
Port: {state['api_port']}
Health Check URL: {state['api_url']}
API Status: {state['api_status']}
Error Details: {state['error_details']}

Tasks:
1. Analyze the severity and root cause
2. Draft a professional alert email informing that:
   - The specific API ({state['api_name']}) running on port {state['api_port']} is currently down
   - Our agentic AI system is automatically attempting to restart it
   - They should wait a few moments
   - We will send an update once the API is back online

Include:
   - Start with "Hi Team,"
   - Mention the specific API name and port prominently
   - Apologetic and reassuring tone
   - Clear subject line with API name and port
   - Brief issue description
   - Automated recovery information
   - End with "Thanks & Regards,\nAI Agent\nAutomated Monitoring System"

Format your response as:
ANALYSIS: [your analysis]
---
SUBJECT: [email subject with API name]
---
EMAIL_BODY:
[email content]
"""
    else:
        prompt = f"""
API Name: {state['api_name']}
Port: {state['api_port']}

The {state['api_name']} was down but has now been successfully recovered by our agentic AI system.

Tasks:
Draft a professional recovery notification email that:
   - Confirms the specific API ({state['api_name']}) on port {state['api_port']} is now operational
   - Thanks them for their patience
   - Mentions automated recovery by AI system
   - Provides reassurance

Include:
   - Start with "Hi Team,"
   - Mention the specific API name and port
   - End with "Thanks & Regards,\nAI Agent\nAutomated Monitoring System"

Format your response as:
ANALYSIS: API successfully recovered automatically
---
SUBJECT: [email subject with API name]
---
EMAIL_BODY:
[email content]
"""
    
    messages = [
        SystemMessage(content="""You are an expert DevOps monitoring assistant. 
        Draft professional, reassuring emails for API incidents and recoveries.
        Always sign emails as "AI Agent" from "Automated Monitoring System".
        Always mention the specific API name and port.
        Never use personal names or job titles."""),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Parse response
    parts = content.split("---")
    state["agent_analysis"] = parts[0].replace("ANALYSIS:", "").strip()
    state["email_subject"] = parts[1].replace("SUBJECT:", "").strip()
    state["email_body"] = parts[2].replace("EMAIL_BODY:", "").strip()
    
    return state

def attempt_restart(state: MonitorState) -> MonitorState:
    """Node: Attempt automatic API restart for specific service"""
    print(f"\n🔄 Attempting automatic restart for {state['api_name']}...")

    restart_delay = int(MONITORING_CONFIG.get("restart_delay", 30))
    if restart_delay < 0:
        restart_delay = 0

    print(f"\n⏰ Waiting {restart_delay} seconds before restart...")
    for i in range(restart_delay, 0, -1):
        print(f"⏳ {i} seconds remaining...", end="\r")
        time.sleep(1)
    print("\n")
    
    success = restart_specific_api(state['api_name'])
    state["restart_attempted"] = True
    state["recovery_status"] = "success" if success else "failed"
    
    return state

def human_review(state: MonitorState) -> MonitorState:
    """Node: Human reviews and approves/rejects/edits"""
    email_type = "🔄 RECOVERY" if state.get("recovery_status") == "success" else "🚨 ALERT"
    
    print("\n" + "="*70)
    print(f"🧑 HUMAN REVIEW REQUIRED - {email_type} - {state['api_name']}")
    print("="*70)
    
    print("\n📊 AGENT ANALYSIS:")
    print("-"*70)
    print(state["agent_analysis"])
    
    print("\n" + "="*70)
    print("📧 PROPOSED EMAIL")
    print("="*70)
    print(f"\n📌 SUBJECT: {state['email_subject']}")
    print(f"\n📬 TO: {', '.join(EMAIL_CONFIG['recipients'])}")
    print("\n" + "-"*70)
    print("MESSAGE BODY:")
    print("-"*70)
    print(state["email_body"])
    print("="*70)
    
    while True:
        print("\n🎯 OPTIONS:")
        print("  [1] Approve and send")
        print("  [2] Reject and cancel")
        print("  [3] Edit email body")
        print("  [4] Edit subject")
        
        choice = input("\nYour choice (1-4): ").strip()
        
        if choice == "1":
            state["human_approval"] = "approved"
            break
        elif choice == "2":
            state["human_approval"] = "rejected"
            break
        elif choice == "3":
            print("\n✏️ Enter new email body (type END on new line when done):")
            lines = []
            while True:
                line = input()
                if line == "END":
                    break
                lines.append(line)
            state["email_body"] = "\n".join(lines)
        elif choice == "4":
            state["email_subject"] = input("\n✏️ Enter new subject: ").strip()
        else:
            print("❌ Invalid choice. Please enter 1-4.")
    
    return state

def send_email_action(state: MonitorState) -> MonitorState:
    """Node: Send the email (only once)"""
    is_recovery = state.get("recovery_status") == "success"
    
    if is_recovery and state["recovery_email_sent"]:
        print("\n⚠️ Recovery email already sent, skipping...")
        return state
    
    if not is_recovery and state["email_sent"]:
        print("\n⚠️ Alert email already sent, skipping...")
        return state
    
    if state["human_approval"] == "approved":
        print(f"\n📤 Sending email for {state['api_name']}...")
        try:
            send_email_alert(state["email_body"], state["email_subject"])
            state["action_taken"] = "Email sent successfully ✅"
            
            if is_recovery:
                state["recovery_email_sent"] = True
            else:
                state["email_sent"] = True
                
            print(f"\n✅ {state['action_taken']}")
        except Exception as e:
            state["action_taken"] = f"Failed to send email: {str(e)}"
            print(f"\n❌ {state['action_taken']}")
    else:
        state["action_taken"] = "Email cancelled by user ❌"
        print(f"\n{state['action_taken']}")
    
    return state

def should_alert(state: MonitorState) -> str:
    """Routing: Decide if alert is needed"""
    if state["api_status"] == "healthy":
        return "healthy"
    else:
        return "needs_alert"

def should_attempt_restart(state: MonitorState) -> str:
    """Routing: Should we attempt restart after sending alert?"""
    return "attempt_restart"

def check_recovery(state: MonitorState) -> str:
    """Routing: Check if recovery was successful"""
    if state.get("recovery_status") == "success":
        return "recovered"
    else:
        return "failed"

# Build the graph
def create_monitoring_graph():
    workflow = StateGraph(MonitorState)
    
    # Add nodes
    workflow.add_node("check_health", check_api_health)
    workflow.add_node("analyze_alert", agent_analyze)
    workflow.add_node("human_review_alert", human_review)
    workflow.add_node("send_alert_email", send_email_action)
    workflow.add_node("attempt_restart", attempt_restart)
    workflow.add_node("analyze_recovery", agent_analyze)
    workflow.add_node("human_review_recovery", human_review)
    workflow.add_node("send_recovery_email", send_email_action)
    
    # Add edges
    workflow.set_entry_point("check_health")
    
    workflow.add_conditional_edges(
        "check_health",
        should_alert,
        {
            "healthy": END,
            "needs_alert": "analyze_alert"
        }
    )
    
    workflow.add_edge("analyze_alert", "human_review_alert")
    workflow.add_edge("human_review_alert", "send_alert_email")
    
    workflow.add_conditional_edges(
        "send_alert_email",
        should_attempt_restart,
        {
            "attempt_restart": "attempt_restart"
        }
    )
    
    workflow.add_conditional_edges(
        "attempt_restart",
        check_recovery,
        {
            "recovered": "analyze_recovery",
            "failed": END
        }
    )
    
    workflow.add_edge("analyze_recovery", "human_review_recovery")
    workflow.add_edge("human_review_recovery", "send_recovery_email")
    workflow.add_edge("send_recovery_email", END)
    
    return workflow.compile()

# Main monitoring loop
def run_monitoring():
    graph = create_monitoring_graph()
    
    print("🚀 Starting Multi-API LangGraph Agentic Monitor with Auto-Recovery")
    print("="*70)
    print(f"📋 Monitoring {len(API_SERVICES)} separate API services:")
    for api_name, config in API_SERVICES.items():
        print(f"   ✓ {api_name} - Port {config['port']}")
    print("="*70)
    
    check_interval = int(MONITORING_CONFIG.get("check_interval", 15))
    if check_interval < 1:
        check_interval = 1

    while True:
        for api_name, config in API_SERVICES.items():
            initial_state = {
                "api_name": api_name,
                "api_url": config["health_url"],
                "api_port": config["port"],
                "api_status": "",
                "error_details": "",
                "agent_analysis": "",
                "email_subject": "",
                "email_body": "",
                "human_approval": "",
                "action_taken": "",
                "email_sent": False,
                "restart_attempted": False,
                "recovery_status": "",
                "recovery_email_sent": False
            }
            
            result = graph.invoke(initial_state)
            
            if result["api_status"] == "healthy":
                print(f"✅ {api_name} (Port {config['port']}) is UP")
            else:
                print(f"🏁 {api_name} Final Status: {result['action_taken']}")
                if result.get("recovery_status") == "success":
                    print(f"✅ {api_name} successfully recovered and notification sent!")
        
        print("\n" + "="*70)
        print(f"⏰ Next check in {check_interval} seconds...")
        print("="*70)
        time.sleep(check_interval)

if __name__ == "__main__":
    run_monitoring()
