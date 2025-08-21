#!/usr/bin/env python3
"""
Cost Monitoring Script for MealMateAI Performance Testing
Monitors API usage and costs in real-time during performance tests.
"""

import os
import sys
import time
import json
import argparse
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import threading
import signal

# Cost configuration (prices as of 2024)
COST_CONFIG = {
    "gemini": {
        "generation": {
            "input_tokens": 0.00001,   # Per token
            "output_tokens": 0.00003,  # Per token
            "average_call": 0.01       # Average per API call
        },
        "embeddings": {
            "per_request": 0.0001      # Per embedding request
        }
    },
    "daily_limit": float(os.getenv("GEMINI_API_DAILY_LIMIT", 50)),
    "hourly_limit": float(os.getenv("GEMINI_API_HOURLY_LIMIT", 5))
}

class CostMonitor:
    """Real-time cost monitoring for AI API usage"""
    
    def __init__(self, log_file="api_costs.log"):
        self.log_file = log_file
        self.current_costs = {
            "total": 0.0,
            "hourly": 0.0,
            "api_calls": 0,
            "start_time": datetime.now()
        }
        self.alerts_sent = set()
        self.shutdown_triggered = False
        self.monitoring = False
        
        # Load existing costs if any
        self.load_existing_costs()
    
    def load_existing_costs(self):
        """Load costs from previous runs today"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if entry['date'] == datetime.now().strftime('%Y-%m-%d'):
                                self.current_costs['total'] = entry.get('cumulative_cost', 0)
                        except:
                            continue
        except Exception as e:
            print(f"Warning: Could not load existing costs: {e}")
    
    def log_api_call(self, service: str, endpoint: str, tokens: int = None, cost: float = None):
        """Log an API call and its cost"""
        if cost is None:
            # Estimate cost based on service and tokens
            if service == "gemini":
                cost = COST_CONFIG["gemini"]["generation"]["average_call"]
        
        self.current_costs["total"] += cost
        self.current_costs["hourly"] += cost
        self.current_costs["api_calls"] += 1
        
        # Log to file
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime('%Y-%m-%d'),
            "service": service,
            "endpoint": endpoint,
            "tokens": tokens,
            "cost": cost,
            "cumulative_cost": self.current_costs["total"],
            "hourly_cost": self.current_costs["hourly"]
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Check thresholds
        self.check_thresholds()
    
    def check_thresholds(self):
        """Check if cost thresholds are exceeded"""
        daily_limit = COST_CONFIG["daily_limit"]
        hourly_limit = COST_CONFIG["hourly_limit"]
        
        # Check daily limit
        daily_percentage = (self.current_costs["total"] / daily_limit) * 100
        
        if daily_percentage >= 50 and "50_daily" not in self.alerts_sent:
            self.send_alert("WARNING", f"50% of daily budget used: ${self.current_costs['total']:.2f} / ${daily_limit:.2f}")
            self.alerts_sent.add("50_daily")
        
        if daily_percentage >= 80 and "80_daily" not in self.alerts_sent:
            self.send_alert("CRITICAL", f"80% of daily budget used: ${self.current_costs['total']:.2f} / ${daily_limit:.2f}")
            self.alerts_sent.add("80_daily")
            self.trigger_ai_shutdown()
        
        if daily_percentage >= 100:
            self.send_alert("EMERGENCY", f"DAILY BUDGET EXCEEDED: ${self.current_costs['total']:.2f}")
            self.emergency_shutdown()
        
        # Check hourly limit
        if self.current_costs["hourly"] >= hourly_limit:
            self.send_alert("WARNING", f"Hourly limit reached: ${self.current_costs['hourly']:.2f}")
            self.current_costs["hourly"] = 0  # Reset hourly counter
    
    def send_alert(self, level: str, message: str):
        """Send alert through configured channels"""
        alert_message = f"[{level}] {message}"
        
        # Console output with color
        color = {
            "WARNING": "\033[93m",
            "CRITICAL": "\033[91m",
            "EMERGENCY": "\033[95m"
        }.get(level, "\033[0m")
        
        print(f"\n{color}{'='*60}")
        print(f"{alert_message}")
        print(f"{'='*60}\033[0m\n")
        
        # Email alert (if configured)
        email = os.getenv("ALERT_EMAIL")
        if email:
            self.send_email_alert(email, level, message)
        
        # Slack alert (if configured)
        slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        if slack_webhook:
            self.send_slack_alert(slack_webhook, level, message)
    
    def send_email_alert(self, email: str, level: str, message: str):
        """Send email alert (placeholder - implement with your email service)"""
        print(f"📧 Email alert would be sent to {email}: {message}")
    
    def send_slack_alert(self, webhook_url: str, level: str, message: str):
        """Send Slack alert"""
        try:
            payload = {
                "text": f"*MealMateAI Cost Alert*",
                "attachments": [{
                    "color": {"WARNING": "warning", "CRITICAL": "danger", "EMERGENCY": "#FF00FF"}.get(level),
                    "title": level,
                    "text": message,
                    "footer": "Cost Monitor",
                    "ts": int(time.time())
                }]
            }
            requests.post(webhook_url, json=payload)
        except:
            pass  # Fail silently
    
    def trigger_ai_shutdown(self):
        """Disable AI endpoints to prevent further costs"""
        if self.shutdown_triggered:
            return
        
        self.shutdown_triggered = True
        print("\n🛑 TRIGGERING AI SERVICE SHUTDOWN")
        
        # Call API gateway to disable AI endpoints
        try:
            response = requests.post(
                "http://localhost:3000/admin/disable-ai",
                headers={"Authorization": f"Bearer {os.getenv('ADMIN_TOKEN', '')}"}
            )
            if response.status_code == 200:
                print("✅ AI services disabled successfully")
            else:
                print("❌ Failed to disable AI services - manual intervention required!")
        except Exception as e:
            print(f"❌ Error disabling AI services: {e}")
    
    def emergency_shutdown(self):
        """Emergency shutdown of all tests"""
        print("\n🚨🚨🚨 EMERGENCY SHUTDOWN 🚨🚨🚨")
        print("Killing all test processes...")
        
        # Kill Locust processes
        os.system("pkill -f locust")
        
        # Stop Docker services
        os.system("docker-compose stop meal-planner-service recipe-service")
        
        print("Emergency shutdown complete")
        sys.exit(1)
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                self.display_status()
                time.sleep(5)  # Update every 5 seconds
        
        # Reset hourly counter every hour
        def hourly_reset():
            while self.monitoring:
                time.sleep(3600)  # Wait 1 hour
                self.current_costs["hourly"] = 0
        
        # Start monitoring threads
        threading.Thread(target=monitor_loop, daemon=True).start()
        threading.Thread(target=hourly_reset, daemon=True).start()
    
    def display_status(self):
        """Display current cost status"""
        runtime = datetime.now() - self.current_costs["start_time"]
        runtime_minutes = runtime.total_seconds() / 60
        
        # Calculate rates
        rate_per_minute = self.current_costs["total"] / max(runtime_minutes, 1)
        projected_hourly = rate_per_minute * 60
        projected_daily = projected_hourly * 24
        
        # Calculate remaining budget
        daily_remaining = COST_CONFIG["daily_limit"] - self.current_costs["total"]
        time_until_limit = daily_remaining / max(rate_per_minute, 0.001)  # Minutes
        
        # Clear screen and display
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║              MealMateAI Cost Monitor v1.0                    ║
╠══════════════════════════════════════════════════════════════╣
║  Current Status: {"🟢 ACTIVE" if not self.shutdown_triggered else "🔴 SHUTDOWN"}
║  Runtime: {runtime_minutes:.1f} minutes
║  
║  💰 Current Costs:
║  ├─ Total Today: ${self.current_costs['total']:.2f}
║  ├─ This Hour: ${self.current_costs['hourly']:.2f}
║  └─ API Calls: {self.current_costs['api_calls']}
║  
║  📊 Rates:
║  ├─ Per Minute: ${rate_per_minute:.3f}
║  ├─ Projected Hourly: ${projected_hourly:.2f}
║  └─ Projected Daily: ${projected_daily:.2f} {"⚠️" if projected_daily > COST_CONFIG['daily_limit'] else ""}
║  
║  🎯 Budget:
║  ├─ Daily Limit: ${COST_CONFIG['daily_limit']:.2f}
║  ├─ Remaining: ${daily_remaining:.2f}
║  └─ Time to Limit: {time_until_limit:.0f} minutes
║  
║  Press Ctrl+C to stop monitoring
╚══════════════════════════════════════════════════════════════╝
        """)
    
    def generate_report(self):
        """Generate cost report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_cost": self.current_costs["total"],
            "api_calls": self.current_costs["api_calls"],
            "runtime_minutes": (datetime.now() - self.current_costs["start_time"]).total_seconds() / 60,
            "daily_limit": COST_CONFIG["daily_limit"],
            "budget_used_percentage": (self.current_costs["total"] / COST_CONFIG["daily_limit"]) * 100
        }
        
        # Save report
        report_file = f"cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(f"results/{report_file}", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Report saved to results/{report_file}")
        return report


def main():
    parser = argparse.ArgumentParser(description="Monitor API costs during performance testing")
    parser.add_argument("--watch", action="store_true", help="Start real-time monitoring")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--emergency-report", action="store_true", help="Generate emergency report")
    parser.add_argument("--alert", action="store_true", help="Send test alert")
    parser.add_argument("--reset", action="store_true", help="Reset daily costs (use with caution)")
    
    args = parser.parse_args()
    
    monitor = CostMonitor()
    
    if args.watch:
        print("Starting real-time cost monitoring...")
        print("Press Ctrl+C to stop")
        
        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            print("\n\nStopping monitor...")
            monitor.monitoring = False
            report = monitor.generate_report()
            print(f"\nFinal cost: ${report['total_cost']:.2f}")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        monitor.start_monitoring()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
    
    elif args.status:
        monitor.display_status()
    
    elif args.emergency_report:
        report = monitor.generate_report()
        print(json.dumps(report, indent=2))
    
    elif args.alert:
        monitor.send_alert("WARNING", "This is a test alert")
    
    elif args.reset:
        confirm = input("⚠️ Are you sure you want to reset daily costs? (yes/no): ")
        if confirm.lower() == "yes":
            os.remove(monitor.log_file)
            print("✅ Daily costs reset")
        else:
            print("❌ Reset cancelled")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()