# MealMateAI Stress Test Plan

## Executive Summary

This document outlines a comprehensive stress testing strategy for MealMateAI, focusing on identifying system limits, bottlenecks, and cost implications of AI-powered features.

---

## Test Objectives

### Primary Goals
1. **Determine system capacity** under various load conditions
2. **Identify performance bottlenecks** in the RAG pipeline
3. **Measure AI service costs** at different scales
4. **Validate rate limiting** and protection mechanisms
5. **Assess database and vector search** performance
6. **Ensure graceful degradation** under stress

### Success Criteria
- All endpoints respond within SLA targets
- System handles target concurrent users
- AI costs remain within budget
- No data corruption under load
- Proper error handling at limits

---

## System Architecture Considerations

### Service Dependencies
```
Frontend (React) → API Gateway (Express) → Microservices
                                         ├── User Service (MySQL)
                                         ├── Recipe Service (PostgreSQL + Qdrant)
                                         ├── Meal Planner (PostgreSQL + Gemini)
                                         └── Notification Service
```

### Critical Paths
1. **Authentication Flow**: User Service + JWT validation
2. **Recipe Search**: Qdrant vector DB + Gemini query generation
3. **Meal Planning**: RAG pipeline + Gemini generation
4. **Grocery List**: Cached vs. generated paths

---

## Test Scenarios

### Phase 1: Baseline Testing (Week 1)

#### Test 1.1: Authentication Performance
- **Load**: 10, 50, 100 concurrent users
- **Duration**: 10 minutes
- **Endpoints**: `/api/auth/login`, `/api/auth/register`
- **Metrics**: Response time, JWT generation time, database connections
- **Risk**: LOW - No AI costs

#### Test 1.2: Recipe Browsing
- **Load**: 20, 100, 200 concurrent users
- **Duration**: 15 minutes
- **Endpoints**: `/api/recipes`, `/api/recipes/search`
- **Metrics**: Query performance, cache hit rates
- **Risk**: LOW - Database only

#### Test 1.3: User Preferences
- **Load**: 50 concurrent users
- **Duration**: 10 minutes
- **Operations**: CRUD on preferences
- **Metrics**: Write performance, consistency
- **Risk**: LOW

### Phase 2: Vector Search Testing (Week 2)

#### Test 2.1: Qdrant Performance
- **Load**: 10, 30, 50 concurrent searches
- **Duration**: 20 minutes
- **Queries**: Various semantic searches
- **Metrics**: Search latency, relevance scores
- **Risk**: MEDIUM - Vector DB compute

#### Test 2.2: Collection-Specific Search
- **Load**: 20 users per collection
- **Duration**: 15 minutes
- **Collections**: All 8 recipe collections
- **Metrics**: Per-collection performance
- **Risk**: MEDIUM

### Phase 3: AI Integration Testing (Week 3)

⚠️ **HIGH COST WARNING**: These tests will incur Gemini API charges

#### Test 3.1: Recipe Recommendations (LIMITED)
- **Load**: 2, 5, 10 concurrent users MAX
- **Duration**: 5 minutes MAX
- **Endpoint**: `/api/recipes/recommendations`
- **Metrics**: Gemini response time, token usage, costs
- **Risk**: HIGH - Direct AI calls
- **Budget Cap**: $10 per test run

#### Test 3.2: Meal Plan Generation (LIMITED)
- **Load**: 1, 2, 5 concurrent users MAX
- **Duration**: 5 minutes MAX
- **Endpoint**: `/api/meal-plans/rag/generate`
- **Metrics**: End-to-end latency, AI costs, success rate
- **Risk**: HIGH - Multiple AI calls
- **Budget Cap**: $20 per test run

#### Test 3.3: Grocery List Generation
- **Load**: 5, 10 concurrent users
- **Duration**: 10 minutes
- **Mix**: 70% cached, 30% generated
- **Metrics**: Cache performance, generation costs
- **Risk**: MEDIUM-HIGH

### Phase 4: Stress Testing (Week 4)

#### Test 4.1: Spike Testing
- **Pattern**: 10 → 100 → 10 users over 30 minutes
- **Endpoints**: All non-AI endpoints
- **Metrics**: Recovery time, error rates
- **Risk**: MEDIUM

#### Test 4.2: Endurance Testing
- **Load**: 50 constant users
- **Duration**: 2 hours
- **Endpoints**: Mixed realistic traffic
- **Metrics**: Memory leaks, connection pools
- **Risk**: MEDIUM

#### Test 4.3: Breaking Point (CAREFULLY)
- **Load**: Gradually increase to failure
- **Duration**: Until system fails
- **Endpoints**: Non-AI only
- **Metrics**: Maximum capacity, failure mode
- **Risk**: MEDIUM - Potential downtime

---

## Load Patterns

### User Journey Simulation
```python
1. Register/Login (5%)
2. Browse recipes (30%)
3. Search recipes (20%)
4. View recipe details (15%)
5. Generate meal plan (10%) - AI COST!
6. View meal plan (10%)
7. Get grocery list (5%)
8. Update preferences (5%)
```

