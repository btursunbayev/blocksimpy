#!/usr/bin/env python3
import os
import re

def fix_file(filepath):
    """Fix common formatting issues in Python files."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove trailing whitespace from all lines
        content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
        
        # Remove whitespace from blank lines
        content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)
        
        # Ensure file ends with exactly one newline
        content = content.rstrip() + '\n'
        
        # Write back if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Process all Python files in src directory."""
    fixed_count = 0
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    fixed_count += 1
    
    print(f"Fixed {fixed_count} files")

if __name__ == '__main__':
    main()
