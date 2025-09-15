"""
Tests for menu generation functionality
"""

import pytest
import json
import yaml
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import date

# Mock OpenAI to avoid API calls during testing
sys_path = Path(__file__).parent.parent
sys.path.insert(0, str(sys_path))

from scripts.generate_menu import MenuGenerator


class TestMenuGenerator:
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration data"""
        return {
            'default_settings': {
                'days_needed': 7,
                'away_days': [],
                'avoid_ingredients': [],
                'max_cooking_time': 60,
                'priority_recipe_sites': ['cookpad.com'],
                'dietary_preferences': []
            }
        }
    
    @pytest.fixture
    def mock_intake_data(self):
        """Mock intake data"""
        return {
            'week_start': '2024-01-15',
            'days_needed': 5,
            'away_days': [5, 6],
            'avoid_ingredients': ['エビ'],
            'max_cooking_time': 30,
            'priority_recipe_sites': ['cookpad.com', 'kurashiru.com'],
            'dietary_restrictions': [],
            'memo': 'テスト用メモ'
        }
    
    @patch('scripts.generate_menu.Path')
    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_config(self, mock_yaml_load, mock_open, mock_path, mock_config):
        """Test configuration loading"""
        mock_path.return_value.exists.return_value = True
        mock_yaml_load.return_value = mock_config
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            generator = MenuGenerator()
            assert generator.config == mock_config
    
    @patch('scripts.generate_menu.Path')
    @patch('builtins.open')
    @patch('json.load')
    @patch('yaml.safe_load')
    def test_load_intake_data(self, mock_yaml_load, mock_json_load, mock_open, mock_path, mock_config, mock_intake_data):
        """Test intake data loading"""
        # Mock config loading
        mock_path.return_value.exists.side_effect = lambda: True
        mock_yaml_load.return_value = mock_config
        mock_json_load.return_value = mock_intake_data
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            generator = MenuGenerator()
            assert generator.intake_data is not None
            assert generator.intake_data.days_needed == 5
    
    @patch('scripts.generate_menu.Path')
    @patch('yaml.safe_load')
    def test_get_menu_settings_with_intake(self, mock_yaml_load, mock_path, mock_config):
        """Test menu settings generation with intake data"""
        mock_path.return_value.exists.return_value = True
        mock_yaml_load.return_value = mock_config
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            generator = MenuGenerator()
            
            # Mock intake data
            mock_intake = Mock()
            mock_intake.days_needed = 5
            mock_intake.away_days = [5, 6]
            mock_intake.avoid_ingredients = ['エビ']
            mock_intake.max_cooking_time = 30
            mock_intake.priority_recipe_sites = ['cookpad.com']
            mock_intake.dietary_restrictions = []
            mock_intake.memo = 'テスト'
            mock_intake.guests_expected = 2
            mock_intake.special_occasions = []
            
            generator.intake_data = mock_intake
            
            settings = generator.get_menu_settings()
            
            assert settings['days_needed'] == 5
            assert settings['away_days'] == [5, 6]
            assert settings['avoid_ingredients'] == ['エビ']
            assert settings['special_memo'] == 'テスト'
            assert settings['guests_expected'] == 2
    
    @patch('scripts.generate_menu.Path')
    @patch('yaml.safe_load')
    def test_get_menu_settings_defaults_only(self, mock_yaml_load, mock_path, mock_config):
        """Test menu settings with defaults only (no intake)"""
        mock_path.return_value.exists.return_value = True
        mock_yaml_load.return_value = mock_config
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            generator = MenuGenerator()
            generator.intake_data = None
            
            settings = generator.get_menu_settings()
            
            assert settings['days_needed'] == 7
            assert settings['away_days'] == []
            assert settings['avoid_ingredients'] == []
    
    @patch('scripts.generate_menu.Path')
    @patch('yaml.safe_load')
    def test_create_menu_prompt(self, mock_yaml_load, mock_path, mock_config):
        """Test menu prompt creation"""
        mock_path.return_value.exists.return_value = True
        mock_yaml_load.return_value = mock_config
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            generator = MenuGenerator()
            generator.intake_data = None
            
            settings = {
                'days_needed': 5,
                'away_days': [5, 6],
                'avoid_ingredients': ['エビ'],
                'max_cooking_time': 30,
                'priority_recipe_sites': ['cookpad.com'],
                'dietary_preferences': []
            }
            
            prompt = generator.create_menu_prompt(settings)
            
            assert '必要日数: 5日分' in prompt
            assert 'エビ' in prompt
            assert '30分' in prompt
            assert 'cookpad.com' in prompt
    
    @patch('scripts.generate_menu.Path')
    @patch('yaml.safe_load')
    @patch('scripts.generate_menu.OpenAI')
    def test_generate_menu_api_call(self, mock_openai_class, mock_yaml_load, mock_path, mock_config):
        """Test OpenAI API call for menu generation"""
        mock_path.return_value.exists.return_value = True
        mock_yaml_load.return_value = mock_config
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated menu content"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            generator = MenuGenerator()
            generator.intake_data = None
            
            result = generator.generate_menu()
            
            assert result == "Generated menu content"
            mock_client.chat.completions.create.assert_called_once()


def test_day_name_conversion():
    """Test day index to Japanese name conversion"""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
        with patch('scripts.generate_menu.MenuGenerator.load_config'):
            with patch('scripts.generate_menu.MenuGenerator.load_intake_data'):
                generator = MenuGenerator()
                
                assert generator.day_name(0) == '月曜日'
                assert generator.day_name(6) == '日曜日'


if __name__ == "__main__":
    # Run basic tests without pytest
    print("Running basic functionality tests...")
    
    # Test day name conversion
    test_day_name_conversion()
    
    print("Basic tests completed!")