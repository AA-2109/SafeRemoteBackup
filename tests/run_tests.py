import os
import sys
import subprocess
import webbrowser
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tests.visualization.test_visualizer import TestDataVisualizer

def run_tests():
    """Run tests with coverage reporting and visualization."""
    # Create coverage directory if it doesn't exist
    coverage_dir = Path("coverage_html")
    coverage_dir.mkdir(exist_ok=True)
    
    # Run tests with coverage
    print("Running tests with coverage...")
    subprocess.run([
        "pytest",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=xml",
        "--cov-report=term-missing",
        "-v",
        "--html=test_report.html",
        "--self-contained-html"
    ])
    
    # Check if tests passed
    if subprocess.run(["pytest", "--cov=app", "--cov-report=term-missing"]).returncode == 0:
        print("\nTests passed successfully!")
        
        # Open coverage report in browser
        coverage_index = coverage_dir / "index.html"
        if coverage_index.exists():
            print(f"\nOpening coverage report in browser...")
            webbrowser.open(f"file://{coverage_index.absolute()}")
        
        # Open test report in browser
        test_report = Path("test_report.html")
        if test_report.exists():
            print(f"Opening test report in browser...")
            webbrowser.open(f"file://{test_report.absolute()}")
        
        # Start visualization server
        print("\nStarting test data visualization server...")
        visualizer = TestDataVisualizer()
        visualizer.run(debug=False, port=8050)
    else:
        print("\nTests failed! Please check the test report for details.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests() 