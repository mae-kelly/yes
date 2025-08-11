#!/usr/bin/env python3

import signal
import logging

logger = logging.getLogger(__name__)

class SignalHandler:
    def __init__(self):
        self.shutdown_requested = False
        self.checkpoint_requested = False
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        if hasattr(signal, 'SIGUSR1'):
            signal.signal(signal.SIGUSR1, self._checkpoint_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, requesting graceful shutdown...")
        self.shutdown_requested = True
    
    def _checkpoint_handler(self, signum, frame):
        logger.info("Received checkpoint signal")
        self.checkpoint_requested = True