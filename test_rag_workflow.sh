#!/bin/bash

# Test RAG Workflow for MealMateAI
echo "🧪 Testing RAG Workflow for MealMateAI"
echo "======================================="

# Configuration  
BASE_URL="http://localhost:8002"
USER_ID=1

echo ""
echo "📝 Step 1-3: Generate initial meal plan"
echo "----------------------------------------"

# Step 1-3: Generate initial meal plan
curl -X POST "$BASE_URL/rag/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "I want a healthy 7-day meal plan with Mediterranean cuisine, no seafood, and include vegetarian options",
    "user_id": '$USER_ID'
  }' | jq '.'

echo ""
echo ""
echo "📝 Step 4: Modify meal plan (replace with your conversation_id from above)"
echo "--------------------------------------------------------------------------"

# Step 4: Modify meal plan (you'll need to replace CONVERSATION_ID with actual ID from previous response)
echo "# Example modification request:"
echo "curl -X POST \"$BASE_URL/rag/modify\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"conversation_id\": \"YOUR_CONVERSATION_ID_HERE\","
echo "    \"user_feedback\": \"Replace breakfast on day 1 and 2 with something with eggs\","
echo "    \"user_id\": $USER_ID"
echo "  }' | jq '.'"

echo ""
echo ""
echo "📝 Step 5: Finalize meal plan"
echo "------------------------------"

echo "# Example finalization request:"
echo "curl -X POST \"$BASE_URL/rag/finalize\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"conversation_id\": \"YOUR_CONVERSATION_ID_HERE\","
echo "    \"user_id\": $USER_ID"
echo "  }' | jq '.'"

echo ""
echo ""
echo "🔍 Additional test endpoints:"
echo "-----------------------------"
echo "# Check if services are running:"
echo "curl http://localhost:8002/health"
echo ""
echo "# Get user's meal plans:"
echo "curl \"$BASE_URL/user/$USER_ID\" | jq '.'"
echo ""
echo "# Test recipe search directly:"
echo "curl \"http://localhost:8001/api/recipes/search?query=mediterranean&limit=5\" | jq '.'"