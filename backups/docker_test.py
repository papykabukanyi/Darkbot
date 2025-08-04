"""
Docker testing script to validate the imports.
This simulates the Docker environment where the error occurred.
"""

import os
import sys

def simulate_docker_import():
    """
    Simulate the import pattern that's failing in Docker.
    """
    print("Simulating Docker import sequence...")
    
    try:
        # This is the import sequence from the error message
        print("from scrapers.factory import get_scraper_for_site")
        from scrapers.factory import get_scraper_for_site
        print("SUCCESS: imported get_scraper_for_site")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Add the current directory to the path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Run the test
    simulate_docker_import()
    
    print("\nTest completed!")
