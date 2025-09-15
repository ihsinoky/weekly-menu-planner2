"""
Notion integration for updating weekly menu pages
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional

from notion_client import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class NotionMenuUpdater:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        notion_token = os.getenv('NOTION_TOKEN')
        if not notion_token:
            raise ValueError("NOTION_TOKEN environment variable is required")
            
        self.notion = Client(auth=notion_token)
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID environment variable is required")
    
    def _retry_with_backoff(self, func, max_retries=3, base_delay=1):
        """Execute function with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"Final attempt failed: {e}")
                    raise
                
                delay = base_delay * (2 ** attempt)
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
    
    def load_generated_menu(self) -> Dict:
        """Load the generated menu data"""
        menu_path = Path('data/generated_menu.json')
        if not menu_path.exists():
            raise FileNotFoundError("No generated menu found. Run generate_menu.py first.")
        
        with open(menu_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def find_existing_page(self, week_start: str) -> Optional[str]:
        """Find existing Notion page for the week with retry logic"""
        def _query_database():
            self.logger.info(f"Searching for existing page for week: {week_start}")
            return self.notion.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Week Start",
                    "date": {
                        "equals": week_start
                    }
                }
            )
        
        try:
            response = self._retry_with_backoff(_query_database, max_retries=3, base_delay=2)
            
            if response['results']:
                page_id = response['results'][0]['id']
                self.logger.info(f"Found existing page: {page_id}")
                return page_id
            return None
            
        except Exception as e:
            self.logger.error(f"Error searching for existing page: {e}")
            return None
    
    def archive_existing_page(self, page_id: str):
        """Archive existing page by setting archived property to true with retry logic"""
        def _archive_page():
            self.logger.info(f"Archiving page: {page_id}")
            return self.notion.pages.update(
                page_id=page_id,
                archived=True
            )
        
        try:
            self._retry_with_backoff(_archive_page, max_retries=3, base_delay=2)
            self.logger.info(f"Successfully archived page: {page_id}")
        except Exception as e:
            self.logger.error(f"Error archiving page {page_id}: {e}")
            raise
    
    def create_notion_page(self, menu_data: Dict) -> str:
        """Create new Notion page with weekly menu with retry logic"""
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
        
        def _create_page():
            self.logger.info(f"Creating Notion page for week: {week_start}")
            return self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children
            )
        
        try:
            response = self._retry_with_backoff(_create_page, max_retries=3, base_delay=2)
            page_id = response['id']
            self.logger.info(f"Successfully created Notion page: {page_id}")
            return page_id
            
        except Exception as e:
            self.logger.error(f"Error creating Notion page: {e}")
            self.logger.error(f"Database ID: {self.database_id}")
            self.logger.error(f"Week start: {week_start}")
            raise
    
    def update_menu(self):
        """Main function to update Notion with generated menu"""
        menu_data = self.load_generated_menu()
        week_start = menu_data['week_start']
        
        # Check for existing page
        existing_page_id = self.find_existing_page(week_start)
        
        if existing_page_id:
            self.logger.info(f"Found existing page for week {week_start}, archiving...")
            self.archive_existing_page(existing_page_id)
        
        # Create new page
        self.logger.info("Creating new Notion page...")
        new_page_id = self.create_notion_page(menu_data)
        
        self.logger.info(f"Successfully created Notion page: {new_page_id}")
        return new_page_id


def main():
    """Main function to update Notion with weekly menu"""
    try:
        updater = NotionMenuUpdater()
        page_id = updater.update_menu()
        print(f"Menu successfully updated in Notion: {page_id}")
        
    except Exception as e:
        logging.error(f"Error updating Notion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()