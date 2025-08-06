"""
Setup script to ensure the project structure is correct
"""

import os
import sys
import logging

def setup_project_structure():
    """Set up the project structure"""
    # Get the root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create logs directory
    logs_dir = os.path.join(root_dir, 'logs')
    if not os.path.exists(logs_dir):
        print(f"Creating logs directory: {logs_dir}")
        os.makedirs(logs_dir)
    else:
        print(f"Logs directory already exists: {logs_dir}")
    
    # Create cache directory
    cache_dir = os.path.join(root_dir, 'data', 'cache')
    if not os.path.exists(cache_dir):
        print(f"Creating cache directory: {cache_dir}")
        os.makedirs(cache_dir)
    else:
        print(f"Cache directory already exists: {cache_dir}")
    
    # Configure basic logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': os.path.join(logs_dir, 'darkbot.log'),
                'formatter': 'standard',
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
            },
        },
        'loggers': {
            '': {
                'handlers': ['file', 'console'],
                'level': 'INFO',
                'propagate': True
            },
            'SneakerBot': {
                'handlers': ['file', 'console'],
                'level': 'INFO',
                'propagate': False
            },
        }
    }
    
    # Write the logging config to a file
    import json
    with open(os.path.join(root_dir, 'logging_config.json'), 'w') as f:
        json.dump(logging_config, f, indent=4)
    
    print("Project structure setup complete!")
    
if __name__ == "__main__":
    setup_project_structure()
