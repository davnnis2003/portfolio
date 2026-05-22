import os
from dotenv import load_dotenv

def init_env():
    """
    Attempts to load environment variables from the project root or the docker/ directory.
    """
    # 1. Try project root
    root_env = os.path.join(os.getcwd(), ".env")
    if os.path.exists(root_env):
        load_dotenv(root_env)
        return

    # 2. Try docker/ directory (useful if files were moved)
    # Check relative to this file's parent's parent (assuming src/utils/env_loader.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    docker_env = os.path.join(script_dir, "../../docker/.env")
    
    if os.path.exists(docker_env):
        load_dotenv(docker_env)
    else:
        # Fallback to standard load_dotenv() search
        load_dotenv()
