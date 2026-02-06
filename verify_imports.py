import sys
import os

# Add parent dir to sys.path to allow 'app' import
sys.path.append(os.getcwd())

print("Attempting to import app.main...")
try:
    from app import main
    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
