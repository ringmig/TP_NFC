#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Tests for main application functionality.
'''
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import load_config, main


class TestMain(unittest.TestCase):
    """Test cases for main application functionality."""
    
    @patch('builtins.open')
    @patch('json.load')
    def test_load_config(self, mock_json_load, mock_open):
        """Test loading configuration."""
        # Setup mock
        mock_config = {"app_name": "test", "version": "0.1.0"}
        mock_json_load.return_value = mock_config
        
        # Call function
        result = load_config()
        
        # Assert
        self.assertEqual(result, mock_config)
        mock_open.assert_called_once()
        mock_json_load.assert_called_once()
    
    @patch('src.main.load_config')
    @patch('src.main.setup_logger')
    def test_main_success(self, mock_setup_logger, mock_load_config):
        """Test main function success path."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger
        mock_load_config.return_value = {
            "app_name": "test",
            "version": "0.1.0",
            "log_level": "INFO",
            "log_file": "logs/test.log",
            "settings": {}
        }
        
        # Call function
        result = main()
        
        # Assert
        self.assertEqual(result, 0)
        mock_logger.info.assert_called()


if __name__ == "__main__":
    unittest.main()
