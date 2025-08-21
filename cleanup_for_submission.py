#!/usr/bin/env python3.9
"""
MealMateAI Project Cleanup for Submission
Preserves all valuable academic content while removing only development artifacts
"""

import os
import shutil
from pathlib import Path

def cleanup_project():
    """Clean up the MealMateAI project for submission"""
    
    print("🧹 CLEANING UP MEALMATEAI PROJECT FOR SUBMISSION")
    print("=" * 60)
    
    base_dir = Path(".")
    
    # 1. Remove ONLY development artifacts (keep all scripts!)
    print("📁 Removing development artifacts only...")
    
    # Only remove these specific development artifacts
    artifacts_to_remove = [
        "cache/",           # Build caches
        "venv/",            # Virtual environment  
        "node_modules/",    # Node.js dependencies (can be reinstalled)
        "__pycache__/",     # Python cache
        ".DS_Store",        # macOS system files
        ".pytest_cache/",   # Test cache
        "thinking_logs_live.txt"  # Live logs (keep historical logs)
    ]
    
    # Remove only these artifacts
    for pattern in artifacts_to_remove:
        if pattern.endswith('/'):
            # Directory patterns
            for path in base_dir.rglob(pattern.rstrip('/')):
                if path.is_dir():
                    print(f"   Removing: {path}")
                    shutil.rmtree(path, ignore_errors=True)
        else:
            # File patterns
            for path in base_dir.rglob(pattern):
                if path.is_file():
                    print(f"   Removing: {path}")
                    path.unlink(missing_ok=True)
    
    # 2. Organize performance testing (KEEP ALL SCRIPTS!)
    print("\n📊 Organizing performance testing directory...")
    
    perf_dir = Path("performance-testing")
    if perf_dir.exists():
        # Create organized subdirectories
        (perf_dir / "scripts").mkdir(exist_ok=True)
        (perf_dir / "documentation").mkdir(exist_ok=True)
        
        # Move scripts to organized location (but keep them!)
        script_files = [
            "ai_test_bypass.py",
            "debug_ai_responses.py", 
            "test_ai_fixed.py",
            "test_ai_with_token.py",
            "working_performance.py",
            "final_comprehensive_test.py",  # KEEP THIS!
            "create_performance_graphs.py"
        ]
        
        for script in script_files:
            script_path = perf_dir / script
            if script_path.exists():
                dest = perf_dir / "scripts" / script
                if not dest.exists():
                    print(f"   Organizing: {script} -> scripts/")
                    shutil.move(str(script_path), str(dest))
        
        # Move locust files to scripts
        for locust_file in perf_dir.glob("locustfile_*.py"):
            dest = perf_dir / "scripts" / locust_file.name
            if not dest.exists():
                print(f"   Organizing: {locust_file.name} -> scripts/")
                shutil.move(str(locust_file), str(dest))
        
        # Move documentation
        doc_files = ["safety_measures.md", "stress_test_plan.md"]
        for doc in doc_files:
            doc_path = perf_dir / doc
            if doc_path.exists():
                dest = perf_dir / "documentation" / doc
                if not dest.exists():
                    print(f"   Organizing: {doc} -> documentation/")
                    shutil.move(str(doc_path), str(dest))
    
    # 3. Clean up recipe service logs (but keep the structure)
    print("\n🍽️ Cleaning recipe service logs...")
    
    recipe_logs = Path("services/recipe-service/logs")
    if recipe_logs.exists():
        # Keep only the most recent logs (last 3 days worth)
        log_files = list(recipe_logs.glob("*.log"))
        if len(log_files) > 6:  # Keep 6 most recent
            log_files.sort(key=lambda x: x.stat().st_mtime)
            for old_log in log_files[:-6]:
                print(f"   Removing old log: {old_log}")
                old_log.unlink()
    
    # 4. Remove only truly temporary files
    print("\n🗑️ Removing only temporary files...")
    
    temp_files_to_remove = [
        "*.tmp",
        "*.temp", 
        "*~",
        "*.swp",
        ".#*"
    ]
    
    for pattern in temp_files_to_remove:
        for path in base_dir.rglob(pattern):
            if path.is_file():
                print(f"   Removing: {path}")
                path.unlink()
    
    # 5. Create academic submission guide
    print("\n📚 Creating submission documentation...")
    
    create_academic_submission_guide()
    
    print("\n✅ PROJECT CLEANUP COMPLETED!")
    print("=" * 60)
    print("🎓 PRESERVED FOR ACADEMIC REVIEW:")
    print("   ✅ All performance testing scripts")
    print("   ✅ Final comprehensive test") 
    print("   ✅ AI debugging and testing tools")
    print("   ✅ Development documentation")
    print("   ✅ Architecture diagrams")
    print("   ✅ Implementation examples")
    print("")
    print("🗑️ REMOVED ONLY:")
    print("   ❌ Build caches and virtual environments")
    print("   ❌ System files (.DS_Store, __pycache__)")
    print("   ❌ Excessive log files")
    print("")
    print("📁 Your project is ready for academic submission!")

def create_academic_submission_guide():
    """Create a guide for academic reviewers"""
    
    guide_content = """# MealMateAI - Academic Submission Guide

## 🎓 For Academic Reviewers

### Quick Evaluation Points
- **Architecture**: Microservices with Docker containerization
- **AI Integration**: RAG with Google Gemini LLM + vector search
- **Performance**: Comprehensive testing with real metrics
- **Code Quality**: Production-ready with security and monitoring

### Key Files to Review

#### 1. Project Report
📄 `mealmateAI.pdf` - Complete academic report with conclusions

#### 2. Architecture & Implementation
🏗️ `ARCHITECTURE.md` - System design and component details
📋 `CLAUDE.md` - Development guide with commands and patterns
🐳 `docker-compose.yml` - Production deployment configuration

#### 3. Performance Analysis
📊 `performance-testing/results/final_comprehensive_report.json` - Complete metrics
📈 `performance-testing/results/*.png` - Performance visualizations
🔬 `performance-testing/scripts/final_comprehensive_test.py` - Testing methodology

#### 4. AI Implementation
🤖 `services/recipe-service/` - Vector search + semantic embeddings
🧠 `services/meal-planner-service/` - RAG meal planning with LLM
📝 `services/*/prompts/` - LLM prompt engineering examples

#### 5. Development Scripts (Academic Interest)
🧪 `performance-testing/scripts/` - All testing and debugging tools
📊 `performance-testing/create_performance_graphs.py` - Data visualization
🔍 AI testing and validation scripts

### Running the Application
```bash
# Full system startup
docker-compose up --build

# Access points
Frontend: http://localhost
API Docs: http://localhost:3000/docs
```

### Performance Highlights
- **Database Operations**: ~25ms average
- **Vector Search**: ~375ms average (10k+ recipes)  
- **AI Recommendations**: ~15s (real Gemini processing)
- **Concurrent Load**: Scales effectively

### Technical Achievements
✅ Microservices architecture with proper separation of concerns
✅ RAG implementation with semantic search
✅ Production-ready containerization and deployment
✅ Comprehensive performance testing and optimization
✅ Real AI integration with cost controls and monitoring
✅ Modern frontend with TypeScript and Material-UI

---
**Note**: All development scripts and debugging tools have been preserved to demonstrate the thorough development and testing process.
"""
    
    with open("ACADEMIC_REVIEW_GUIDE.md", "w") as f:
        f.write(guide_content)

if __name__ == "__main__":
    cleanup_project()