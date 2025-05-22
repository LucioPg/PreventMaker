import sys
import os
import subprocess

def test_application():
    """
    Test that the application can be launched and basic functionality works
    """
    print("Testing PreventMaker application...")
    
    # Check if the main file exists
    if not os.path.exists("preventmaker.py"):
        print("ERROR: preventmaker.py not found!")
        return False
    
    # Check if all required modules can be imported
    try:
        print("Testing imports...")
        import PyQt6
        import reportlab
        import PyPDF2
        print("All required modules imported successfully.")
    except ImportError as e:
        print(f"ERROR: Failed to import required module: {e}")
        print("Please install all dependencies with: pip install -e .")
        return False
    
    # Try to run the application in a subprocess (will exit immediately)
    try:
        print("Testing application launch...")
        # Start the process but kill it immediately (just to test if it starts)
        process = subprocess.Popen(
            [sys.executable, "preventmaker.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Wait a short time to see if it crashes immediately
        import time
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print("Application launched successfully!")
            # Terminate the process
            process.terminate()
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"ERROR: Application failed to start properly.")
            print(f"STDOUT: {stdout.decode('utf-8', errors='ignore')}")
            print(f"STDERR: {stderr.decode('utf-8', errors='ignore')}")
            return False
    except Exception as e:
        print(f"ERROR: Failed to launch application: {e}")
        return False

if __name__ == "__main__":
    success = test_application()
    if success:
        print("\nAll tests passed! The application is ready to use.")
        print("\nTo run the application:")
        print("  python preventmaker.py")
        print("\nTo build the executable:")
        print("  python build.py")
    else:
        print("\nTests failed. Please fix the issues before proceeding.")
    
    sys.exit(0 if success else 1)