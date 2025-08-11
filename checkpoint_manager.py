#!/usr/bin/env python3

import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CheckpointManager:
    def __init__(self, checkpoint_file: str = "discovery_checkpoint.json"):
        self.checkpoint_file = Path(checkpoint_file)
        self._lock = threading.Lock()
    
    def save_checkpoint(self, state: Dict[str, Any]):
        with self._lock:
            try:
                with open(self.checkpoint_file, 'w') as f:
                    json.dump({
                        **state,
                        'timestamp': datetime.now().isoformat(),
                        'version': '1.0'
                    }, f, indent=2, default=str)
                logger.info(f"Checkpoint saved: {self.checkpoint_file}")
            except Exception as e:
                logger.error(f"Failed to save checkpoint: {e}")
    
    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        if not self.checkpoint_file.exists():
            return None
        
        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            
            checkpoint_time = datetime.fromisoformat(checkpoint.get('timestamp', '1970-01-01'))
            if datetime.now() - checkpoint_time > timedelta(hours=24):
                logger.warning("Checkpoint is older than 24 hours, starting fresh")
                return None
            
            logger.info(f"Loaded checkpoint from {checkpoint['timestamp']}")
            return checkpoint
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def clear_checkpoint(self):
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()