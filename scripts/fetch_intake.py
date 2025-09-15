"""
Fetch intake.json from GitHub Gist or other storage.
This script tries to retrieve user preferences collected by Dify Slack bot.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path


def get_current_week_start():
    """Get the Monday of the current week"""
    today = datetime.now()
    # Calculate days back to Monday (0=Monday, 6=Sunday)
    days_back = today.weekday()
    monday = today - timedelta(days=days_back)
    return monday.date()


def fetch_from_gist(gist_id, github_token):
    """Fetch intake.json from GitHub Gist"""
    if not gist_id or not github_token:
        print("Missing GIST_ID or GITHUB_TOKEN environment variables")
        return None
    
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f'https://api.github.com/gists/{gist_id}'
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        gist_data = response.json()
        
        # Look for intake files for current week
        week_start = get_current_week_start()
        target_filename = f"intake_{week_start.strftime('%Y_%m_%d')}.json"
        
        # Check for exact match first
        if target_filename in gist_data['files']:
            content = gist_data['files'][target_filename]['content']
            return json.loads(content)
        
        # Fallback: look for any recent intake file
        intake_files = {name: file_data for name, file_data in gist_data['files'].items() 
                       if name.startswith('intake_') and name.endswith('.json')}
        
        if intake_files:
            # Get the most recent file
            latest_file = max(intake_files.items(), key=lambda x: x[0])
            content = latest_file[1]['content']
            print(f"Using fallback intake file: {latest_file[0]}")
            return json.loads(content)
        
        print("No intake files found in gist")
        return None
        
    except requests.RequestException as e:
        print(f"Error fetching from gist: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from gist: {e}")
        return None


def save_intake_locally(intake_data):
    """Save intake data to local file for menu generation script"""
    intake_path = Path('data/intake.json')
    intake_path.parent.mkdir(exist_ok=True)
    
    with open(intake_path, 'w', encoding='utf-8') as f:
        json.dump(intake_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"Intake data saved to {intake_path}")


def main():
    """Main function to fetch and save intake data"""
    gist_id = os.getenv('GIST_ID')
    github_token = os.getenv('GITHUB_TOKEN')
    
    print("Attempting to fetch intake.json...")
    
    # Try to fetch from GitHub Gist
    intake_data = fetch_from_gist(gist_id, github_token)
    
    if intake_data:
        print("Successfully fetched intake data")
        save_intake_locally(intake_data)
        sys.exit(0)
    else:
        print("Could not fetch intake data, will use rules.yaml fallback")
        sys.exit(1)


if __name__ == "__main__":
    main()