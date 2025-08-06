"""
Progress Manager for REST API-based progress updates during document processing.

This module provides a centralized way to send progress updates to the backend
via REST API, which then relays them to the frontend via WebSocket connections.
"""

import logging
import requests
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ProgressManager:
    """
    Manages progress updates for document processing operations.
    
    This class provides a centralized way to track and report progress
    during document ingestion, parsing, and vector storage operations.
    The progress updates are sent to the backend via REST API, which then
    relays them to the frontend via WebSocket connections.
    """

    def __init__(self, backend_url: str, document_id: str, task_id: str):
        """
        Initialize the progress manager.
        
        Args:
            backend_url: URL of the backend API (e.g., "http://localhost:8000")
            document_id: ID of the document being processed
            task_id: ID of the processing task
        """
        self.backend_url = backend_url.rstrip('/')
        self.document_id = document_id
        self.task_id = task_id
        self.start_time = datetime.now()
        self.current_stage = "initialized"
        self.stage_progress = 0.0
        self.total_progress = 0.0
        
        # Stage weights for overall progress calculation
        self.stage_weights = {
            "parsing": 0.2,      # 20% - LLMSherpa parsing
            "chunking": 0.3,     # 30% - Hierarchical chunking
            "embedding": 0.3,    # 30% - Embedding generation
            "storage": 0.2,      # 20% - Vector storage
        }
        
        # Stage start times for duration tracking
        self.stage_start_times: Dict[str, datetime] = {}

    def start_stage(self, stage_name: str) -> None:
        """
        Start a new processing stage.
        
        Args:
            stage_name: Name of the stage being started
        """
        self.current_stage = stage_name
        self.stage_progress = 0.0
        self.stage_start_times[stage_name] = datetime.now()
        
        self._send_progress_update(
            f"Started {stage_name}",
            0,
            100,
            stage_name
        )
        
        logger.info(f"Started stage: {stage_name}")

    def update_stage_progress(self, message: str, current: int, total: int) -> None:
        """
        Update progress within the current stage.
        
        Args:
            message: Progress message
            current: Current item being processed
            total: Total items to process
        """
        if total > 0:
            self.stage_progress = (current / total) * 100
            self._update_total_progress()
        
        self._send_progress_update(
            message,
            current,
            total,
            self.current_stage
        )
        
        logger.info(f"Stage {self.current_stage}: {message} - {current}/{total}")

    def complete_stage(self, stage_name: str) -> None:
        """
        Mark a stage as completed.
        
        Args:
            stage_name: Name of the completed stage
        """
        self.stage_progress = 100.0
        self._update_total_progress()
        
        duration = datetime.now() - self.stage_start_times.get(stage_name, self.start_time)
        
        self._send_progress_update(
            f"Completed {stage_name} in {duration.total_seconds():.1f}s",
            100,
            100,
            stage_name
        )
        
        logger.info(f"Completed stage: {stage_name} in {duration.total_seconds():.1f}s")

    def _update_total_progress(self) -> None:
        """Update the total progress based on stage weights."""
        total_progress = 0.0
        
        # Calculate progress for completed stages
        for stage, weight in self.stage_weights.items():
            if stage in self.stage_start_times:
                if stage == self.current_stage:
                    # Current stage: use current progress
                    total_progress += (self.stage_progress / 100.0) * weight
                else:
                    # Completed stage: full weight
                    total_progress += weight
        
        self.total_progress = total_progress * 100.0

    def _send_progress_update(
        self, 
        message: str, 
        current: int, 
        total: int, 
        stage: str
    ) -> None:
        """
        Send progress update via REST API to backend.
        
        Args:
            message: Progress message
            current: Current progress
            total: Total items
            stage: Current stage
        """
        try:
            # Calculate progress percentage
            progress_percentage = (current / total * 100) if total > 0 else 0
            
            # Prepare progress data for backend
            progress_data = {
                "task_id": self.task_id,
                "document_id": self.document_id,
                "status": "processing",
                "progress": int(progress_percentage),
                "stage": stage,
                "message": message,
                "current": current,
                "total": total,
                "stage_progress": self.stage_progress,
                "total_progress": self.total_progress,
                "chunks": []  # Empty chunks for progress updates
            }
            
            # Send to backend via REST API
            response = requests.post(
                f"{self.backend_url}/worker/status",
                json=progress_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"Progress update sent successfully: {message}")
            else:
                logger.warning(f"Failed to send progress update: {response.status_code} - {response.text}")
            
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")

    def get_progress_callback(self) -> Callable[[str, int, int], None]:
        """
        Get a progress callback function for use with LlamaIndex components.
        
        Returns:
            Callback function that can be passed to CustomHierarchicalNodeParser
            and CustomPineconeVectorStore
        """
        def progress_callback(message: str, current: int, total: int) -> None:
            self.update_stage_progress(message, current, total)
        
        return progress_callback

