import sys

try:
    with open('debug_output.txt', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        # Filter to printable ASCII
        safe_content = "".join(c if ord(c) < 128 else "?" for c in content)
        print(safe_content)
except Exception as e:
    print(f"Error reading log: {e}")
