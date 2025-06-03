#!/usr/bin/env python3
"""
GitHub Actions Monitor for Meme Maker
Helps track the status of workflow runs after pushing code
"""
import requests
import time
import sys
from datetime import datetime

def check_actions_status():
    """Check the status of recent GitHub Actions workflows"""
    
    # Your repository details
    owner = "subszero0"
    repo = "Meme-Maker"
    
    # GitHub API endpoint for workflow runs
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    
    try:
        print("🔍 Checking GitHub Actions status...")
        print(f"📍 Repository: https://github.com/{owner}/{repo}")
        print(f"🌐 Actions URL: https://github.com/{owner}/{repo}/actions")
        print("=" * 60)
        
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        runs = data.get('workflow_runs', [])
        
        if not runs:
            print("❓ No workflow runs found")
            return
        
        # Get the most recent 5 runs
        recent_runs = runs[:5]
        
        print(f"📊 Latest {len(recent_runs)} workflow runs:")
        print()
        
        for i, run in enumerate(recent_runs, 1):
            name = run.get('name', 'Unknown')
            status = run.get('status', 'unknown')
            conclusion = run.get('conclusion', 'none')
            created_at = run.get('created_at', '')
            html_url = run.get('html_url', '')
            
            # Format timestamp
            if created_at:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            else:
                time_str = 'Unknown time'
            
            # Choose emoji based on status
            if status == 'completed':
                if conclusion == 'success':
                    emoji = "✅"
                elif conclusion == 'failure':
                    emoji = "❌"
                elif conclusion == 'cancelled':
                    emoji = "🚫"
                else:
                    emoji = "⚠️"
            elif status == 'in_progress':
                emoji = "🔄"
            elif status == 'queued':
                emoji = "⏳"
            else:
                emoji = "❓"
            
            print(f"{i}. {emoji} {name}")
            print(f"   Status: {status} | Conclusion: {conclusion}")
            print(f"   Time: {time_str}")
            print(f"   URL: {html_url}")
            print()
        
        # Check if any are still running
        running_count = sum(1 for run in recent_runs if run.get('status') in ['in_progress', 'queued'])
        failed_count = sum(1 for run in recent_runs if run.get('conclusion') == 'failure')
        success_count = sum(1 for run in recent_runs if run.get('conclusion') == 'success')
        
        print("=" * 60)
        print(f"📈 Summary: {success_count} successful, {failed_count} failed, {running_count} running")
        
        if running_count > 0:
            print("⏳ Some workflows are still running. Check back in a few minutes.")
        elif failed_count > 0:
            print("❌ Some workflows failed. Check the URLs above for details.")
        else:
            print("✅ All recent workflows completed successfully!")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accessing GitHub API: {e}")
        print("💡 You can manually check: https://github.com/subszero0/Meme-Maker/actions")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Main function with option to keep monitoring"""
    if len(sys.argv) > 1 and sys.argv[1] == '--watch':
        print("👀 Watching mode: Will check every 30 seconds. Press Ctrl+C to stop.")
        try:
            while True:
                check_actions_status()
                print("\n⏰ Waiting 30 seconds for next check...\n")
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped.")
    else:
        check_actions_status()
        print("\n💡 Tip: Run 'python monitor_actions.py --watch' to keep monitoring")

if __name__ == "__main__":
    main() 