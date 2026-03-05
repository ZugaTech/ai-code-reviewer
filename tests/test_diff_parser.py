import pytest
import os
from src.diff_parser import parse_diff

def test_parse_diff():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sample.diff")
    with open(fixture_path, "r", encoding="utf-8") as f:
        diff_content = f.read()

    files = parse_diff(diff_content, exclude_patterns=["*.md"])
    
    assert len(files) == 1
    assert files[0]["filename"] == "src/main.py"
    assert files[0]["language"] == "py"
    
    hunks = files[0]["hunks"]
    assert len(hunks) == 1
    
    lines = hunks[0]["lines"]
    added_lines = [l for l in lines if l["type"] == "added"]
    assert len(added_lines) == 2
    assert added_lines[0]["content"] == '    print("Hello World")'
