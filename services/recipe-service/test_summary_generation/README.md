# Batch Summary Generation Test Suite

This test suite validates that the Gemini batch summary generation is working correctly with proper formatting and expected outputs.

## Files

- `extract_test_recipes.py` - Creates a representative sample of 50 recipes from the full dataset
- `test_summary_generator.py` - Modified version of the summary generator for testing
- `test_and_validate.py` - Main test runner that generates summaries and validates results
- `test_classified_recipes.json` - Test dataset (generated)
- `test_recipe_summaries/` - Generated summaries (created during test)

## Quick Start

1. **Extract test recipes:**
   ```bash
   python3.9 extract_test_recipes.py
   ```

2. **Run the full test suite:**
   ```bash
   python3.9 test_and_validate.py
   ```

## What the test does

1. **Generates summaries** for 50 sample recipes using batch processing
2. **Validates format** of each generated summary:
   - Appropriate length (20-1000 characters)
   - No numbered list artifacts (like "1.", "2.")
   - Contains food-related content
   - Proper format (not starting with "Recipe")
3. **Reports success rate** by collection and overall
4. **Provides detailed feedback** on any issues found

## Expected Results

- **Success rate ≥ 80%**: Excellent - batch processing working correctly
- **Success rate ≥ 60%**: Good - mostly working with minor issues
- **Success rate ≥ 40%**: Fair - needs improvement
- **Success rate < 40%**: Poor - significant issues to fix

## Test Configuration

- Batch sizes: 5 recipes per batch (small for testing)
- Collections: All except beverages (as requested)
- Timeout: 5 minutes for generation
- Validation: Format and content checks

## Sample Output

```
🧪 BATCH SUMMARY GENERATION TEST SUITE
============================================================
📝 Step 1: Generate summaries for test dataset
🚀 Running test summary generation...
✅ Generation completed successfully

🔍 Step 2: Validate generated summaries
📁 Validating collection: desserts-sweets
   ✅ Recipe 12345: Valid summary (156 chars)
   ✅ Recipe 67890: Valid summary (203 chars)

📊 VALIDATION REPORT
============================================================
📈 Overall Results:
   Expected summaries: 44
   Generated summaries: 44
   Valid summaries: 42
   Success rate: 42/44 (95.5%)

🎯 ASSESSMENT:
✅ EXCELLENT: Batch processing is working correctly!
```

## Troubleshooting

- **API Key issues**: Ensure `GOOGLE_API_KEY` is set in environment
- **Timeout errors**: API might be slow, try running again
- **Format issues**: Check `parse_batch_response()` logic
- **Missing summaries**: Check Gemini API response parsing