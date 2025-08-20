#!/usr/bin/env python3
"""
Test and Validate Batch Summary Generation
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from collections import defaultdict
import time

def validate_summary_format(summary_text):
    """Validate that a summary meets expected criteria"""
    issues = []
    
    if not summary_text:
        issues.append("Empty summary")
        return issues
    
    summary = summary_text.strip()
    
    # Basic length checks
    if len(summary) < 20:
        issues.append(f"Too short ({len(summary)} chars)")
    elif len(summary) > 1000:
        issues.append(f"Too long ({len(summary)} chars)")
    
    # Content checks
    if summary.lower().startswith("recipe"):
        issues.append("Summary starts with 'Recipe' (should be clean)")
    
    if "1." in summary or "2." in summary:
        issues.append("Contains numbered list format (should be parsed)")
    
    # Check for reasonable content
    food_keywords = ['recipe', 'dish', 'ingredient', 'cook', 'bake', 'fry', 'serve', 'flavor', 'season', 'prepare', 'chicken', 'beef', 'vegetable', 'sauce', 'spice']
    has_food_content = any(keyword in summary.lower() for keyword in food_keywords)
    
    if not has_food_content:
        issues.append("No food-related content detected")
    
    return issues

def run_test_generation():
    """Run the test summary generation"""
    print("🚀 Running test summary generation...")
    
    try:
        result = subprocess.run([
            "python3.9", "test_summary_generator.py"
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        print("📄 GENERATION OUTPUT:")
        print("=" * 40)
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  ERRORS:")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"❌ Generation failed with return code {result.returncode}")
            return False
        
        print("✅ Generation completed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Generation timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running generation: {e}")
        return False

def validate_results():
    """Validate the generated summaries"""
    print("\n🔍 Validating generated summaries...")
    
    # Load test recipes to know what we expect
    with open("test_classified_recipes.json", 'r', encoding='utf-8') as f:
        test_recipes = json.load(f)
    
    summary_dir = Path("test_recipe_summaries")
    if not summary_dir.exists():
        print("❌ Summary directory not found")
        return False
    
    # Group expected recipes by collection
    expected_by_collection = defaultdict(list)
    for recipe_id, recipe_data in test_recipes.items():
        collection = recipe_data.get('collection')
        if collection != 'beverages':  # Skip beverages as they're excluded
            expected_by_collection[collection].append(recipe_id)
    
    validation_results = {
        'total_expected': 0,
        'total_generated': 0,
        'total_valid': 0,
        'collections': {},
        'issues': []
    }
    
    for collection, expected_recipe_ids in expected_by_collection.items():
        print(f"\n📁 Validating collection: {collection}")
        
        col_dir = summary_dir / collection
        collection_results = {
            'expected': len(expected_recipe_ids),
            'generated': 0,
            'valid': 0,
            'issues': []
        }
        
        if not col_dir.exists():
            collection_results['issues'].append("Collection directory missing")
            validation_results['collections'][collection] = collection_results
            continue
        
        # Check each expected recipe
        for recipe_id in expected_recipe_ids:
            summary_file = col_dir / f"{recipe_id}.txt"
            validation_results['total_expected'] += 1
            
            if not summary_file.exists():
                collection_results['issues'].append(f"Missing summary for recipe {recipe_id}")
                continue
            
            # Read and validate summary
            try:
                summary_text = summary_file.read_text(encoding='utf-8')
                collection_results['generated'] += 1
                validation_results['total_generated'] += 1
                
                # Validate format
                issues = validate_summary_format(summary_text)
                
                if not issues:
                    collection_results['valid'] += 1
                    validation_results['total_valid'] += 1
                    print(f"   ✅ Recipe {recipe_id}: Valid summary ({len(summary_text)} chars)")
                else:
                    print(f"   ⚠️  Recipe {recipe_id}: Issues - {', '.join(issues)}")
                    collection_results['issues'].extend([f"Recipe {recipe_id}: {issue}" for issue in issues])
                
            except Exception as e:
                collection_results['issues'].append(f"Error reading recipe {recipe_id}: {e}")
                print(f"   ❌ Recipe {recipe_id}: Error reading file")
        
        validation_results['collections'][collection] = collection_results
        print(f"   📊 {collection}: {collection_results['valid']}/{collection_results['expected']} valid summaries")
    
    return validation_results

def print_validation_report(results):
    """Print a detailed validation report"""
    print("\n📊 VALIDATION REPORT")
    print("=" * 60)
    
    print(f"📈 Overall Results:")
    print(f"   Expected summaries: {results['total_expected']}")
    print(f"   Generated summaries: {results['total_generated']}")
    print(f"   Valid summaries: {results['total_valid']}")
    print(f"   Success rate: {results['total_valid']}/{results['total_expected']} ({results['total_valid']/results['total_expected']*100:.1f}%)")
    
    print(f"\n📁 Collection Breakdown:")
    for collection, col_results in results['collections'].items():
        success_rate = col_results['valid'] / col_results['expected'] * 100 if col_results['expected'] > 0 else 0
        status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
        
        print(f"   {status} {collection}:")
        print(f"      Valid: {col_results['valid']}/{col_results['expected']} ({success_rate:.1f}%)")
        
        if col_results['issues']:
            print(f"      Issues: {len(col_results['issues'])}")
            for issue in col_results['issues'][:3]:  # Show first 3 issues
                print(f"        - {issue}")
            if len(col_results['issues']) > 3:
                print(f"        ... and {len(col_results['issues']) - 3} more")
    
    # Overall assessment
    overall_success = results['total_valid'] / results['total_expected'] * 100 if results['total_expected'] > 0 else 0
    
    print(f"\n🎯 ASSESSMENT:")
    if overall_success >= 80:
        print("✅ EXCELLENT: Batch processing is working correctly!")
    elif overall_success >= 60:
        print("⚠️  GOOD: Batch processing mostly working, minor issues to address")
    elif overall_success >= 40:
        print("⚠️  FAIR: Batch processing partially working, needs improvement")
    else:
        print("❌ POOR: Batch processing has significant issues")

def cleanup_test_files():
    """Clean up test files"""
    import shutil
    
    print("\n🧹 Cleaning up test files...")
    
    summary_dir = Path("test_recipe_summaries")
    if summary_dir.exists():
        shutil.rmtree(summary_dir)
        print("   ✅ Removed test summary directory")
    
    print("   ✅ Cleanup complete")

def main():
    """Main test execution"""
    print("🧪 BATCH SUMMARY GENERATION TEST SUITE")
    print("=" * 60)
    
    # Check if test data exists
    if not Path("test_classified_recipes.json").exists():
        print("❌ Test data not found. Run extract_test_recipes.py first.")
        return 1
    
    start_time = time.time()
    
    try:
        # Step 1: Run test generation
        print("📝 Step 1: Generate summaries for test dataset")
        if not run_test_generation():
            print("❌ Test generation failed")
            return 1
        
        # Step 2: Validate results
        print("\\n🔍 Step 2: Validate generated summaries")
        results = validate_results()
        
        if not results:
            print("❌ Validation failed")
            return 1
        
        # Step 3: Print report
        print_validation_report(results)
        
        # Ask if user wants to clean up
        print(f"\\n⏱️  Total test time: {time.time() - start_time:.1f} seconds")
        
        cleanup_choice = input("\\n🧹 Clean up test files? (y/n): ").lower().strip()
        if cleanup_choice == 'y':
            cleanup_test_files()
        
        # Return success/failure based on results
        success_rate = results['total_valid'] / results['total_expected'] * 100 if results['total_expected'] > 0 else 0
        return 0 if success_rate >= 60 else 1
        
    except KeyboardInterrupt:
        print("\\n❌ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\\n❌ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())