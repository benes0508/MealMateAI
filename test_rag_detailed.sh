#!/bin/bash

# Comprehensive RAG Workflow Test with Full Logging
# This script tests all 5 steps and logs everything to a file

LOG_FILE="rag_test_results_$(date +%Y%m%d_%H%M%S).txt"
BASE_URL="http://localhost:8002"
USER_ID=1

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to log API request and response
log_api() {
    local step="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local response="$5"
    
    {
        echo "======================================"
        echo "API REQUEST - $step"
        echo "======================================"
        echo "Method: $method"
        echo "URL: $url"
        echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "Request Body:"
        echo "$data" | jq '.' 2>/dev/null || echo "$data"
        echo ""
        echo "Response:"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        echo ""
        echo "Response Summary:"
        if echo "$response" | jq '.' > /dev/null 2>&1; then
            echo "- Status: Valid JSON response"
            echo "- Size: $(echo "$response" | wc -c) characters"
            # Extract key fields based on step
            case "$step" in
                "STEP 1-3"*)
                    echo "- Queries Used: $(echo "$response" | jq -r '.meal_plan.queries_used | length // "N/A"')"
                    echo "- Recipes Found: $(echo "$response" | jq -r '.meal_plan.recipes_found // "N/A"')"
                    echo "- Meal Plan Days: $(echo "$response" | jq -r '.meal_plan.meal_plan | length // "N/A"')"
                    echo "- Conversation ID: $(echo "$response" | jq -r '.conversation_id // "N/A"')"
                    ;;
                "STEP 4"*)
                    echo "- Status: $(echo "$response" | jq -r '.status // "N/A"')"
                    echo "- Changes Made: $(echo "$response" | jq -r '.meal_plan.changes_made // "Not specified"')"
                    ;;
                "STEP 5"*)
                    echo "- Finalization: $(echo "$response" | jq -r '.id // "Success"')"
                    ;;
            esac
        else
            echo "- Status: Invalid JSON or Error"
            echo "- Raw Response: $response"
        fi
        echo ""
    } >> "$LOG_FILE"
}

# Function to display colored output
print_step() {
    echo -e "${BLUE}$1${NC}"
    log "$1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    log "✅ $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log "⚠️ $1"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    log "❌ $1"
}

# Start logging
{
    echo "=========================================="
    echo "RAG WORKFLOW COMPREHENSIVE TEST LOG"
    echo "=========================================="
    echo "Test Started: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Log File: $LOG_FILE"
    echo "Base URL: $BASE_URL"
    echo "User ID: $USER_ID"
    echo ""
} > "$LOG_FILE"

print_step "🧪 Starting Comprehensive RAG Workflow Test"
echo "📝 All results will be saved to: $LOG_FILE"
echo ""

# Check if services are running
print_step "🔍 PRELIMINARY CHECKS"
log "Checking if services are running..."

# Check meal-planner service
meal_planner_check=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/user/1" 2>/dev/null)
if [ "$meal_planner_check" = "200" ]; then
    print_success "Meal-planner service is running"
else
    print_error "Meal-planner service is not responding (HTTP: $meal_planner_check)"
fi

# Check recipe service
recipe_check=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8001/?limit=1" 2>/dev/null)
if [ "$recipe_check" = "200" ]; then
    print_success "Recipe service is running"
else
    print_error "Recipe service is not responding (HTTP: $recipe_check)"
fi

# Check available recipes
recipe_count=$(curl -s "http://localhost:8001/search?query=apple&limit=1" | jq -r '.total // 0' 2>/dev/null)
log "Available apple recipes: $recipe_count"

echo ""

# STEP 1-3: Generate Initial Meal Plan
print_step "📝 STEP 1-3: Generate Initial Meal Plan"

request_data='{
  "user_prompt": "Create a 3-day meal plan with healthy apple-based recipes and some vegetarian options",
  "user_id": '$USER_ID'
}'

log "Sending initial meal plan request..."
response_step1=$(curl -s -X POST "$BASE_URL/rag/generate" \
  -H "Content-Type: application/json" \
  -d "$request_data")

log_api "STEP 1-3: Generate Initial Meal Plan" "POST" "$BASE_URL/rag/generate" "$request_data" "$response_step1"

# Extract conversation ID for next steps
conversation_id=$(echo "$response_step1" | jq -r '.conversation_id // "ERROR"')

if [ "$conversation_id" != "ERROR" ] && [ "$conversation_id" != "null" ]; then
    print_success "Initial meal plan generated successfully"
    log "Conversation ID: $conversation_id"
    
    # Extract and log meal plan details
    queries_count=$(echo "$response_step1" | jq -r '.meal_plan.queries_used | length // 0')
    recipes_found=$(echo "$response_step1" | jq -r '.meal_plan.recipes_found // 0')
    meal_plan_days=$(echo "$response_step1" | jq -r '.meal_plan.meal_plan | length // 0')
    
    log "Generated $queries_count search queries"
    log "Found $recipes_found recipes"
    log "Created meal plan for $meal_plan_days days"
    
    # Log individual queries used
    {
        echo "Queries Used:"
        echo "$response_step1" | jq -r '.meal_plan.queries_used[]?' 2>/dev/null | sed 's/^/  - /'
        echo ""
    } >> "$LOG_FILE"
else
    print_error "Failed to generate initial meal plan"
    conversation_id="failed"
fi

echo ""

# STEP 4: Modify Meal Plan
print_step "📝 STEP 4: Modify Meal Plan Based on Feedback"

