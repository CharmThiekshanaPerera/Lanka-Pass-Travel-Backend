
import subprocess
import os
import time

# Absolute path to backend
backend_dir = r"C:\Users\amjad\OneDrive\Documents\Custom Office Templates\OneDrive\Desktop\Phyxle\Lanka-Pass-Travel-Backend"

# Set environment variables
env = os.environ.copy()
env["PYTHONPATH"] = backend_dir

print(f"Starting server in {backend_dir}...")
with open(os.path.join(os.getcwd(), "startup_test_v2.log"), "w") as f:
    process = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--port", "8001"],
        cwd=backend_dir,
        stdout=f,
        stderr=subprocess.STDOUT,
        env=env
    )
    
    # Wait a bit
    time.sleep(5)
    process.terminate()

print("Server test complete. Check startup_test_v2.log")
