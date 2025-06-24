#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Various helper functions for the application.
'''


def is_valid_input(value, min_value=None, max_value=None):
    """
    Validate if a value is within specified range.
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        
    Returns:
        bool: True if valid, False otherwise
    """
    if min_value is not None and value < min_value:
        return False
    if max_value is not None and value > max_value:
        return False
    return True


def format_output(data, format_type="json"):
    """
    Format data for output.
    
    Args:
        data: Data to format
        format_type: Output format (json, text, etc.)
        
    Returns:
        str: Formatted output
    """
    if format_type == "json":
        import json
        return json.dumps(data, indent=4)
    elif format_type == "text":
        return str(data)
    else:
        return data
