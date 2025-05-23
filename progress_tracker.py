#!/usr/bin/env python3
"""
Progress tracking utilities for long-running operations.
This module provides a ProgressTracker class to track progress of operations
and log updates at appropriate intervals.
"""

import time
import logging
from datetime import datetime
from typing import Optional, Callable

class ProgressTracker:
    """
    Tracks progress of long-running operations and provides logging utilities.
    
    This class encapsulates progress tracking logic, including:
    - Counting processed items
    - Calculating processing rate
    - Estimating remaining time
    - Logging progress at appropriate intervals
    
    It follows the Single Responsibility Principle by handling only progress
    tracking concerns.
    """
    
    def __init__(self, logger=None, name: str = "default"):
        """
        Initialize a new progress tracker.
        
        Args:
            logger: Logger instance to use (if None, creates a new one)
            name: Name to identify this tracker instance
        """
        self.progress_count = 0
        self.start_time = None
        self.last_log_time = None
        self.name = name
        
        # Use provided logger or create a new one
        self.logger = logger or logging.getLogger(f"progress_tracker.{name}")
    
    def reset(self):
        """Reset the progress counter and timer."""
        self.progress_count = 0
        self.start_time = None
        self.last_log_time = None
    
    def update(self, increment: int = 1, total: Optional[int] = None, 
               interval: int = 30, force_log: bool = False) -> int:
        """
        Update progress count and log progress if appropriate.
        
        Args:
            increment: Number of items to add to the progress count
            total: Total number of items (for percentage calculation)
            interval: Minimum seconds between log entries
            force_log: If True, log regardless of interval
            
        Returns:
            Current progress count
        """
        # Update progress count
        self.progress_count += increment
        
        # Initialize start_time on first call
        current_time = time.time()
        if self.start_time is None:
            self.start_time = current_time
            self.last_log_time = current_time
        
        # Determine if we should log based on interval
        should_log = force_log or self.last_log_time is None or \
                   (current_time - self.last_log_time) >= interval
        
        if should_log:
            self._log_progress(total)
            self.last_log_time = current_time
            
        return self.progress_count
    
    def _log_progress(self, total: Optional[int] = None):
        """
        Log current progress with rate and time information.
        
        Args:
            total: Total number of items (for percentage calculation)
        """
        if self.start_time is None:
            return
            
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Calculate items per second
        rate = self.progress_count / elapsed if elapsed > 0 else 0
        
        # Format as HH:MM:SS
        elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed))
        
        # Log with percentage if total is known
        if total:
            percentage = (self.progress_count / total) * 100
            self.logger.info(
                f"Progress: {self.progress_count}/{total} ({percentage:.1f}%) | "
                f"Rate: {rate:.2f} items/sec | Elapsed: {elapsed_str}"
            )
            
            # Estimate remaining time if total is known
            if rate > 0:
                remaining_items = total - self.progress_count
                estimated_seconds = remaining_items / rate
                remaining_str = time.strftime('%H:%M:%S', time.gmtime(estimated_seconds))
                self.logger.info(f"Estimated time remaining: {remaining_str}")
        else:
            self.logger.info(
                f"Progress: {self.progress_count} items | "
                f"Rate: {rate:.2f} items/sec | Elapsed: {elapsed_str}"
            )

    @property
    def elapsed_seconds(self) -> float:
        """Get the elapsed time in seconds."""
        if self.start_time is None:
            return 0
        return time.time() - self.start_time
    
    @property 
    def items_per_second(self) -> float:
        """Calculate the current processing rate."""
        if self.start_time is None or self.elapsed_seconds == 0:
            return 0
        return self.progress_count / self.elapsed_seconds
