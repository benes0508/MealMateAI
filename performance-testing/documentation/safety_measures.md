# Safety Measures for MealMateAI Performance Testing

## ⚠️ Critical Warning

Performance testing AI-powered features can result in **significant unexpected costs**. This document outlines mandatory safety measures to protect against budget overruns.

---

## Cost Risk Assessment

### Service Cost Matrix

| Service | Cost per Call | Risk Level | Daily Budget |
|---------|--------------|------------|--------------|
| Gemini API (Generation) | $0.001-0.01 | ⚠️ HIGH | $50 |
| Gemini API (Embeddings) | $0.0001 | MEDIUM | $10 |
| Qdrant Vector Search | Compute only | LOW | N/A |
| PostgreSQL Queries | Compute only | LOW | N/A |
| User Auth | Compute only | LOW | N/A |

### Potential Cost Scenarios

#### Worst Case (No Protection)
- 100 users × 10 meal plans × $0.01 = **$10/minute**
- Potential daily cost: **$14,400** 😱

#### With Protection
- Rate limited to 5 req/min
- Maximum daily cost: **$50**
- Auto-shutdown at 80% budget

---

## Mandatory Safety Protocols

### 1. Environment Configuration

```bash
# Required environment variables
export PERFORMANCE_TEST_MODE=true
export GEMINI_API_DAILY_LIMIT=50  # dollars
export GEMINI_API_HOURLY_LIMIT=5   # dollars
export ALERT_EMAIL=team@example.com
export ALERT_PHONE=+1234567890
export AUTO_SHUTDOWN_THRESHOLD=0.8  # 80% of budget
export MOCK_AI_RESPONSES=false      # Set true for cost-free testing
```

### 2. Rate Limiting Configuration

```python
# In API Gateway settings
RATE_LIMITS = {
    "ai_endpoints": {
        "per_minute": 5,      # During testing
        "per_hour": 100,      # During testing
        "per_day": 500,       # During testing
        "burst": 10           # Maximum burst
    },
    "normal_endpoints": {
        "per_minute": 100,
        "per_hour": 5000,
        "per_day": 50000
    }
}
```

### 3. Circuit Breaker Pattern

```python
# Auto-disable AI features on threshold
class AICircuitBreaker:
    def __init__(self):
        self.daily_spend = 0
        self.hourly_spend = 0
        self.is_open = False
        
    def check_before_call(self):
        if self.daily_spend >= DAILY_LIMIT * 0.8:
            self.is_open = True
            self.send_alert("AI services disabled - 80% budget reached")
            return False
        return True
```

---

## Pre-Test Checklist

### ✅ Required Steps Before ANY Test

- [ ] Set `PERFORMANCE_TEST_MODE=true`
- [ ] Configure daily budget limit
- [ ] Start cost monitor script
- [ ] Verify rate limits active
- [ ] Check alert contacts
- [ ] Backup production data
- [ ] Use test user accounts
- [ ] Clear previous test data
- [ ] Review emergency shutdown procedure
- [ ] Confirm team availability

---

## Cost Monitoring Tools

### Real-Time Monitor Script

```bash
# Start monitor before tests
python scripts/cost_monitor.py --watch --alert-threshold=40

# Monitor shows:
# - Current spend: $12.34
# - Daily limit: $50.00
# - Rate: $0.45/min
# - Projected daily: $648.00 ⚠️
# - Auto-shutdown in: 82 minutes
```

### Dashboard Metrics

```python
# Key metrics to track
- api_calls_per_minute
- tokens_consumed_per_request
- cost_per_request
- cumulative_daily_cost
- remaining_budget
- projected_daily_total
- circuit_breaker_status
```

---

## Testing Strategies by Risk Level

### 🟢 Safe Testing (No AI Costs)

```python
# Use mock responses
export MOCK_AI_RESPONSES=true

# Test endpoints
- /api/auth/*
- /api/recipes (GET)
- /api/users/*
- Cached meal plans
- Cached grocery lists
```

### 🟡 Moderate Risk Testing

```python
# Limited AI with strict controls
export GEMINI_API_TEST_LIMIT=10  # Max 10 calls total

# Test carefully
- Single recipe recommendation
- One meal plan generation
- Vector search only
```

### 🔴 High Risk Testing

```python
# ONLY with approval and monitoring
export REQUIRES_APPROVAL=true
export MONITOR_MODE=paranoid

# Maximum safety
- 2 concurrent users MAX
- 5 minute test MAX
- Real-time cost display
- Auto-abort on spike
```

---

## Emergency Procedures

### Cost Spike Detected

```bash
#!/bin/bash
# EMERGENCY SHUTDOWN SCRIPT

# 1. Kill all test processes
pkill -9 -f locust
pkill -9 -f "python.*test"

# 2. Disable AI endpoints
curl -X POST http://localhost:3000/admin/disable-ai \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 3. Clear request queues
redis-cli FLUSHALL

# 4. Generate report
python scripts/cost_monitor.py --emergency-report

# 5. Send alerts
python scripts/send_alerts.py --critical \
  --message "AI costs exceeded threshold - services disabled"
```

### Recovery Steps

1. **Immediate** (< 5 minutes)
   - Stop all tests
   - Disable AI features
   - Clear queues
   
2. **Short-term** (< 1 hour)
   - Analyze cost spike
   - Review logs
   - Calculate total damage
   
