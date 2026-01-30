try:
    with open("server_debug.log", "r", encoding="utf-16-le") as f:
        content = f.read()
except Exception:
    with open("server_debug.log", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

print(f"File Size: {len(content)}")
print("--- BEGIN CONTENT ---")
print(content[:1000])
print("--- END CONTENT ---")
