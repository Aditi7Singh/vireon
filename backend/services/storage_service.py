import os
import uuid
from typing import Optional

UPLOADS_DIR = "backend/data/uploads"

class SimpleStorage:
    """Mock cloud storage implementation (Local File System)"""
    
    def __init__(self):
        if not os.path.exists(UPLOADS_DIR):
            os.makedirs(UPLOADS_DIR)
            
    def save_file(self, content: bytes, filename: str) -> str:
        """Saves file and returns a mock cloud URL/path"""
        safe_name = f"{uuid.uuid4()}_{filename}"
        path = os.path.join(UPLOADS_DIR, safe_name)
        with open(path, "wb") as f:
            f.write(content)
        return f"storage://vireon-docs/{safe_name}"

storage = SimpleStorage()
