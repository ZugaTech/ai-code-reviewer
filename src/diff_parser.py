import re
import fnmatch
from typing import List, Dict, Any

def match_exclude_pattern(filename: str, patterns: List[str]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(filename, pattern):
            return True
    return False

def get_language(filename: str) -> str:
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    return ext

def parse_diff(raw_diff: str, exclude_patterns: List[str]) -> List[Dict[str, Any]]:
    files = []
    current_file = None
    current_hunk = None
    
    lines = raw_diff.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line.startswith("diff --git"):
            if current_file and not match_exclude_pattern(current_file["filename"], exclude_patterns):
                files.append(current_file)
            
            parts = line.split(" ")
            filename = parts[-1][2:] if parts[-1].startswith("b/") else parts[-1]
            
            # Check binary
            is_binary = False
            
            current_file = {
                "filename": filename,
                "language": get_language(filename),
                "hunks": []
            }
            current_hunk = None
            
            while i + 1 < len(lines) and not lines[i+1].startswith("@@ ") and not lines[i+1].startswith("diff --git"):
                i += 1
                if "Binary files" in lines[i]:
                    is_binary = True
                    break
                    
            if is_binary:
                current_file = None # Skip binary
                
        elif line.startswith("@@ ") and current_file:
            header_match = re.search(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if header_match:
                old_start = int(header_match.group(1))
                new_start = int(header_match.group(2))
                current_hunk = {
                    "hunk_header": line,
                    "lines": [],
                    "new_start": new_start,
                    "old_start": old_start
                }
                current_file["hunks"].append(current_hunk)
                
        elif current_hunk:
            if line.startswith("\\ No newline"):
                pass
            elif line.startswith("+"):
                current_hunk["lines"].append({
                    "type": "added",
                    "line_number_old": None,
                    "line_number_new": current_hunk["new_start"],
                    "content": line[1:]
                })
                current_hunk["new_start"] += 1
            elif line.startswith("-"):
                current_hunk["lines"].append({
                    "type": "removed",
                    "line_number_old": current_hunk["old_start"],
                    "line_number_new": None,
                    "content": line[1:]
                })
                current_hunk["old_start"] += 1
            elif line.startswith(" "):
                current_hunk["lines"].append({
                    "type": "context",
                    "line_number_old": current_hunk["old_start"],
                    "line_number_new": current_hunk["new_start"],
                    "content": line[1:]
                })
                current_hunk["old_start"] += 1
                current_hunk["new_start"] += 1
                
        i += 1
        
    if current_file and not match_exclude_pattern(current_file["filename"], exclude_patterns):
        files.append(current_file)
        
    return files
