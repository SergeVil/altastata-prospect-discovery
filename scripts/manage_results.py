#!/usr/bin/env python3
"""
Script to manage and organize results by date
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import glob
from datetime import datetime, timedelta
import shutil

def organize_results_by_date():
    """Organize existing results files into date-based directories"""
    print("📁 Organizing Results by Date")
    print("=" * 50)
    
    results_dir = "results"
    if not os.path.exists(results_dir):
        print("❌ No results directory found")
        return
    
    # Find all result files in root of results directory
    patterns = [
        "results/ai_security_analysis_*.json",
        "results/generated_emails_*.csv", 
        "results/linkedin_prospects_*.md"
    ]
    
    files_moved = 0
    for pattern in patterns:
        files = glob.glob(pattern)
        for file_path in files:
            filename = os.path.basename(file_path)
            
            # Extract date from filename (format: *_YYYYMMDD_HHMMSS.ext)
            try:
                # Find the date part in the filename
                parts = filename.split('_')
                date_part = None
                for part in parts:
                    if len(part) == 8 and part.isdigit():  # YYYYMMDD format
                        date_part = part
                        break
                
                if date_part:
                    # Convert YYYYMMDD to YYYY-MM-DD
                    year = date_part[:4]
                    month = date_part[4:6]
                    day = date_part[6:8]
                    date_str = f"{year}-{month}-{day}"
                    
                    # Create date directory
                    date_dir = f"results/{date_str}"
                    os.makedirs(date_dir, exist_ok=True)
                    
                    # Move file
                    new_path = f"{date_dir}/{filename}"
                    shutil.move(file_path, new_path)
                    print(f"📄 Moved: {filename} → {date_str}/")
                    files_moved += 1
                    
            except Exception as e:
                print(f"⚠️  Could not organize {filename}: {e}")
    
    print(f"\n✅ Organized {files_moved} files into date directories")

def list_results_by_date():
    """List all results organized by date"""
    print("📊 Results by Date")
    print("=" * 50)
    
    results_dir = "results"
    if not os.path.exists(results_dir):
        print("❌ No results directory found")
        return
    
    # Get all date directories
    date_dirs = []
    for item in os.listdir(results_dir):
        item_path = os.path.join(results_dir, item)
        if os.path.isdir(item_path) and item.startswith("20"):  # Date format YYYY-MM-DD
            date_dirs.append(item)
    
    date_dirs.sort(reverse=True)  # Most recent first
    
    if not date_dirs:
        print("📂 No organized date directories found")
        print("💡 Run organize_results_by_date() first")
        return
    
    for date_dir in date_dirs:
        print(f"\n📅 **{date_dir}**")
        date_path = f"results/{date_dir}"
        
        # Count files by type
        json_files = glob.glob(f"{date_path}/*.json")
        csv_files = glob.glob(f"{date_path}/*.csv")
        md_files = glob.glob(f"{date_path}/*.md")
        
        print(f"   📋 {len(json_files)} analysis files")
        print(f"   ✉️  {len(csv_files)} email files")
        print(f"   🎯 {len(md_files)} LinkedIn prospect files")
        
        # Show latest files
        all_files = json_files + csv_files + md_files
        if all_files:
            latest_file = max(all_files, key=os.path.getmtime)
            latest_name = os.path.basename(latest_file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
            print(f"   🕐 Latest: {latest_name} ({mod_time.strftime('%I:%M %p')})")

def get_latest_prospects():
    """Get the path to the latest LinkedIn prospects file"""
    print("🎯 Finding Latest LinkedIn Prospects")
    print("=" * 50)
    
    # Find all LinkedIn prospect files
    prospect_files = glob.glob("results/*/linkedin_prospects_*.md")
    
    if not prospect_files:
        print("❌ No LinkedIn prospect files found")
        return None
    
    # Get the most recent file
    latest_file = max(prospect_files, key=os.path.getmtime)
    mod_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
    
    print(f"📄 Latest prospects file: {latest_file}")
    print(f"🕐 Generated: {mod_time.strftime('%B %d, %Y at %I:%M %p')}")
    
    return latest_file

def cleanup_old_results(days_to_keep=30):
    """Move old results to archives"""
    print(f"🧹 Cleaning Up Results Older Than {days_to_keep} Days")
    print("=" * 50)
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    archives_dir = "results/archives"
    os.makedirs(archives_dir, exist_ok=True)
    
    date_dirs = glob.glob("results/20*")  # Date directories
    moved_count = 0
    
    for date_dir in date_dirs:
        dir_name = os.path.basename(date_dir)
        try:
            # Parse date from directory name YYYY-MM-DD
            dir_date = datetime.strptime(dir_name, "%Y-%m-%d")
            
            if dir_date < cutoff_date:
                archive_path = f"{archives_dir}/{dir_name}"
                shutil.move(date_dir, archive_path)
                print(f"📦 Archived: {dir_name}")
                moved_count += 1
                
        except ValueError:
            print(f"⚠️  Skipping invalid date directory: {dir_name}")
    
    print(f"\n✅ Archived {moved_count} old result directories")

def show_results_summary():
    """Show a summary of all results"""
    print("📊 Results Summary")
    print("=" * 50)
    
    # Current results
    current_dirs = glob.glob("results/20*")
    current_dirs.sort(reverse=True)
    
    total_json = len(glob.glob("results/*/*.json"))
    total_csv = len(glob.glob("results/*/*.csv"))
    total_md = len(glob.glob("results/*/*.md"))
    
    print(f"📂 Active date directories: {len(current_dirs)}")
    print(f"📋 Total analysis files: {total_json}")
    print(f"✉️  Total email files: {total_csv}")
    print(f"🎯 Total prospect files: {total_md}")
    
    if current_dirs:
        latest_dir = current_dirs[0]
        print(f"\n📅 Latest results: {os.path.basename(latest_dir)}")
        
        # Show storage usage
        total_size = 0
        for root, dirs, files in os.walk("results"):
            for file in files:
                total_size += os.path.getsize(os.path.join(root, file))
        
        size_mb = total_size / (1024 * 1024)
        print(f"💾 Total storage: {size_mb:.1f} MB")

def main():
    """Main function with command options"""
    import sys
    
    if len(sys.argv) < 2:
        print("🛠️  Results Management Tool")
        print("=" * 30)
        print("Usage: python scripts/manage_results.py <command>")
        print()
        print("Commands:")
        print("  organize    - Organize files into date directories")
        print("  list        - List results by date")
        print("  latest      - Show latest prospects file")
        print("  cleanup     - Archive old results (30+ days)")
        print("  summary     - Show overall summary")
        return
    
    command = sys.argv[1].lower()
    
    if command == "organize":
        organize_results_by_date()
    elif command == "list":
        list_results_by_date()
    elif command == "latest":
        get_latest_prospects()
    elif command == "cleanup":
        cleanup_old_results()
    elif command == "summary":
        show_results_summary()
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: organize, list, latest, cleanup, summary")

if __name__ == "__main__":
    main()
