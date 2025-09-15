"""
Archive previous week's menu pages in Notion
"""

import os
import sys
from datetime import datetime, timedelta
from notion_client import Client


class NotionArchiver:
    def __init__(self):
        notion_token = os.getenv('NOTION_TOKEN')
        if not notion_token:
            raise ValueError("NOTION_TOKEN environment variable is required")
            
        self.notion = Client(auth=notion_token)
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID environment variable is required")
    
    def get_previous_week_pages(self):
        """Find pages from previous weeks that should be archived"""
        # Get date two weeks ago to archive old pages
        cutoff_date = (datetime.now() - timedelta(weeks=2)).date().isoformat()
        
        try:
            response = self.notion.databases.query(
                database_id=self.database_id,
                filter={
                    "and": [
                        {
                            "property": "Week Start",
                            "date": {
                                "before": cutoff_date
                            }
                        },
                        {
                            "property": "Status",
                            "select": {
                                "does_not_equal": "Archived"
                            }
                        }
                    ]
                }
            )
            
            return response['results']
            
        except Exception as e:
            print(f"Error querying old pages: {e}")
            return []
    
    def update_page_status(self, page_id: str, status: str = "Archived"):
        """Update page status to archived"""
        try:
            self.notion.pages.update(
                page_id=page_id,
                properties={
                    "Status": {
                        "select": {
                            "name": status
                        }
                    }
                }
            )
            print(f"Updated page {page_id} status to {status}")
            
        except Exception as e:
            print(f"Error updating page {page_id}: {e}")
    
    def archive_old_menus(self):
        """Archive old menu pages"""
        old_pages = self.get_previous_week_pages()
        
        if not old_pages:
            print("No old pages found to archive")
            return
        
        print(f"Found {len(old_pages)} old pages to archive")
        
        for page in old_pages:
            page_id = page['id']
            # Get week start for logging
            week_start = page['properties'].get('Week Start', {}).get('date', {}).get('start', 'Unknown')
            print(f"Archiving page for week {week_start}")
            
            self.update_page_status(page_id, "Archived")
        
        print(f"Successfully archived {len(old_pages)} old menu pages")


def main():
    """Main function to archive old menu pages"""
    try:
        archiver = NotionArchiver()
        archiver.archive_old_menus()
        
    except Exception as e:
        print(f"Error archiving old menus: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()