3. **Long-term** (< 24 hours)
   - Implement additional safeguards
   - Update rate limits
   - Retrain team

---

## Mock Testing Configuration

### Enable Mock Responses

```python
# In test environment
if os.getenv('MOCK_AI_RESPONSES') == 'true':
    # Return canned responses
    return {
        "meal_plan": load_mock_meal_plan(),
        "cost": 0,
        "mock": True
    }
```

### Mock Data Files

```
/performance-testing/mocks/
├── meal_plan_response.json
├── recipe_recommendations.json
├── grocery_list.json
└── gemini_responses.json
```

---

## Rate Limiting Implementation

### API Gateway Level

```javascript
// Strict limits during testing
const testRateLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 5, // 5 requests per minute for AI
  message: 'Rate limit exceeded - protecting against cost overrun',
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    logger.warn(`Rate limit hit: ${req.ip}`);
    alerting.send('Rate limit triggered during test');
    res.status(429).json({
      error: 'Rate limit exceeded',
      retryAfter: 60
    });
  }
});
```

### Service Level

```python
# In Gemini service
class GeminiRateLimiter:
    def __init__(self):
        self.window = []
        self.max_per_minute = 5
        
    def allow_request(self):
        now = time.time()
        # Remove old entries
        self.window = [t for t in self.window if now - t < 60]
        
        if len(self.window) >= self.max_per_minute:
            return False
            
        self.window.append(now)
        return True
```

---

## Budget Alerts

### Alert Thresholds

| Threshold | Action | Notification |
|-----------|--------|--------------|
| 50% | Warning | Email |
| 70% | Reduce rate limit | Email + Slack |
| 80% | Disable non-critical AI | Email + SMS |
| 90% | Full shutdown | All channels + Phone |
| 100% | Emergency stop | Executive escalation |

### Alert Configuration

```python
ALERT_CONFIG = {
    "channels": {
        "email": ["dev-team@example.com"],
        "sms": ["+1234567890"],
        "slack": "#alerts-critical",
        "pagerduty": "service-key-here"
    },
    "thresholds": {
        0.5: ["email"],
        0.7: ["email", "slack"],
        0.8: ["email", "slack", "sms"],
        0.9: ["all"],
        1.0: ["all", "executive"]
    }
}
```

---

## Test Data Isolation

### Dedicated Test Accounts

```sql
-- Create test users with limited permissions
INSERT INTO users (email, password, is_test_account, rate_limit_override)
VALUES 
  ('perf-test-1@test.local', 'hashed', true, 5),
  ('perf-test-2@test.local', 'hashed', true, 5);

-- Limit test account capabilities
ALTER TABLE users ADD CONSTRAINT check_test_limits
  CHECK (is_test_account = false OR daily_ai_calls <= 10);
```

### Cleanup Procedures

```bash
#!/bin/bash
# Clean test data after runs

# Remove test meal plans
psql -c "DELETE FROM meal_plans WHERE user_id IN (SELECT id FROM users WHERE is_test_account = true);"

# Clear test cache
redis-cli --scan --pattern "test:*" | xargs redis-cli DEL

# Archive logs
tar -czf "test-logs-$(date +%Y%m%d).tar.gz" logs/test-*
rm logs/test-*
```

---

## Compliance and Audit

### Required Documentation

- [ ] Pre-test budget approval
- [ ] Test configuration snapshot
- [ ] Cost monitoring logs
- [ ] Alert response times
- [ ] Post-test cost report
- [ ] Lessons learned document

### Audit Trail

```python
# Log all AI calls during tests
def log_ai_call(endpoint, cost, response_time):
    audit_log.write({
        "timestamp": datetime.now(),
        "test_id": current_test_id,
        "endpoint": endpoint,
        "cost": cost,
        "response_time": response_time,
        "user": test_user_id,
        "budget_remaining": get_remaining_budget()
    })
```

---

## Best Practices

### DO ✅
- Start with mock responses
- Test in isolated environment
- Monitor costs in real-time
- Use dedicated test accounts
- Set conservative limits
- Have shutdown plan ready
- Document everything
- Review costs immediately

### DON'T ❌
- Test in production
- Skip pre-test checklist
- Ignore cost alerts
- Test without monitoring
- Use real user data
- Exceed approved budget
- Test alone (buddy system)
- Forget cleanup

---

## Tool Commands

### Monitor Commands
```bash
# Start monitor
./scripts/start_monitor.sh

# Check status
curl http://localhost:9999/cost-status

# Emergency stop
./scripts/emergency_stop.sh

# Generate report
python scripts/cost_report.py --date=today
```

### Safety Scripts
```bash
# Pre-test validation
./scripts/pre_test_check.sh

# Post-test cleanup
./scripts/post_test_cleanup.sh

# Cost projection
python scripts/project_costs.py --users=100 --duration=1h
```

---

## Contact Information

### Escalation Path

1. **Level 1**: Dev Team Lead
   - Email: lead@example.com
   - Slack: @teamlead

2. **Level 2**: Engineering Manager
   - Email: manager@example.com
   - Phone: +1-234-567-8901

3. **Level 3**: CTO
   - Email: cto@example.com
   - Phone: +1-234-567-8902

### External Support
- Google Cloud Support: [Support URL]
- Gemini API Issues: [API Support]

---

**Remember**: It's better to be overly cautious than to receive a surprise cloud bill! 💸

**Golden Rule**: If in doubt, DON'T run the test. Ask for review first.