
try:
    print("Attempting to import app from app.main...")
    import sys
    import os
    # Add app directory to path
    sys.path.append(os.path.join(os.getcwd(), "app"))
    from app.main import app
    print("Import successful!")
    print("Checking routes...")
    for route in app.routes:
        print(f"Route: {route.path} - Methods: {route.methods}")
except Exception as e:
    import traceback
    print("Import failed with exception:")
    traceback.print_exc()
