"""
Notion integration for updating weekly menu pages
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional

from notion_client import Client


class NotionMenuUpdater:
    def __init__(self):
        notion_token = os.getenv('NOTION_TOKEN')
        if not notion_token:
            raise ValueError("NOTION_TOKEN environment variable is required")
            
        self.notion = Client(auth=notion_token)
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID environment variable is required")
    
    def load_generated_menu(self) -> Dict:
        """Load the generated menu data"""
        menu_path = Path('data/generated_menu.json')
        if not menu_path.exists():
            raise FileNotFoundError("No generated menu found. Run generate_menu.py first.")
        
        with open(menu_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def find_existing_page(self, week_start: str) -> Optional[str]:
        """Find existing Notion page for the week"""
        try:
            response = self.notion.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Week Start",
                    "date": {
                        "equals": week_start
                    }
                }
            )
            
            if response['results']:
                return response['results'][0]['id']
            return None
            
        except Exception as e:
            print(f"Error searching for existing page: {e}")
            return None
    
    def archive_existing_page(self, page_id: str):
        """Archive existing page by setting archived property to true"""
        try:
            self.notion.pages.update(
                page_id=page_id,
                archived=True
            )
            print(f"Archived existing page: {page_id}")
        except Exception as e:
            print(f"Error archiving page: {e}")
    
    def create_notion_page(self, menu_data: Dict) -> str:
        """Create new Notion page with weekly menu"""
        week_start = menu_data['week_start']
        menu_content = menu_data['menu_content']
        generated_at = menu_data['generated_at']
        
        # Parse week start date
        week_date = datetime.fromisoformat(week_start).date()
        
        properties = {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": f"{week_date.strftime('%Y年%m月%d日')}週の献立"
                        }
                    }
                ]
            },
            "Week Start": {
                "date": {
                    "start": week_start
                }
            },
            "Generated At": {
                "date": {
                    "start": generated_at
                }
            },
            "Status": {
                "select": {
                    "name": "Current"
                }
            }
        }
        
        # Add intake data flag if available
        if menu_data.get('intake_data_available'):
            properties["Intake Used"] = {
                "checkbox": True
            }
        
        # Create page content blocks
        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"{week_date.strftime('%Y年%m月%d日')}週の夕食献立"}
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            }
        ]
        
        # Parse menu content and add as blocks
        menu_lines = menu_content.split('\n')
        current_paragraph = []
        
        for line in menu_lines:
            line = line.strip()
            if not line:
                if current_paragraph:
                    # Add accumulated paragraph
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": '\n'.join(current_paragraph)}
                                }
                            ]
                        }
                    })
                    current_paragraph = []
            elif line.startswith('**') and line.endswith('**'):
                # Day header
                if current_paragraph:
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": '\n'.join(current_paragraph)}
                                }
                            ]
                        }
                    })
                    current_paragraph = []
                
                day_name = line.strip('*')
                children.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": day_name},
                                "annotations": {"bold": True}
                            }
                        ]
                    }
                })
            elif line.startswith('- '):
                # Menu item
                children.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": line[2:]}  # Remove "- " prefix
                            }
                        ]
                    }
                })
            else:
                current_paragraph.append(line)
        
        # Add any remaining paragraph
        if current_paragraph:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": '\n'.join(current_paragraph)}
                        }
                    ]
                }
            })
        
        try:
            response = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children
            )
            
            return response['id']
            
        except Exception as e:
            print(f"Error creating Notion page: {e}")
            raise
    
    def update_menu(self):
        """Main function to update Notion with generated menu"""
        menu_data = self.load_generated_menu()
        week_start = menu_data['week_start']
        
        # Check for existing page
        existing_page_id = self.find_existing_page(week_start)
        
        if existing_page_id:
            print(f"Found existing page for week {week_start}, archiving...")
            self.archive_existing_page(existing_page_id)
        
        # Create new page
        print("Creating new Notion page...")
        new_page_id = self.create_notion_page(menu_data)
        
        print(f"Successfully created Notion page: {new_page_id}")
        return new_page_id


def main():
    """Main function to update Notion with weekly menu"""
    try:
        updater = NotionMenuUpdater()
        page_id = updater.update_menu()
        print(f"Menu successfully updated in Notion: {page_id}")
        
    except Exception as e:
        print(f"Error updating Notion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()