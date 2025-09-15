"""
Schema definitions for intake.json file structure.
This defines the structure of data collected from Dify Slack conversations.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date


class IntakeData(BaseModel):
    """Main intake data structure collected from Slack conversation via Dify"""
    
    # Required fields
    week_start: date = Field(..., description="Start date of the week (Monday)")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this intake was created")
    
    # User preferences (collected via conversation)
    days_needed: int = Field(default=7, ge=1, le=7, description="Number of days to generate meals for")
    away_days: List[int] = Field(default=[], description="Days when no meals needed (0=Monday, 6=Sunday)")
    avoid_ingredients: List[str] = Field(default=[], description="Ingredients to avoid")
    max_cooking_time: int = Field(default=60, ge=10, le=180, description="Maximum cooking time in minutes")
    
    # Recipe preferences
    priority_recipe_sites: List[str] = Field(
        default=["cookpad.com", "kurashiru.com", "recipe.rakuten.co.jp"],
        description="Preferred recipe sites in order of priority"
    )
    cuisine_preferences: List[str] = Field(
        default=["和食", "洋食", "中華"],
        description="Preferred cuisine types"
    )
    dietary_restrictions: List[str] = Field(
        default=[],
        description="Dietary restrictions (vegetarian, vegan, gluten-free, etc.)"
    )
    
    # Optional fields
    memo: Optional[str] = Field(None, description="Additional notes or special requests")
    guests_expected: int = Field(default=0, ge=0, description="Number of additional guests expected")
    special_occasions: List[str] = Field(default=[], description="Special occasions during the week")
    
    # Metadata
    user_id: Optional[str] = Field(None, description="Slack user ID who provided this intake")
    conversation_id: Optional[str] = Field(None, description="Dify conversation ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class DifySlotData(BaseModel):
    """Structure for managing conversation slots in Dify"""
    
    slot_name: str
    slot_value: Any
    is_filled: bool
    prompt_text: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None


# Example intake.json structure for documentation
EXAMPLE_INTAKE = {
    "week_start": "2024-01-15",
    "timestamp": "2024-01-14T10:30:00+09:00",
    "days_needed": 5,
    "away_days": [5, 6],  # Saturday and Sunday
    "avoid_ingredients": ["エビ", "カニ"],
    "max_cooking_time": 45,
    "priority_recipe_sites": [
        "cookpad.com",
        "kurashiru.com"
    ],
    "cuisine_preferences": ["和食", "洋食"],
    "dietary_restrictions": [],
    "memo": "今週は残業が多いので、簡単に作れるものでお願いします",
    "guests_expected": 0,
    "special_occasions": [],
    "user_id": "U123456789",
    "conversation_id": "conv_abc123"
}