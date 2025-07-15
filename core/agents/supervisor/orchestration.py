"""
Supervisor Agent Orchestration

This module provides the orchestration component for the SupervisorAgent,
managing the workflow of supervision tasks and coordinating the supervision process.
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class SupervisorOrchestration:
    """
    Orchestration component for the SupervisorAgent.
    
    Manages the workflow of supervision tasks and coordinates the supervision process,
    including task scheduling, dependency management, and status tracking.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the SupervisorOrchestration component.
        
        Args:
            config (Dict[str, Any], optional): Configuration options
        """
        self.config = config or {}
        
        # Task management
        self.task_queue = []
        self.running_tasks = {}
        self.completed_tasks = {}
        
        # Initialize status tracking
        self.status = {
            "supervision_id": self._generate_supervision_id(),
            "started_at": self.get_current_timestamp(),
            "status": "initialized",
            "tasks_total": 0,
            "tasks_completed": 0,
            "tasks_failed": 0
        }
        
        logger.info("SupervisorOrchestration initialized")
    
    def schedule_task(self, task_type: str, params: Dict[str, Any], priority: int = 1) -> str:
        """
        Schedule a supervision task.
        
        Args:
            task_type (str): Type of task to schedule
            params (Dict[str, Any]): Parameters for the task
            priority (int, optional): Task priority (higher is more important)
            
        Returns:
            str: Task ID
        """
        task_id = self._generate_task_id()
        
        task = {
            "task_id": task_id,
            "task_type": task_type,
            "params": params,
            "priority": priority,
            "status": "pending",
            "scheduled_at": self.get_current_timestamp(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        self.task_queue.append(task)
        self.status["tasks_total"] += 1
        
        # Sort task queue by priority
        self.task_queue.sort(key=lambda t: t["priority"], reverse=True)
        
        logger.info(f"Scheduled {task_type} task with ID {task_id}, priority {priority}")
        return task_id
    
    def start_task(self, task_id: str) -> Dict[str, Any]:
        """
        Start a scheduled task.
        
        Args:
            task_id (str): ID of the task to start
            
        Returns:
            Dict[str, Any]: Task data
        """
        # Find task in queue
        for i, task in enumerate(self.task_queue):
            if task["task_id"] == task_id:
                # Remove from queue and mark as running
                task = self.task_queue.pop(i)
                task["status"] = "running"
                task["started_at"] = self.get_current_timestamp()
                self.running_tasks[task_id] = task
                
                logger.info(f"Started task {task_id} ({task['task_type']})")
                return task
        
        logger.warning(f"Task {task_id} not found in queue")
        return None
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """
        Get the next task from the queue based on priority.
        
        Returns:
            Optional[Dict[str, Any]]: Next task or None if queue is empty
        """
        if not self.task_queue:
            return None
        
        # Get highest priority task
        task = self.task_queue[0]
        return self.start_task(task["task_id"])
    
    def complete_task(self, task_id: str, result: Any, status: str = "completed") -> bool:
        """
        Mark a task as completed.
        
        Args:
            task_id (str): ID of the task
            result (Any): Result of the task
            status (str, optional): Final status (completed or failed)
            
        Returns:
            bool: Success status
        """
        if task_id not in self.running_tasks:
            logger.warning(f"Cannot complete non-running task {task_id}")
            return False
        
        # Update task data
        task = self.running_tasks.pop(task_id)
        task["status"] = status
        task["completed_at"] = self.get_current_timestamp()
        task["result"] = result
        
        # Add to completed tasks
        self.completed_tasks[task_id] = task
        
        # Update supervision status
        if status == "completed":
            self.status["tasks_completed"] += 1
        else:
            self.status["tasks_failed"] += 1
        
        logger.info(f"Completed task {task_id} with status {status}")
        return True
    
    def fail_task(self, task_id: str, error: Any) -> bool:
        """
        Mark a task as failed.
        
        Args:
            task_id (str): ID of the task
            error (Any): Error information
            
        Returns:
            bool: Success status
        """
        if task_id not in self.running_tasks:
            logger.warning(f"Cannot fail non-running task {task_id}")
            return False
        
        # Update task data
        task = self.running_tasks.pop(task_id)
        task["status"] = "failed"
        task["completed_at"] = self.get_current_timestamp()
        task["error"] = error
        
        # Add to completed tasks
        self.completed_tasks[task_id] = task
        
        # Update supervision status
        self.status["tasks_failed"] += 1
        
        logger.info(f"Failed task {task_id}: {error}")
        return True
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a task.
        
        Args:
            task_id (str): ID of the task
            
        Returns:
            Optional[Dict[str, Any]]: Task status or None if not found
        """
        # Check in all possible states
        for task_dict in [self.task_queue, self.running_tasks, self.completed_tasks]:
            if isinstance(task_dict, list):
                for task in task_dict:
                    if task["task_id"] == task_id:
                        return task
            elif task_id in task_dict:
                return task_dict[task_id]
        
        return None
    
    def get_supervision_status(self) -> Dict[str, Any]:
        """
        Get the overall status of the supervision process.
        
        Returns:
            Dict[str, Any]: Supervision status
        """
        # Update status
        self.status["updated_at"] = self.get_current_timestamp()
        
        # Check if all tasks are complete
        all_tasks = self.status["tasks_total"]
        completed_tasks = self.status["tasks_completed"] + self.status["tasks_failed"]
        
        if all_tasks > 0 and all_tasks == completed_tasks:
            self.status["status"] = "completed"
        elif len(self.running_tasks) > 0:
            self.status["status"] = "running"
        else:
            self.status["status"] = "pending"
        
        # Add task counts
        self.status["pending_tasks"] = len(self.task_queue)
        self.status["running_tasks"] = len(self.running_tasks)
        
        return self.status
    
    def get_all_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all tasks organized by status.
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: All tasks
        """
        return {
            "pending": self.task_queue.copy(),
            "running": list(self.running_tasks.values()),
            "completed": [t for t in self.completed_tasks.values() if t["status"] == "completed"],
            "failed": [t for t in self.completed_tasks.values() if t["status"] == "failed"]
        }
    
    def run_supervision_workflow(self, agent_outputs: Dict[str, Any], guidelines: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete supervision workflow for a set of agent outputs.
        
        Args:
            agent_outputs (Dict[str, Any]): Outputs from all agents
            guidelines (Dict[str, Any]): Supervision guidelines
            
        Returns:
            Dict[str, Any]: Workflow results
        """
        logger.info(f"Starting supervision workflow for {len(agent_outputs)} agents")
        
        # Reset status
        self.status = {
            "supervision_id": self._generate_supervision_id(),
            "started_at": self.get_current_timestamp(),
            "status": "running",
            "tasks_total": 0,
            "tasks_completed": 0,
            "tasks_failed": 0
        }
        
        # Clear task queues
        self.task_queue = []
        self.running_tasks = {}
        self.completed_tasks = {}
        
        try:
            # Schedule quality check tasks
            quality_task_ids = {}
            for agent_name, agent_output in agent_outputs.items():
                task_id = self.schedule_task(
                    task_type="quality_check",
                    params={
                        "agent_name": agent_name,
                        "agent_output": agent_output,
                        "guidelines": guidelines
                    }
                )
                quality_task_ids[agent_name] = task_id
            
            # Schedule consistency check tasks
            consistency_task_ids = {}
            for agent_name, agent_output in agent_outputs.items():
                task_id = self.schedule_task(
                    task_type="consistency_check",
                    params={
                        "agent_name": agent_name,
                        "agent_output": agent_output,
                        "guidelines": guidelines
                    }
                )
                consistency_task_ids[agent_name] = task_id
            
            # Schedule refinement tasks (dependent on quality and consistency checks)
            refinement_task_ids = {}
            for agent_name, agent_output in agent_outputs.items():
                task_id = self.schedule_task(
                    task_type="refinement",
                    params={
                        "agent_name": agent_name,
                        "agent_output": agent_output,
                        "quality_task_id": quality_task_ids[agent_name],
                        "consistency_task_id": consistency_task_ids[agent_name],
                        "guidelines": guidelines
                    },
                    priority=0  # Lower priority than checks
                )
                refinement_task_ids[agent_name] = task_id
            
            # Schedule report generation task (dependent on all refinements)
            report_task_id = self.schedule_task(
                task_type="report_generation",
                params={
                    "agent_outputs": agent_outputs,
                    "refinement_task_ids": refinement_task_ids,
                    "guidelines": guidelines
                },
                priority=-1  # Lowest priority
            )
            
            # Execute tasks (this would normally be done by a task executor)
            # For now, we'll simulate task execution
            
            # Quality and consistency checks can run in parallel in a real system
            quality_results = {}
            consistency_results = {}
            
            # Run quality checks
            for agent_name, task_id in quality_task_ids.items():
                task = self.start_task(task_id)
                if task:
                    # Simulate quality check execution
                    quality_results[agent_name] = {
                        "quality_score": 0.8,
                        "issues": [],
                        "metrics": {}
                    }
                    self.complete_task(task_id, quality_results[agent_name])
            
            # Run consistency checks
            for agent_name, task_id in consistency_task_ids.items():
                task = self.start_task(task_id)
                if task:
                    # Simulate consistency check execution
                    consistency_results[agent_name] = {
                        "consistency_score": 0.9,
                        "issues": [],
                        "comparisons": []
                    }
                    self.complete_task(task_id, consistency_results[agent_name])
            
            # Run refinements
            refined_outputs = {}
            for agent_name, task_id in refinement_task_ids.items():
                task = self.start_task(task_id)
                if task:
                    # Simulate refinement execution
                    refined_outputs[agent_name] = {
                        **agent_outputs[agent_name],
                        "refinement_status": "refined",
                        "refinements": []
                    }
                    self.complete_task(task_id, refined_outputs[agent_name])
            
            # Generate report
            task = self.start_task(report_task_id)
            if task:
                # Simulate report generation
                report = {
                    "status": "success",
                    "timestamp": self.get_current_timestamp(),
                    "agents_supervised": len(refined_outputs),
                    "overall_metrics": {
                        "quality": {
                            "before": sum(r["quality_score"] for r in quality_results.values()) / len(quality_results) if quality_results else 0,
                            "after": 0.9
                        },
                        "consistency": {
                            "before": sum(r["consistency_score"] for r in consistency_results.values()) / len(consistency_results) if consistency_results else 0,
                            "after": 0.95
                        },
                        "refinements_made": 0
                    }
                }
                self.complete_task(report_task_id, report)
            
            # Return final results
            return {
                "status": "success",
                "supervision_id": self.status["supervision_id"],
                "refined_outputs": refined_outputs,
                "supervision_report": report if 'report' in locals() else {},
                "workflow_status": self.get_supervision_status()
            }
            
        except Exception as e:
            logger.error(f"Error in supervision workflow: {str(e)}")
            
            # Update status
            self.status["status"] = "failed"
            self.status["error"] = str(e)
            
            return {
                "status": "error",
                "message": f"Error in supervision workflow: {str(e)}",
                "supervision_id": self.status["supervision_id"],
                "workflow_status": self.get_supervision_status()
            }
    
    def get_current_timestamp(self) -> str:
        """
        Get the current timestamp in ISO format.
        
        Returns:
            str: Current timestamp
        """
        return datetime.now().isoformat()
    
    def _generate_supervision_id(self) -> str:
        """
        Generate a unique supervision ID.
        
        Returns:
            str: Supervision ID
        """
        return f"sup-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
    
    def _generate_task_id(self) -> str:
        """
        Generate a unique task ID.
        
        Returns:
            str: Task ID
        """
        return f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}" 