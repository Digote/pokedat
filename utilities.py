"""
Utilities module for text processing.

This module provides helper functions for converting between binary data and text strings,
with options for character remapping and configuration.
"""
from typing import Iterable, List, Optional

from text_file import TextFile


def get_strings(data: bytes, config=None, remap_characters: bool = False) -> Optional[List[str]]:
    """
    Extract strings from binary data.
    
    Args:
        data (bytes): Binary data to extract strings from
        config (dict, optional): Configuration parameters for text extraction
        remap_characters (bool, optional): Whether to apply character remapping
        
    Returns:
        list: Extracted text lines or None if extraction fails
    """
    try:
        return TextFile(data, config, remap_characters).lines
    except Exception:
        return None


def get_bytes(lines: Iterable[str], flags: Iterable[int], config=None, remap_characters: bool = False) -> bytes:
    """
    Convert lines and flags to binary data.
    
    Args:
        lines (list): List of text strings
        flags (list): Associated flags for each line
        config (dict, optional): Configuration parameters for text conversion
        remap_characters (bool, optional): Whether to apply character remapping
        
    Returns:
        bytes: Binary representation of the text
    """
    return bytes(TextFile.from_lines(lines, flags, config, remap_characters).data)