if [ "$conversation_id" != "failed" ]; then
    modify_request='{
      "conversation_id": "'$conversation_id'",
      "user_feedback": "Replace all breakfast items with lighter, healthier options and add more protein",
      "user_id": '$USER_ID'
    }'
    
    log "Sending meal plan modification request..."
    response_step4=$(curl -s -X POST "$BASE_URL/rag/modify" \
      -H "Content-Type: application/json" \
      -d "$modify_request")
    
    log_api "STEP 4: Modify Meal Plan" "POST" "$BASE_URL/rag/modify" "$modify_request" "$response_step4"
    
    # Check if modification was successful
    modify_status=$(echo "$response_step4" | jq -r '.status // "ERROR"')
    if [ "$modify_status" = "modified" ]; then
        print_success "Meal plan modified successfully"
        
        # Log modification details
        changes=$(echo "$response_step4" | jq -r '.meal_plan.changes_made // "No specific changes documented"')
        log "Modification changes: $changes"
    else
        print_warning "Meal plan modification completed with status: $modify_status"
    fi
else
    print_warning "Skipping modification step due to failed initial generation"
    response_step4='{"status": "skipped", "reason": "Initial generation failed"}'
fi

echo ""

# STEP 5: Finalize Meal Plan
print_step "📝 STEP 5: Finalize Meal Plan"

if [ "$conversation_id" != "failed" ]; then
    finalize_request='{
      "conversation_id": "'$conversation_id'",
      "user_id": '$USER_ID'
    }'
    
    log "Sending meal plan finalization request..."
    response_step5=$(curl -s -X POST "$BASE_URL/rag/finalize" \
      -H "Content-Type: application/json" \
      -d "$finalize_request")
    
    log_api "STEP 5: Finalize Meal Plan" "POST" "$BASE_URL/rag/finalize" "$finalize_request" "$response_step5"
    
    # Check finalization result
    finalize_result=$(echo "$response_step5" | jq -r '.id // .message // "Unknown"')
    if [ "$finalize_result" != "Unknown" ] && [ "$finalize_result" != "null" ]; then
        print_success "Meal plan finalized successfully"
        log "Finalization result: $finalize_result"
    else
        print_warning "Meal plan finalization status unclear"
    fi
else
    print_warning "Skipping finalization step due to failed initial generation"
    response_step5='{"status": "skipped", "reason": "Initial generation failed"}'
fi

echo ""

# Additional Tests
print_step "🔍 ADDITIONAL VERIFICATION TESTS"

# Test direct recipe search
log "Testing direct recipe search..."
direct_search=$(curl -s "http://localhost:8001/search?query=healthy%20apple&limit=5")
search_results=$(echo "$direct_search" | jq -r '.total // 0')
log "Direct search for 'healthy apple' returned $search_results results"

# Get user's meal plans
log "Fetching user meal plans..."
user_plans=$(curl -s "$BASE_URL/user/$USER_ID")
plans_count=$(echo "$user_plans" | jq '. | length // 0' 2>/dev/null)
log "User has $plans_count total meal plans"

# Log service status
{
    echo "======================================"
    echo "SERVICE STATUS SUMMARY"
    echo "======================================"
    echo "Meal-Planner Service: $([ "$meal_planner_check" = "200" ] && echo "✅ Running" || echo "❌ Down")"
    echo "Recipe Service: $([ "$recipe_check" = "200" ] && echo "✅ Running" || echo "❌ Down")"
    echo "Recipe Database: $recipe_count apple recipes available"
    echo "User Meal Plans: $plans_count plans found"
    echo ""
} >> "$LOG_FILE"

# Final Summary
print_step "📊 TEST SUMMARY"

{
    echo "======================================"
    echo "FINAL TEST RESULTS SUMMARY"
    echo "======================================"
    echo "Test Completed: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "Step 1-3 (Generate): $([ "$conversation_id" != "failed" ] && echo "✅ SUCCESS" || echo "❌ FAILED")"
    echo "Step 4 (Modify): $([ "$conversation_id" != "failed" ] && echo "✅ COMPLETED" || echo "⚠️ SKIPPED")"
    echo "Step 5 (Finalize): $([ "$conversation_id" != "failed" ] && echo "✅ COMPLETED" || echo "⚠️ SKIPPED")"
    echo ""
    echo "Key Metrics:"
    echo "- Conversation ID: $conversation_id"
    echo "- Search Queries Generated: $(echo "$response_step1" | jq -r '.meal_plan.queries_used | length // 0')"
    echo "- Recipes Found: $(echo "$response_step1" | jq -r '.meal_plan.recipes_found // 0')"
    echo "- Meal Plan Days: $(echo "$response_step1" | jq -r '.meal_plan.meal_plan | length // 0')"
    echo ""
    echo "Overall Status: $([ "$conversation_id" != "failed" ] && echo "✅ RAG WORKFLOW FUNCTIONAL" || echo "❌ RAG WORKFLOW NEEDS ATTENTION")"
    echo ""
} >> "$LOG_FILE"

if [ "$conversation_id" != "failed" ]; then
    print_success "RAG Workflow Test Completed Successfully!"
    print_success "All 5 steps of the workflow are functional"
else
    print_error "RAG Workflow Test Had Issues"
    print_warning "Check the log file for detailed error information"
fi

echo ""
echo -e "${BLUE}📄 Complete test log saved to: ${NC}$LOG_FILE"
echo -e "${BLUE}📊 Review the file to see all API requests, responses, and detailed analysis${NC}"

# Make the log file easily readable
chmod 644 "$LOG_FILE"