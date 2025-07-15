"""
Supervisor Agent Memory

This module provides the memory component for the SupervisorAgent,
storing supervision history and results for retrieval and analysis.
"""

import os
import json
import logging
from datetime import datetime
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class SupervisorMemory:
    """
    Memory component for the SupervisorAgent.
    
    Stores supervision history and results, including:
    - Quality check results
    - Consistency check results
    - Refinement history
    - Supervision guidelines and standards
    - Agent output patterns and statistics
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the SupervisorMemory component.
        
        Args:
            config (Dict[str, Any], optional): Configuration options
        """
        self.config = config or {}
        
        # Set memory storage location
        self.memory_dir = Path(self.config.get("memory_dir", "output/memory/supervisor"))
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory storage
        self.quality_history = {}
        self.consistency_history = {}
        self.refinement_history = {}
        self.guidelines_history = {}
        self.agent_patterns = {}
        
        # Runtime memory (cleared between runs)
        self.current_run_id = None
        self.current_run_data = {}
        
        # Load existing memory if available
        self._load_memory()
        
        logger.info(f"SupervisorMemory initialized with storage at {self.memory_dir}")
    
    def store_quality_check(self, agent_name: str, quality_check: Dict[str, Any], run_id: str = None) -> str:
        """
        Store a quality check result.
        
        Args:
            agent_name (str): Name of the agent
            quality_check (Dict[str, Any]): Quality check result
            run_id (str, optional): Run ID, uses current run if None
            
        Returns:
            str: Storage ID
        """
        return self._store_check("quality", agent_name, quality_check, run_id)
    
    def store_consistency_check(self, agent_name: str, consistency_check: Dict[str, Any], run_id: str = None) -> str:
        """
        Store a consistency check result.
        
        Args:
            agent_name (str): Name of the agent
            consistency_check (Dict[str, Any]): Consistency check result
            run_id (str, optional): Run ID, uses current run if None
            
        Returns:
            str: Storage ID
        """
        return self._store_check("consistency", agent_name, consistency_check, run_id)
    
    def store_refinement(self, agent_name: str, refinement_data: Dict[str, Any], run_id: str = None) -> str:
        """
        Store a refinement result.
        
        Args:
            agent_name (str): Name of the agent
            refinement_data (Dict[str, Any]): Refinement data
            run_id (str, optional): Run ID, uses current run if None
            
        Returns:
            str: Storage ID
        """
        # Get run ID
        run_id = run_id or self.current_run_id or self._generate_run_id()
        
        # Add metadata
        storage_id = f"ref-{agent_name}-{int(time.time())}"
        
        storage_data = {
            "storage_id": storage_id,
            "agent_name": agent_name,
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "data": refinement_data
        }
        
        # Store in memory
        if agent_name not in self.refinement_history:
            self.refinement_history[agent_name] = []
        
        self.refinement_history[agent_name].append(storage_data)
        
        # Store in runtime memory
        if run_id not in self.current_run_data:
            self.current_run_data[run_id] = {"refinements": {}}
        if "refinements" not in self.current_run_data[run_id]:
            self.current_run_data[run_id]["refinements"] = {}
        
        self.current_run_data[run_id]["refinements"][agent_name] = storage_data
        
        # Save to disk
        self._save_to_disk("refinements", agent_name, storage_id, storage_data)
        
        logger.info(f"Stored refinement for {agent_name}: {storage_id}")
        return storage_id
    
    def store_guidelines(self, guidelines: Dict[str, Any], version: str = None) -> str:
        """
        Store supervision guidelines.
        
        Args:
            guidelines (Dict[str, Any]): Guidelines data
            version (str, optional): Version string, auto-generated if None
            
        Returns:
            str: Storage ID
        """
        # Generate version if not provided
        if not version:
            version = f"v{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Add metadata
        storage_id = f"guidelines-{version}"
        
        storage_data = {
            "storage_id": storage_id,
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "data": guidelines
        }
        
        # Store in memory
        self.guidelines_history[version] = storage_data
        
        # Save to disk
        self._save_to_disk("guidelines", "all", storage_id, storage_data)
        
        logger.info(f"Stored guidelines version {version}: {storage_id}")
        return storage_id
    
    def update_agent_patterns(self, agent_name: str, pattern_data: Dict[str, Any]) -> bool:
        """
        Update agent output patterns.
        
        Args:
            agent_name (str): Name of the agent
            pattern_data (Dict[str, Any]): Pattern data
            
        Returns:
            bool: Success status
        """
        # Initialize if needed
        if agent_name not in self.agent_patterns:
            self.agent_patterns[agent_name] = {
                "last_updated": None,
                "patterns": {}
            }
        
        # Update with new data
        self.agent_patterns[agent_name]["last_updated"] = datetime.now().isoformat()
        
        # Merge existing patterns with new ones
        for pattern_key, pattern_value in pattern_data.items():
            self.agent_patterns[agent_name]["patterns"][pattern_key] = pattern_value
        
        # Save to disk
        self._save_to_disk("patterns", agent_name, "latest", self.agent_patterns[agent_name])
        
        logger.info(f"Updated patterns for {agent_name}")
        return True
    
    def start_new_run(self) -> str:
        """
        Start a new supervision run.
        
        Returns:
            str: Run ID
        """
        # Generate new run ID
        self.current_run_id = self._generate_run_id()
        
        # Initialize run data
        self.current_run_data[self.current_run_id] = {
            "run_id": self.current_run_id,
            "started_at": datetime.now().isoformat(),
            "quality_checks": {},
            "consistency_checks": {},
            "refinements": {},
            "completed_at": None
        }
        
        logger.info(f"Started new supervision run: {self.current_run_id}")
        return self.current_run_id
    
    def end_run(self, run_id: str = None) -> Dict[str, Any]:
        """
        End a supervision run and save final state.
        
        Args:
            run_id (str, optional): Run ID to end, uses current run if None
            
        Returns:
            Dict[str, Any]: Run data
        """
        # Get run ID
        run_id = run_id or self.current_run_id
        
        if not run_id or run_id not in self.current_run_data:
            logger.warning(f"Cannot end unknown run: {run_id}")
            return {}
        
        # Update completion time
        self.current_run_data[run_id]["completed_at"] = datetime.now().isoformat()
        
        # Save run data to disk
        run_file = self.memory_dir / "runs" / f"{run_id}.json"
        run_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(run_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_run_data[run_id], f, ensure_ascii=False, indent=2)
        
        logger.info(f"Ended supervision run: {run_id}")
        
        # If this is the current run, clear it
        if run_id == self.current_run_id:
            self.current_run_id = None
        
        return self.current_run_data[run_id]
    
    def get_quality_history(self, agent_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get quality check history for an agent.
        
        Args:
            agent_name (str): Name of the agent
            limit (int, optional): Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: Quality check history
        """
        if agent_name not in self.quality_history:
            return []
        
        # Return most recent entries
        return sorted(self.quality_history[agent_name], 
                     key=lambda x: x["timestamp"], 
                     reverse=True)[:limit]
    
    def get_consistency_history(self, agent_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get consistency check history for an agent.
        
        Args:
            agent_name (str): Name of the agent
            limit (int, optional): Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: Consistency check history
        """
        if agent_name not in self.consistency_history:
            return []
        
        # Return most recent entries
        return sorted(self.consistency_history[agent_name], 
                     key=lambda x: x["timestamp"], 
                     reverse=True)[:limit]
    
    def get_refinement_history(self, agent_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get refinement history for an agent.
        
        Args:
            agent_name (str): Name of the agent
            limit (int, optional): Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: Refinement history
        """
        if agent_name not in self.refinement_history:
            return []
        
        # Return most recent entries
        return sorted(self.refinement_history[agent_name], 
                     key=lambda x: x["timestamp"], 
                     reverse=True)[:limit]
    
    def get_current_guidelines(self) -> Dict[str, Any]:
        """
        Get the current guidelines.
        
        Returns:
            Dict[str, Any]: Current guidelines
        """
        if not self.guidelines_history:
            return {}
        
        # Get the most recent guidelines
        latest = sorted(self.guidelines_history.values(), 
                       key=lambda x: x["timestamp"], 
                       reverse=True)[0]
        
        return latest.get("data", {})
    
    def get_agent_patterns(self, agent_name: str) -> Dict[str, Any]:
        """
        Get patterns for an agent.
        
        Args:
            agent_name (str): Name of the agent
            
        Returns:
            Dict[str, Any]: Agent patterns
        """
        if agent_name not in self.agent_patterns:
            return {"patterns": {}}
        
        return self.agent_patterns[agent_name].get("patterns", {})
    
    def get_run_data(self, run_id: str = None) -> Dict[str, Any]:
        """
        Get data for a specific run.
        
        Args:
            run_id (str, optional): Run ID, uses current run if None
            
        Returns:
            Dict[str, Any]: Run data
        """
        # Get run ID
        run_id = run_id or self.current_run_id
        
        if not run_id:
            logger.warning("No current run ID")
            return {}
        
        # Check if run data is in memory
        if run_id in self.current_run_data:
            return self.current_run_data[run_id]
        
        # Try to load from disk
        run_file = self.memory_dir / "runs" / f"{run_id}.json"
        if run_file.exists():
            try:
                with open(run_file, 'r', encoding='utf-8') as f:
                    run_data = json.load(f)
                return run_data
            except Exception as e:
                logger.error(f"Error loading run data for {run_id}: {str(e)}")
        
        logger.warning(f"No data found for run {run_id}")
        return {}
    
    def export_memory(self, target_dir: str = None) -> str:
        """
        Export all memory to a directory.
        
        Args:
            target_dir (str, optional): Target directory, uses timestamp if None
            
        Returns:
            str: Path to export directory
        """
        # Generate target directory if not provided
        if not target_dir:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            target_dir = f"output/exports/supervisor_memory_{timestamp}"
        
        # Create target directory
        export_dir = Path(target_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Export quality history
        quality_dir = export_dir / "quality"
        quality_dir.mkdir(exist_ok=True)
        for agent_name, checks in self.quality_history.items():
            agent_file = quality_dir / f"{agent_name}.json"
            with open(agent_file, 'w', encoding='utf-8') as f:
                json.dump(checks, f, ensure_ascii=False, indent=2)
        
        # Export consistency history
        consistency_dir = export_dir / "consistency"
        consistency_dir.mkdir(exist_ok=True)
        for agent_name, checks in self.consistency_history.items():
            agent_file = consistency_dir / f"{agent_name}.json"
            with open(agent_file, 'w', encoding='utf-8') as f:
                json.dump(checks, f, ensure_ascii=False, indent=2)
        
        # Export refinement history
        refinement_dir = export_dir / "refinements"
        refinement_dir.mkdir(exist_ok=True)
        for agent_name, refinements in self.refinement_history.items():
            agent_file = refinement_dir / f"{agent_name}.json"
            with open(agent_file, 'w', encoding='utf-8') as f:
                json.dump(refinements, f, ensure_ascii=False, indent=2)
        
        # Export guidelines
        guidelines_file = export_dir / "guidelines.json"
        with open(guidelines_file, 'w', encoding='utf-8') as f:
            json.dump(self.guidelines_history, f, ensure_ascii=False, indent=2)
        
        # Export patterns
        patterns_file = export_dir / "patterns.json"
        with open(patterns_file, 'w', encoding='utf-8') as f:
            json.dump(self.agent_patterns, f, ensure_ascii=False, indent=2)
        
        # Export metadata
        metadata = {
            "exported_at": datetime.now().isoformat(),
            "quality_checks": sum(len(checks) for checks in self.quality_history.values()),
            "consistency_checks": sum(len(checks) for checks in self.consistency_history.values()),
            "refinements": sum(len(refs) for refs in self.refinement_history.values()),
            "guideline_versions": len(self.guidelines_history),
            "agent_patterns": len(self.agent_patterns)
        }
        
        metadata_file = export_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported memory to {export_dir}")
        return str(export_dir)
    
    def clear_memory(self, keep_guidelines: bool = True) -> bool:
        """
        Clear all memory.
        
        Args:
            keep_guidelines (bool, optional): Whether to keep guidelines
            
        Returns:
            bool: Success status
        """
        # Clear memory structures
        self.quality_history = {}
        self.consistency_history = {}
        self.refinement_history = {}
        self.agent_patterns = {}
        
        if not keep_guidelines:
            self.guidelines_history = {}
        
        # Clear current run
        self.current_run_id = None
        self.current_run_data = {}
        
        logger.info(f"Cleared memory (keep_guidelines={keep_guidelines})")
        return True
    
    def _store_check(self, check_type: str, agent_name: str, check_data: Dict[str, Any], run_id: str = None) -> str:
        """
        Store a check result (internal method).
        
        Args:
            check_type (str): Type of check (quality or consistency)
            agent_name (str): Name of the agent
            check_data (Dict[str, Any]): Check result data
            run_id (str, optional): Run ID, uses current run if None
            
        Returns:
            str: Storage ID
        """
        # Get run ID
        run_id = run_id or self.current_run_id or self._generate_run_id()
        
        # Add metadata
        storage_id = f"{check_type}-{agent_name}-{int(time.time())}"
        
        storage_data = {
            "storage_id": storage_id,
            "agent_name": agent_name,
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "data": check_data
        }
        
        # Store in appropriate memory
        if check_type == "quality":
            history = self.quality_history
            run_key = "quality_checks"
        else:  # consistency
            history = self.consistency_history
            run_key = "consistency_checks"
        
        if agent_name not in history:
            history[agent_name] = []
        
        history[agent_name].append(storage_data)
        
        # Store in runtime memory
        if run_id not in self.current_run_data:
            self.current_run_data[run_id] = {run_key: {}}
        if run_key not in self.current_run_data[run_id]:
            self.current_run_data[run_id][run_key] = {}
        
        self.current_run_data[run_id][run_key][agent_name] = storage_data
        
        # Save to disk
        self._save_to_disk(f"{check_type}_checks", agent_name, storage_id, storage_data)
        
        logger.info(f"Stored {check_type} check for {agent_name}: {storage_id}")
        return storage_id
    
    def _save_to_disk(self, category: str, agent_name: str, storage_id: str, data: Dict[str, Any]) -> bool:
        """
        Save memory data to disk.
        
        Args:
            category (str): Data category
            agent_name (str): Name of the agent
            storage_id (str): Storage ID
            data (Dict[str, Any]): Data to save
            
        Returns:
            bool: Success status
        """
        try:
            # Create directory structure
            category_dir = self.memory_dir / category
            agent_dir = category_dir / agent_name
            agent_dir.mkdir(parents=True, exist_ok=True)
            
            # Save data
            data_file = agent_dir / f"{storage_id}.json"
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving memory to disk: {str(e)}")
            return False
    
    def _load_memory(self) -> bool:
        """
        Load memory from disk.
        
        Returns:
            bool: Success status
        """
        try:
            # Check if memory directory exists
            if not self.memory_dir.exists():
                logger.info(f"Memory directory does not exist: {self.memory_dir}")
                return False
            
            # Load quality checks
            quality_dir = self.memory_dir / "quality_checks"
            if quality_dir.exists():
                for agent_dir in quality_dir.iterdir():
                    if agent_dir.is_dir():
                        agent_name = agent_dir.name
                        self.quality_history[agent_name] = []
                        
                        for check_file in agent_dir.glob("*.json"):
                            try:
                                with open(check_file, 'r', encoding='utf-8') as f:
                                    check_data = json.load(f)
                                self.quality_history[agent_name].append(check_data)
                            except Exception as e:
                                logger.error(f"Error loading quality check file {check_file}: {str(e)}")
            
            # Load consistency checks
            consistency_dir = self.memory_dir / "consistency_checks"
            if consistency_dir.exists():
                for agent_dir in consistency_dir.iterdir():
                    if agent_dir.is_dir():
                        agent_name = agent_dir.name
                        self.consistency_history[agent_name] = []
                        
                        for check_file in agent_dir.glob("*.json"):
                            try:
                                with open(check_file, 'r', encoding='utf-8') as f:
                                    check_data = json.load(f)
                                self.consistency_history[agent_name].append(check_data)
                            except Exception as e:
                                logger.error(f"Error loading consistency check file {check_file}: {str(e)}")
            
            # Load refinements
            refinements_dir = self.memory_dir / "refinements"
            if refinements_dir.exists():
                for agent_dir in refinements_dir.iterdir():
                    if agent_dir.is_dir():
                        agent_name = agent_dir.name
                        self.refinement_history[agent_name] = []
                        
                        for refinement_file in agent_dir.glob("*.json"):
                            try:
                                with open(refinement_file, 'r', encoding='utf-8') as f:
                                    refinement_data = json.load(f)
                                self.refinement_history[agent_name].append(refinement_data)
                            except Exception as e:
                                logger.error(f"Error loading refinement file {refinement_file}: {str(e)}")
            
            # Load guidelines
            guidelines_dir = self.memory_dir / "guidelines"
            if guidelines_dir.exists():
                for guidelines_file in guidelines_dir.glob("**/*.json"):
                    try:
                        with open(guidelines_file, 'r', encoding='utf-8') as f:
                            guidelines_data = json.load(f)
                        
                        version = guidelines_data.get("version")
                        if version:
                            self.guidelines_history[version] = guidelines_data
                    except Exception as e:
                        logger.error(f"Error loading guidelines file {guidelines_file}: {str(e)}")
            
            # Load patterns
            patterns_dir = self.memory_dir / "patterns"
            if patterns_dir.exists():
                for agent_dir in patterns_dir.iterdir():
                    if agent_dir.is_dir():
                        agent_name = agent_dir.name
                        
                        # Get latest pattern file
                        pattern_files = list(agent_dir.glob("*.json"))
                        if pattern_files:
                            latest_file = max(pattern_files, key=lambda p: p.stat().st_mtime)
                            try:
                                with open(latest_file, 'r', encoding='utf-8') as f:
                                    pattern_data = json.load(f)
                                self.agent_patterns[agent_name] = pattern_data
                            except Exception as e:
                                logger.error(f"Error loading pattern file {latest_file}: {str(e)}")
            
            # Log summary
            quality_count = sum(len(checks) for checks in self.quality_history.values())
            consistency_count = sum(len(checks) for checks in self.consistency_history.values())
            refinement_count = sum(len(refs) for refs in self.refinement_history.values())
            
            logger.info(f"Loaded memory: {quality_count} quality checks, {consistency_count} consistency checks, "
                       f"{refinement_count} refinements, {len(self.guidelines_history)} guideline versions, "
                       f"{len(self.agent_patterns)} agent patterns")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading memory: {str(e)}")
            return False
    
    def _generate_run_id(self) -> str:
        """
        Generate a unique run ID.
        
        Returns:
            str: Run ID
        """
        return f"run-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}" 