# Note: send_error and send_completion methods removed - use report_status_to_backend() instead

    def report_status_to_backend(
        self,
        status: str,
        chunks: List[Any] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Report status to backend (replaces the standalone report_status_to_backend function).
        This method handles both progress updates and final status reporting.
        
        Args:
            status: Status to report (processing, completed, failed)
            chunks: List of chunks (for completion)
            error: Error message (for failures)
        """
        try:
            # Include complete progress information for final status updates
            payload = {
                "task_id": self.task_id,
                "document_id": self.document_id,
                "status": status,
                "progress": 100 if status == "completed" else 0,
                "stage": "completed" if status == "completed" else "failed" if status == "failed" else "processing",
                "message": f"Document processing {status}",
                "current": 1 if status in ["completed", "failed"] else 0,
                "total": 1 if status in ["completed", "failed"] else 0,
                "stage_progress": self.stage_progress,
                "total_progress": self.total_progress,
                "chunks": chunks or [],
                "error": error,
            }

            logger.info(f"Reporting status to backend: {status} for document {self.document_id}")

            # Send to backend via REST API
            response = requests.post(
                f"{self.backend_url}/worker/status",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Successfully reported status to backend for document {self.document_id}")
            else:
                logger.warning(f"Backend returned status code {response.status_code} for document {self.document_id}")

        except Exception as e:
            logger.error(f"Failed to report status to backend for document {self.document_id}: {str(e)}")
            # Don't raise here as this shouldn't fail the main task

    def send_final_progress_update(self, status: str, chunks: List[Any] = None, error: Optional[str] = None) -> None:
        """
        Send a final progress update with complete information.
        This ensures the backend receives all progress data for the final status.
        
        Args:
            status: Final status (completed, failed)
            chunks: List of chunks (for completion)
            error: Error message (for failures)
        """
        try:
            # Send a final progress update with 100% completion
            self._send_progress_update(
                message=f"Document processing {status}",
                current=1,
                total=1,
                stage="completed" if status == "completed" else "failed"
            )
            
            # Then send the final status with chunks
            self.report_status_to_backend(status, chunks, error)
            
            logger.info(f"Final progress update sent for document {self.document_id} with status: {status}")
            
        except Exception as e:
            logger.error(f"Failed to send final progress update for document {self.document_id}: {str(e)}")
            # Don't raise here as this shouldn't fail the main task


class ProgressCallback:
    """
    Simple progress callback wrapper for LlamaIndex components.
    
    This class provides a simple interface for progress callbacks
    that can be used with CustomHierarchicalNodeParser and CustomPineconeVectorStore.
    """

    def __init__(self, progress_manager: ProgressManager):
        """
        Initialize with a progress manager.
        
        Args:
            progress_manager: Progress manager instance
        """
        self.progress_manager = progress_manager

    def __call__(self, message: str, current: int, total: int) -> None:
        """
        Call the progress callback.
        
        Args:
            message: Progress message
            current: Current progress
            total: Total items
        """
        self.progress_manager.update_stage_progress(message, current, total) 