### Traffic Distribution
- **Peak Hours**: 11am-1pm, 5pm-8pm
- **Off-Peak**: 2am-6am
- **Weekend Surge**: 2x normal traffic

---

## Performance Targets

### Response Time SLAs

| Endpoint Category | P50 | P95 | P99 | Max |
|------------------|-----|-----|-----|-----|
| Static Content | 50ms | 100ms | 200ms | 500ms |
| Authentication | 100ms | 300ms | 500ms | 1s |
| Database Queries | 100ms | 500ms | 1s | 2s |
| Vector Search | 200ms | 800ms | 1.5s | 3s |
| AI Generation | 2s | 5s | 10s | 30s |

### Throughput Targets
- **Authentication**: 100 req/s
- **Recipe Browse**: 500 req/s
- **Vector Search**: 50 req/s
- **AI Generation**: 5 req/s (rate limited)

### Error Rate Tolerances
- **Critical (Auth)**: < 0.1%
- **Important (CRUD)**: < 1%
- **AI Services**: < 5%

---

## Resource Monitoring

### Application Metrics
- Request rate and latency
- Error rates by endpoint
- Active connections
- Queue depths

### Infrastructure Metrics
- CPU utilization (target < 70%)
- Memory usage (target < 80%)
- Disk I/O
- Network bandwidth

### Database Metrics
- Connection pool usage
- Query execution time
- Lock contention
- Replication lag

### AI Service Metrics
- API call rate
- Token consumption
- Cost per request
- Rate limit hits

---

## Risk Mitigation

### Cost Controls
1. **Hard Limits**: Daily API budget caps
2. **Rate Limiting**: Per-user and global limits
3. **Circuit Breakers**: Auto-disable AI on budget exceed
4. **Monitoring**: Real-time cost tracking
5. **Alerts**: Email/SMS on threshold breach

### Testing Safeguards
1. Start with minimal load
2. Monitor continuously
3. Gradual load increase
4. Kill switches ready
5. Rollback procedures

### Data Protection
1. Use test data only
2. Backup before testing
3. Separate test environment
4. Data validation post-test

---

## Test Execution Schedule

### Week 1: Preparation
- Day 1-2: Environment setup
- Day 3-4: Baseline tests
- Day 5: Analysis and tuning

### Week 2: Core Testing
- Day 1-2: Vector search tests
- Day 3-4: Mixed load tests
- Day 5: Performance optimization

### Week 3: AI Testing (LIMITED)
- Day 1: Single-user AI tests
- Day 2: Small concurrent AI tests
- Day 3-5: Analysis and cost review

### Week 4: Stress Tests
- Day 1-2: Spike and endurance
- Day 3: Breaking point test
- Day 4-5: Final report

---

## Reporting

### Test Reports Include
1. Executive summary
2. Test configuration
3. Performance metrics
4. Cost analysis
5. Bottleneck identification
6. Recommendations
7. Raw data appendix

### Key Deliverables
- Performance baseline document
- Capacity planning guide
- Cost projection model
- Optimization recommendations
- Emergency runbooks

---

## Tools and Scripts

### Required Tools
- **Locust**: Load generation
- **Grafana**: Real-time monitoring
- **Python**: Cost monitoring scripts
- **Docker**: Service orchestration
- **PostgreSQL tools**: Query analysis

### Monitoring Stack
```bash
# Start monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Access dashboards
# Grafana: http://localhost:3001
# Prometheus: http://localhost:9090
```

---

## Success Metrics

### Performance Goals
✅ All endpoints meet SLA targets
✅ System handles 100 concurrent users
✅ Vector search < 1s P95
✅ AI generation < 5s P95

### Cost Goals
✅ Daily AI costs < $50
✅ Per-user cost < $0.10
✅ Cached hit rate > 70%

### Reliability Goals
✅ 99.9% uptime for core features
✅ Graceful degradation of AI features
✅ Auto-recovery from failures

---

## Post-Test Actions

1. **Immediate**
   - Stop all load generators
   - Check system health
   - Calculate total costs
   - Backup test results

2. **Within 24 Hours**
   - Clean test data
   - Analyze results
   - Document issues
   - Plan optimizations

3. **Within 1 Week**
   - Implement fixes
   - Retest problem areas
   - Update documentation
   - Share findings

---

## Appendix

### Emergency Contacts
- DevOps Lead: [Contact]
- Database Admin: [Contact]
- API Budget Owner: [Contact]

### Useful Commands
```bash
# Monitor costs
watch -n 5 'python scripts/cost_monitor.py --status'

# System resources
docker stats

# Database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Kill all tests
pkill -f locust
```

### References
- [Locust Documentation](https://docs.locust.io/)
- [Gemini API Pricing](https://ai.google.dev/pricing)
- [Performance Testing Best Practices](https://example.com)

---

**Remember**: Safety first! Monitor costs continuously and be ready to abort tests if needed.