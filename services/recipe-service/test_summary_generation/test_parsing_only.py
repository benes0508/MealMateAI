#!/usr/bin/env python3
"""
Test just the parsing logic without API calls
"""

import sys
import re
from pathlib import Path

def parse_batch_response(response_text, expected_count):
    """Parse numbered response into individual summaries"""
    summaries = []
    
    # Use regex to split by numbered items (1., 2., 3., etc.)
    # Find all numbered sections
    pattern = r'^(\d+)\.\s*(.*?)(?=^\d+\.|$)'
    matches = re.findall(pattern, response_text, re.MULTILINE | re.DOTALL)
    
    for number, content in matches:
        # Clean up the content
        cleaned_content = re.sub(r'\n+', ' ', content.strip())  # Replace multiple newlines with spaces
        cleaned_content = re.sub(r'\s+', ' ', cleaned_content)   # Replace multiple spaces with single space
        
        # Remove any markdown formatting like **bold**
        cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_content)
        
        if cleaned_content:
            summaries.append(cleaned_content)
    
    # If regex approach didn't work well, try manual parsing
    if len(summaries) != expected_count:
        print(f"🔧 Regex parsing got {len(summaries)} summaries, expected {expected_count}. Trying manual parsing...")
        summaries = manual_parse_response(response_text, expected_count)
    
    # Ensure we return exactly the expected number of summaries
    while len(summaries) < expected_count:
        summaries.append("")
    
    return summaries[:expected_count]

def manual_parse_response(response_text, expected_count):
    """Fallback manual parsing method"""
    summaries = []
    lines = response_text.strip().split('\n')
    current_summary = ""
    current_number = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this line starts with a number pattern like "1." or "1: "
        number_match = re.match(r'^(\d+)[\.\:\)]\s*(.*)', line)
        
        if number_match:
            number = int(number_match.group(1))
            content = number_match.group(2)
            
            # Save previous summary if we have one
            if current_summary and current_number > 0:
                # Clean up the summary
                cleaned = re.sub(r'\s+', ' ', current_summary.strip())
                cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)  # Remove markdown
                summaries.append(cleaned)
            
            # Start new summary
            current_number = number
            current_summary = content
        else:
            # Continue current summary
            if current_summary:
                current_summary += " " + line
            elif line and not line.lower().startswith(('here', 'the following', 'summary')):
                # Skip introductory text
                current_summary = line
    
    # Add the last summary
    if current_summary and current_number > 0:
        cleaned = re.sub(r'\s+', ' ', current_summary.strip())
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
        summaries.append(cleaned)
    
    return summaries

def test_parsing():
    """Test the parsing with the actual response from the test"""
    
    # Sample response from the test results
    sample_response = """Here are the concise summaries for each recipe:

1.  **White Lasagne with Parmigiano Besciamella (Lasagne in Bianco)**: A white lasagne featuring layers of pasta with a rich Parmigiano Besciamella sauce made with shallots, milk, chicken stock, eggs, and Marsala, baked until golden.
2.  **Gluten-Free Coconut Bread**: A gluten-free loaf made with a blend of white rice, sorghum, and tapioca flours, enriched with toasted shredded coconut and coconut milk, baked in a loaf pan.
3.  **Whole Grain Shortbread with Einkorn and Rye Flour**: A shortbread cookie prepared with a blend of einkorn, rye, and rice flours along with cornstarch, mixed with very soft butter and sugar, then pressed into a baking dish and baked.
4.  **Sour Cream Apple Pie**: A classic apple pie featuring a pre-chilled pastry shell filled with sliced Granny Smith apples and a creamy, spiced custard made from sour cream, eggs, vanilla, and sugar, then baked.
5.  **Potato Pancakes**: Crispy potato pancakes made from grated baking potatoes and onion, bound with flour, baking powder, and eggs, seasoned with cinnamon and pepper, then pan-fried until golden."""
    
    print("🧪 TESTING BATCH RESPONSE PARSING")
    print("=" * 50)
    
    expected_count = 5
    summaries = parse_batch_response(sample_response, expected_count)
    
    print(f"📊 Expected: {expected_count} summaries")
    print(f"📊 Got: {len(summaries)} summaries")
    print()
    
    for i, summary in enumerate(summaries, 1):
        print(f"📝 Summary {i}:")
        if summary:
            print(f"   Length: {len(summary)} characters")
            print(f"   Content: {summary[:100]}{'...' if len(summary) > 100 else ''}")
            
            # Check for issues
            issues = []
            if "**" in summary:
                issues.append("Contains markdown")
            if any(f"{j}." in summary for j in range(1, 10)):
                issues.append("Contains numbers")
            if len(summary) < 20:
                issues.append("Too short")
            if len(summary) > 1000:
                issues.append("Too long")
                
            if issues:
                print(f"   ⚠️  Issues: {', '.join(issues)}")
            else:
                print(f"   ✅ Valid")
        else:
            print(f"   ❌ Empty summary")
        print()
    
    # Overall assessment
    valid_summaries = sum(1 for s in summaries if s and 20 <= len(s) <= 1000 and "**" not in s and not any(f"{j}." in s for j in range(1, 10)))
    success_rate = valid_summaries / expected_count * 100
    
    print(f"🎯 RESULTS:")
    print(f"   Valid summaries: {valid_summaries}/{expected_count}")
    print(f"   Success rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("   ✅ EXCELLENT: Parsing is working correctly!")
        return True
    elif success_rate >= 60:
        print("   ⚠️  GOOD: Mostly working, minor issues")
        return True
    else:
        print("   ❌ POOR: Parsing has issues")
        return False

if __name__ == "__main__":
    success = test_parsing()
    sys.exit(0 if success else 1)