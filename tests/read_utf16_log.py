import sys

try:
    with open("server_debug.log", "r", encoding="utf-16-le") as f:
        print(f.read())
except Exception as e:
    print(f"Error: {e}")
