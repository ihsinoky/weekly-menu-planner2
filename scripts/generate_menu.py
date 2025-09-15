"""
Generate weekly menu using OpenAI API based on intake.json and rules.yaml
"""

import os
import sys
import json
import yaml
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional

from openai import OpenAI
from schemas.intake_schema import IntakeData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class MenuGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4')  # Default to gpt-4 if not specified
        self.config = self.load_config()
        self.intake_data = self.load_intake_data()
        
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
        
    def load_config(self) -> Dict:
        """Load default rules from yaml file"""
        config_path = Path('config/rules.yaml')
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def load_intake_data(self) -> Optional[IntakeData]:
        """Load intake data if available"""
        intake_path = Path('data/intake.json')
        if not intake_path.exists():
            print("No intake.json found, using default rules only")
            return None
            
        try:
            with open(intake_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return IntakeData(**data)
        except Exception as e:
            print(f"Error loading intake data: {e}")
            return None
    
    def get_menu_settings(self) -> Dict:
        """Merge default settings with intake data"""
        settings = self.config['default_settings'].copy()
        
        if self.intake_data:
            # Override with intake data where available
            settings['days_needed'] = self.intake_data.days_needed
            settings['away_days'] = self.intake_data.away_days
            settings['avoid_ingredients'] = self.intake_data.avoid_ingredients
            settings['max_cooking_time'] = self.intake_data.max_cooking_time
            settings['priority_recipe_sites'] = self.intake_data.priority_recipe_sites
            settings['dietary_preferences'] = self.intake_data.dietary_restrictions
            
            # Add intake-specific fields
            if self.intake_data.memo:
                settings['special_memo'] = self.intake_data.memo
            if self.intake_data.guests_expected > 0:
                settings['guests_expected'] = self.intake_data.guests_expected
            if self.intake_data.special_occasions:
                settings['special_occasions'] = self.intake_data.special_occasions
                
        return settings
    
    def get_week_start(self) -> date:
        """Get the start date of the week to generate menu for"""
        if self.intake_data and self.intake_data.week_start:
            return self.intake_data.week_start
        
        # Default to current week's Monday
        today = datetime.now().date()
        days_back = today.weekday()
        return today - timedelta(days=days_back)
    
    def create_menu_prompt(self, settings: Dict) -> str:
        """Create prompt for OpenAI to generate weekly menu"""
        week_start = self.get_week_start()
        
        prompt = f"""
あなたは日本の家庭料理の献立プランナーです。{week_start.strftime('%Y年%m月%d日')}（月曜日）から始まる週の夕食献立を作成してください。

## 条件:
- 必要日数: {settings['days_needed']}日分
- 外泊日: {[self.day_name(d) for d in settings['away_days']] if settings['away_days'] else 'なし'}
- 避けたい食材: {', '.join(settings['avoid_ingredients']) if settings['avoid_ingredients'] else 'なし'}
- 最大調理時間: {settings['max_cooking_time']}分
- 優先レシピサイト: {', '.join(settings['priority_recipe_sites'][:3])}
"""

        if settings.get('dietary_preferences'):
            prompt += f"- 食事制限: {', '.join(settings['dietary_preferences'])}\n"
        
        if settings.get('special_memo'):
            prompt += f"- 特記事項: {settings['special_memo']}\n"
            
        if settings.get('guests_expected', 0) > 0:
            prompt += f"- 来客予定: {settings['guests_expected']}名\n"

        prompt += f"""
## 要求事項:
1. 月曜日から日曜日までの7日間で表示
2. 外泊日は「外食・外泊」と表示
3. 必要日数が7日未満の場合、残りの日は「お休み」と表示
4. 各料理に調理時間（分）を記載
5. 栄養バランスを考慮し、連日同じような料理は避ける
6. 日本の一般的な家庭料理を中心に
7. 可能な範囲で指定レシピサイトで見つかりそうな料理を選ぶ

## 出力形式:
```
### {week_start.strftime('%Y年%m月%d日')}週の夕食献立

**月曜日 ({(week_start).strftime('%m/%d')})**
- 料理名 (調理時間: XX分)

**火曜日 ({(week_start + timedelta(days=1)).strftime('%m/%d')})**
- 料理名 (調理時間: XX分)

[以下同様に日曜日まで]
```

栄養バランスとバラエティを重視し、美味しそうな献立を作成してください。
"""
        
        return prompt
    
    def day_name(self, day_index: int) -> str:
        """Convert day index to Japanese day name"""
        days = ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日']
        return days[day_index]
    
    def generate_menu(self) -> str:
        """Generate weekly menu using OpenAI with retry logic"""
        settings = self.get_menu_settings()
        prompt = self.create_menu_prompt(settings)
        
        def _make_openai_request():
            self.logger.info(f"Generating menu using model: {self.openai_model}")
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "あなたは経験豊富な日本の家庭料理の献立プランナーです。バランスの取れた美味しい献立を作成することが得意です。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7,
                timeout=30  # 30 second timeout
            )
            return response.choices[0].message.content
        
        try:
            return self._retry_with_backoff(_make_openai_request, max_retries=3, base_delay=2)
        except Exception as e:
            self.logger.error(f"Failed to generate menu after all retries: {e}")
            self.logger.error(f"Model used: {self.openai_model}")
            self.logger.error(f"Prompt length: {len(prompt)} characters")
            raise
    
    def save_menu_data(self, menu_content: str):
        """Save generated menu data for Notion integration"""
        week_start = self.get_week_start()
        settings = self.get_menu_settings()
        
        menu_data = {
            'week_start': week_start.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'menu_content': menu_content,
            'settings_used': settings,
            'intake_data_available': self.intake_data is not None
        }
        
        output_path = Path('data/generated_menu.json')
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(menu_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"Menu data saved to {output_path}")


def main():
    """Main function to generate weekly menu"""
    try:
        generator = MenuGenerator()
        print("Generating weekly menu...")
        
        menu_content = generator.generate_menu()
        print("Menu generated successfully")
        
        # Save the generated menu
        generator.save_menu_data(menu_content)
        
        print("\nGenerated Menu:")
        print("=" * 50)
        print(menu_content)
        print("=" * 50)
        
    except Exception as e:
        print(f"Error generating menu: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()