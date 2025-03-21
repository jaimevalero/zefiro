import json
import time
import os
from pathlib import Path
from loguru import logger
from threading import Lock

class AuthStore:
    """Simple file-based authentication store with TTL"""
    
    def __init__(self, ttl_hours=24):
        self.auth_file = "/tmp/auth_store.json"
        self.ttl_seconds = ttl_hours * 3600
        self.lock = Lock()
        self._init_store()
    
    def _init_store(self):
        """Initialize the store if it doesn't exist"""
        with self.lock:
            if not os.path.exists(self.auth_file):
                self._save_store({})
    
    def _load_store(self):
        """Load the store from file"""
        try:
            with open(self.auth_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading auth store: {e}")
            return {}
    
    def _save_store(self, data):
        """Save the store to file"""
        with open(self.auth_file, 'w') as f:
            json.dump(data, f)
    
    def add_auth(self, uuid: str, user_id: str):
        """Add a new UUID-user_id mapping"""
        with self.lock:
            store = self._load_store()
            store[uuid] = {
                "user_id": user_id,
                "timestamp": time.time()
            }
            self._save_store(store)
    
    def verify_auth(self, uuid: str, user_id: str) -> bool:
        """Verify if a user has access to a UUID"""
        with self.lock:
            store = self._load_store()
            if uuid not in store:
                return False
            
            entry = store[uuid]
            # Check if entry has expired
            if time.time() - entry["timestamp"] > self.ttl_seconds:
                del store[uuid]
                self._save_store(store)
                return False
                
            return entry["user_id"] == user_id
    
    def cleanup(self):
        """Remove expired entries"""
        with self.lock:
            store = self._load_store()
            current_time = time.time()
            store = {
                uuid: data 
                for uuid, data in store.items() 
                if current_time - data["timestamp"] <= self.ttl_seconds
            }
            self._save_store(store)
