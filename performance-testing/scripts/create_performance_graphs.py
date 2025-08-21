#!/usr/bin/env python3.9
"""
Performance Data Visualization Script
Generates professional charts and graphs from MealMateAI performance test results
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path
import pandas as pd
from matplotlib.patches import Rectangle
import warnings
warnings.filterwarnings('ignore')

# Set professional style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def load_performance_data():
    """Load performance data from JSON file"""
    with open('results/final_comprehensive_report.json', 'r') as f:
        return json.load(f)

def create_response_time_comparison():
    """Create a comprehensive response time comparison chart"""
    data = load_performance_data()
    stats = data['statistics']
    
    # Create categories and their average response times
    categories = []
    avg_times = []
    colors = []
    
    # Database operations (green)
    db_categories = ['health_check', 'database_recipes', 'database_collections', 'database_recipe_detail']
    for cat in db_categories:
        categories.append(cat.replace('_', ' ').title())
        avg_times.append(stats[cat]['avg'])
        colors.append('#2E8B57')  # Sea Green
    
    # Vector search operations (blue)
    vector_categories = ['vector_multi_search', 'vector_protein_search', 'vector_dessert_search', 
                        'vector_breakfast_search', 'vector_quick_search', 'vector_fresh_search']
    for cat in vector_categories:
        categories.append(cat.replace('_', ' ').title().replace('Vector ', ''))
        avg_times.append(stats[cat]['avg'])
        colors.append('#4682B4')  # Steel Blue
    
    # User operations (orange)
    user_categories = ['authentication', 'user_preferences_get', 'user_preferences_update']
    for cat in user_categories:
        categories.append(cat.replace('_', ' ').title())
        avg_times.append(stats[cat]['avg'])
        colors.append('#FF8C00')  # Dark Orange
    
    # AI operations (red) - convert to seconds for better visualization
    ai_categories = ['ai_recommendations', 'ai_meal_planning']
    for cat in ai_categories:
        categories.append(cat.replace('_', ' ').title())
        avg_times.append(stats[cat]['avg'] / 1000)  # Convert to seconds
        colors.append('#DC143C')  # Crimson
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Create bars
    bars = ax.bar(range(len(categories)), avg_times, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Customize the plot
    ax.set_xlabel('Operation Categories', fontsize=14, fontweight='bold')
    ax.set_ylabel('Average Response Time (ms/s)', fontsize=14, fontweight='bold')
    ax.set_title('MealMateAI Performance Overview - Average Response Times', fontsize=16, fontweight='bold', pad=20)
    
    # Set x-axis labels
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=10)
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, avg_times)):
        height = bar.get_height()
        if i >= len(categories) - 2:  # AI operations in seconds
            label = f'{value:.1f}s'
        else:  # Other operations in milliseconds
            label = f'{value:.1f}ms'
        ax.text(bar.get_x() + bar.get_width()/2., height + max(avg_times)*0.01,
                label, ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    # Add legend
    legend_elements = [
        Rectangle((0,0),1,1, facecolor='#2E8B57', alpha=0.8, label='Database Operations'),
        Rectangle((0,0),1,1, facecolor='#4682B4', alpha=0.8, label='Vector Search'),
        Rectangle((0,0),1,1, facecolor='#FF8C00', alpha=0.8, label='User Operations'),
        Rectangle((0,0),1,1, facecolor='#DC143C', alpha=0.8, label='AI Operations')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=11)
    
    # Add grid for better readability
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    plt.savefig('results/response_time_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_ai_performance_analysis():
    """Create detailed AI performance analysis charts"""
    data = load_performance_data()
    
    # Create subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('AI Performance Deep Dive Analysis', fontsize=16, fontweight='bold')
    
    # 1. AI Response Time Distribution
    ai_rec_times = [t/1000 for t in data['measurements']['ai_recommendations']]  # Convert to seconds
    ai_meal_times = [t/1000 for t in data['measurements']['ai_meal_planning']]
    
    ax1.hist(ai_rec_times, bins=8, alpha=0.7, color='#FF6B6B', label='Recommendations', edgecolor='black')
    ax1.hist(ai_meal_times, bins=8, alpha=0.7, color='#4ECDC4', label='Meal Planning', edgecolor='black')
    ax1.set_xlabel('Response Time (seconds)', fontweight='bold')
    ax1.set_ylabel('Frequency', fontweight='bold')
    ax1.set_title('AI Response Time Distribution', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. AI vs Non-AI Performance Comparison
    categories = ['Database\nOperations', 'Vector\nSearch', 'User\nOperations', 'AI\nRecommendations', 'AI Meal\nPlanning']
    avg_times = [
        np.mean([data['statistics']['database_recipes']['avg'], 
                data['statistics']['database_collections']['avg']]),
        data['statistics']['vector_multi_search']['avg'],
        data['statistics']['authentication']['avg'],
        data['statistics']['ai_recommendations']['avg'] / 1000,  # Convert to seconds
        data['statistics']['ai_meal_planning']['avg'] / 1000
    ]
    colors = ['#2E8B57', '#4682B4', '#FF8C00', '#DC143C', '#8B0000']
    
    bars = ax2.bar(categories, avg_times, color=colors, alpha=0.8, edgecolor='black')
    ax2.set_ylabel('Average Response Time (ms/s)', fontweight='bold')
    ax2.set_title('Performance Categories Comparison', fontweight='bold')
    
    # Add value labels
    for bar, value in zip(bars, avg_times):
        height = bar.get_height()
        if value > 1000:
            label = f'{value:.1f}s'
        else:
            label = f'{value:.0f}ms'
        ax2.text(bar.get_x() + bar.get_width()/2., height + max(avg_times)*0.02,
                label, ha='center', va='bottom', fontweight='bold')
    
    ax2.grid(True, alpha=0.3)
    
    # 3. AI Performance Variability
    ai_rec_stats = data['statistics']['ai_recommendations']
    ai_meal_stats = data['statistics']['ai_meal_planning']
    
    categories = ['AI Recommendations', 'AI Meal Planning']
    means = [ai_rec_stats['avg']/1000, ai_meal_stats['avg']/1000]
    stds = [ai_rec_stats['std']/1000, ai_meal_stats['std']/1000]
    mins = [ai_rec_stats['min']/1000, ai_meal_stats['min']/1000]
    maxs = [ai_rec_stats['max']/1000, ai_meal_stats['max']/1000]
    
    x_pos = np.arange(len(categories))
    bars = ax3.bar(x_pos, means, yerr=stds, capsize=10, color=['#FF6B6B', '#4ECDC4'], 
                   alpha=0.8, edgecolor='black', error_kw={'linewidth': 2})
    
    # Add min/max markers
    for i, (mean, min_val, max_val) in enumerate(zip(means, mins, maxs)):
        ax3.plot(i, min_val, 'v', color='red', markersize=8, label='Min' if i == 0 else "")
        ax3.plot(i, max_val, '^', color='darkred', markersize=8, label='Max' if i == 0 else "")
    
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(categories)
    ax3.set_ylabel('Response Time (seconds)', fontweight='bold')
    ax3.set_title('AI Performance Variability', fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Percentile Analysis
    p50_rec = ai_rec_stats['p50'] / 1000
    p95_rec = ai_rec_stats['p95'] / 1000
    p99_rec = ai_rec_stats['p99'] / 1000
    
    p50_meal = ai_meal_stats['p50'] / 1000
    p95_meal = ai_meal_stats['p95'] / 1000
    p99_meal = ai_meal_stats['p99'] / 1000
    
    percentiles = ['P50', 'P95', 'P99']
    rec_values = [p50_rec, p95_rec, p99_rec]
    meal_values = [p50_meal, p95_meal, p99_meal]
    
    x = np.arange(len(percentiles))
    width = 0.35
    
    ax4.bar(x - width/2, rec_values, width, label='Recommendations', color='#FF6B6B', alpha=0.8, edgecolor='black')
    ax4.bar(x + width/2, meal_values, width, label='Meal Planning', color='#4ECDC4', alpha=0.8, edgecolor='black')
    
    ax4.set_xlabel('Percentiles', fontweight='bold')
    ax4.set_ylabel('Response Time (seconds)', fontweight='bold')
    ax4.set_title('AI Performance Percentiles', fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(percentiles)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('results/ai_performance_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_vector_search_comparison():
    """Create vector search performance comparison"""
    data = load_performance_data()
    stats = data['statistics']
    
    # Vector search categories
    vector_cats = ['vector_multi_search', 'vector_protein_search', 'vector_dessert_search', 
                   'vector_breakfast_search', 'vector_quick_search', 'vector_fresh_search']
    
    categories = ['Multi-Collection\nSearch', 'Protein\nSearch', 'Dessert\nSearch', 
                  'Breakfast\nSearch', 'Quick\nSearch', 'Fresh\nSearch']
    
    # Extract performance metrics
    avg_times = [stats[cat]['avg'] for cat in vector_cats]
    p50_times = [stats[cat]['p50'] for cat in vector_cats]
    p95_times = [stats[cat]['p95'] for cat in vector_cats]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Vector Search Performance Analysis', fontsize=16, fontweight='bold')
    
    # 1. Average response times comparison
    bars = ax1.bar(categories, avg_times, color='#4682B4', alpha=0.8, edgecolor='black')
    ax1.set_ylabel('Average Response Time (ms)', fontweight='bold')
    ax1.set_title('Vector Search Average Response Times', fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    
    # Add value labels
    for bar, value in zip(bars, avg_times):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + max(avg_times)*0.02,
                f'{value:.1f}ms', ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    ax1.grid(True, alpha=0.3)
    
    # 2. Percentile comparison
    x = np.arange(len(categories))
    width = 0.25
    
    ax2.bar(x - width, avg_times, width, label='Average', color='#4682B4', alpha=0.8, edgecolor='black')
    ax2.bar(x, p50_times, width, label='P50', color='#87CEEB', alpha=0.8, edgecolor='black')
    ax2.bar(x + width, p95_times, width, label='P95', color='#191970', alpha=0.8, edgecolor='black')
    
    ax2.set_xlabel('Search Types', fontweight='bold')
    ax2.set_ylabel('Response Time (ms)', fontweight='bold')
    ax2.set_title('Vector Search Percentile Analysis', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('results/vector_search_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_concurrent_performance_analysis():
    """Create concurrent performance analysis"""
    data = load_performance_data()
    
    concurrent_vector = data['measurements']['concurrent_vector']
    concurrent_db = data['measurements']['concurrent_database']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Concurrent Load Performance Analysis', fontsize=16, fontweight='bold')
    
    # 1. Concurrent vector search performance over time
    ax1.plot(range(1, len(concurrent_vector) + 1), concurrent_vector, 
             marker='o', linewidth=2, markersize=6, color='#4682B4', label='Vector Search')
    ax1.set_xlabel('Request Number', fontweight='bold')
    ax1.set_ylabel('Response Time (ms)', fontweight='bold')
    ax1.set_title('Concurrent Vector Search Performance', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Add trend line
    z = np.polyfit(range(len(concurrent_vector)), concurrent_vector, 1)
    p = np.poly1d(z)
    ax1.plot(range(1, len(concurrent_vector) + 1), p(range(len(concurrent_vector))), 
             "--", alpha=0.8, color='red', label='Trend')
    ax1.legend()
    
    # 2. Concurrent database performance over time
    ax2.plot(range(1, len(concurrent_db) + 1), concurrent_db, 
             marker='s', linewidth=2, markersize=6, color='#2E8B57', label='Database Operations')
    ax2.set_xlabel('Request Number', fontweight='bold')
    ax2.set_ylabel('Response Time (ms)', fontweight='bold')
    ax2.set_title('Concurrent Database Performance', fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Add trend line
    z = np.polyfit(range(len(concurrent_db)), concurrent_db, 1)
    p = np.poly1d(z)
    ax2.plot(range(1, len(concurrent_db) + 1), p(range(len(concurrent_db))), 
             "--", alpha=0.8, color='red', label='Trend')
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig('results/concurrent_performance_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_performance_summary_table():
    """Create a comprehensive performance summary table"""
    data = load_performance_data()
    stats = data['statistics']
    
    # Create summary data
    summary_data = []
    
    categories = [
        ('Database Operations', ['health_check', 'database_recipes', 'database_collections', 'database_recipe_detail']),
        ('Vector Search', ['vector_multi_search', 'vector_protein_search', 'vector_dessert_search', 
                          'vector_breakfast_search', 'vector_quick_search', 'vector_fresh_search']),
        ('User Operations', ['authentication', 'user_preferences_get', 'user_preferences_update']),
        ('AI Operations', ['ai_recommendations', 'ai_meal_planning']),
        ('Concurrent Load', ['concurrent_vector', 'concurrent_database'])
    ]
    
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.axis('tight')
    ax.axis('off')
    
    # Prepare table data
    table_data = []
    headers = ['Category', 'Operation', 'Avg (ms)', 'Min (ms)', 'Max (ms)', 'P50 (ms)', 'P95 (ms)', 'P99 (ms)', 'Tests']
    
    for category, operations in categories:
        for i, op in enumerate(operations):
            stat = stats[op]
            operation_name = op.replace('_', ' ').title()
            
            # Convert AI operations to seconds for display
            if 'ai_' in op:
                avg = f"{stat['avg']/1000:.1f}s"
                min_val = f"{stat['min']/1000:.1f}s"
                max_val = f"{stat['max']/1000:.1f}s"
                p50 = f"{stat['p50']/1000:.1f}s"
                p95 = f"{stat['p95']/1000:.1f}s"
                p99 = f"{stat['p99']/1000:.1f}s"
            else:
                avg = f"{stat['avg']:.1f}"
                min_val = f"{stat['min']:.1f}"
                max_val = f"{stat['max']:.1f}"
                p50 = f"{stat['p50']:.1f}"
                p95 = f"{stat['p95']:.1f}"
                p99 = f"{stat['p99']:.1f}"
            
            row = [
                category if i == 0 else '',
                operation_name,
                avg, min_val, max_val, p50, p95, p99,
                str(stat['count'])
            ]
            table_data.append(row)
    
    # Create table
    table = ax.table(cellText=table_data, colLabels=headers, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 2)
    
    # Style the table
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#4472C4')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Color code rows by category
    colors = ['#E8F4FD', '#FFF2CC', '#F2F2F2', '#FFE6E6', '#E8F5E8']
    color_index = 0
    current_category = ''
    
    for i, row in enumerate(table_data):
        if row[0] != '':  # New category
            current_category = row[0]
            if i > 0:
                color_index += 1
        
        for j in range(len(headers)):
            table[(i+1, j)].set_facecolor(colors[color_index % len(colors)])
    
    plt.title('MealMateAI Performance Summary Table', fontsize=16, fontweight='bold', pad=20)
    plt.savefig('results/performance_summary_table.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_architecture_performance_chart():
    """Create an architecture-based performance visualization"""
    data = load_performance_data()
    stats = data['statistics']
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Define architecture layers and their performance
    layers = {
        'Frontend/API Gateway': {
            'operations': ['health_check'],
            'color': '#FF9999',
            'y_pos': 0.8
        },
        'Authentication Layer': {
            'operations': ['authentication', 'user_preferences_get', 'user_preferences_update'],
            'color': '#FFB366',
            'y_pos': 0.6
        },
        'Database Layer': {
            'operations': ['database_recipes', 'database_collections', 'database_recipe_detail'],
            'color': '#66B2FF',
            'y_pos': 0.4
        },
        'Vector Search Layer': {
            'operations': ['vector_multi_search', 'vector_protein_search', 'vector_dessert_search'],
            'color': '#66FFB2',
            'y_pos': 0.2
        },
        'AI Processing Layer': {
            'operations': ['ai_recommendations', 'ai_meal_planning'],
            'color': '#FF6666',
            'y_pos': 0.0
        }
    }
    
    max_time = 0
    for layer_name, layer_info in layers.items():
        avg_times = []
        for op in layer_info['operations']:
            avg_time = stats[op]['avg']
            if 'ai_' in op:
                avg_time = avg_time / 1000  # Convert to seconds for AI
            avg_times.append(avg_time)
        
        layer_avg = np.mean(avg_times)
        max_time = max(max_time, layer_avg)
        
        # Create horizontal bar
        bar_width = layer_avg / (25000 if any('ai_' in op for op in layer_info['operations']) else 1000)
        rect = Rectangle((0, layer_info['y_pos']), bar_width, 0.15, 
                        facecolor=layer_info['color'], alpha=0.7, edgecolor='black')
        ax.add_patch(rect)
        
        # Add layer name
        ax.text(-0.02, layer_info['y_pos'] + 0.075, layer_name, 
               ha='right', va='center', fontweight='bold', fontsize=11)
        
        # Add performance value
        unit = 's' if any('ai_' in op for op in layer_info['operations']) else 'ms'
        ax.text(bar_width + 0.02, layer_info['y_pos'] + 0.075, 
               f'{layer_avg:.1f}{unit}', ha='left', va='center', fontweight='bold')
    
    ax.set_xlim(-0.5, 1.2)
    ax.set_ylim(-0.1, 1.0)
    ax.set_title('MealMateAI Architecture Performance Layers', fontsize=16, fontweight='bold')
    ax.axis('off')
    
    # Add performance scale indicator
    ax.text(0.6, 0.95, 'Performance Scale:', fontweight='bold', fontsize=12)
    ax.text(0.6, 0.9, '← Faster    Slower →', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('results/architecture_performance_chart.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Generate all performance visualization charts"""
    print("🎯 Generating MealMateAI Performance Visualizations...")
    print("=" * 60)
    
    # Create results directory
    Path('results').mkdir(exist_ok=True)
    
    try:
        print("📊 Creating response time comparison chart...")
        create_response_time_comparison()
        
        print("🤖 Creating AI performance analysis...")
        create_ai_performance_analysis()
        
        print("🔍 Creating vector search comparison...")
        create_vector_search_comparison()
        
        print("⚡ Creating concurrent performance analysis...")
        create_concurrent_performance_analysis()
        
        print("📋 Creating performance summary table...")
        create_performance_summary_table()
        
        print("🏗️ Creating architecture performance chart...")
        create_architecture_performance_chart()
        
        print("\n✅ All charts generated successfully!")
        print("📁 Charts saved in 'results/' directory:")
        print("   • response_time_comparison.png")
        print("   • ai_performance_analysis.png") 
        print("   • vector_search_comparison.png")
        print("   • concurrent_performance_analysis.png")
        print("   • performance_summary_table.png")
        print("   • architecture_performance_chart.png")
        
    except Exception as e:
        print(f"❌ Error generating charts: {e}")
        raise

if __name__ == "__main__":
    main()