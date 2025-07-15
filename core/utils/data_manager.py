"""
Data Manager Module

This module provides the DataManager class that manages data storage,
retrieval, and tracking across the educational content pipeline.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Type
from pathlib import Path
import hashlib

# Configure logging
logger = logging.getLogger(__name__)

class DataManager:
    """
    Data Manager class for handling data storage, retrieval, and tracking
    across the educational content pipeline.
    
    This class provides functionality for:
    1. Runtime data management during pipeline execution
    2. Persistent storage of agent outputs and intermediate results
    3. Memory management for agent learning and improvement
    4. Data provenance tracking
    5. Versioning of processed data
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the DataManager with the specified configuration.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary
        """
        self.config = config or {}
        
        # Set data storage paths
        self.base_data_dir = Path(self.config.get("base_data_dir", "output/data"))
        self.runtime_data_dir = self.base_data_dir / "runtime"
        self.memory_data_dir = self.base_data_dir / "memory"
        self.archive_data_dir = self.base_data_dir / "archive"
        
        # Create data directories if they don't exist
        os.makedirs(self.runtime_data_dir, exist_ok=True)
        os.makedirs(self.memory_data_dir, exist_ok=True)
        os.makedirs(self.archive_data_dir, exist_ok=True)
        
        # Initialize runtime data store
        self.runtime_data = {}
        
        # Initialize data tracking
        self.data_versions = {}
        self.data_provenance = {}
        
        logger.info(f"DataManager initialized with base directory: {self.base_data_dir}")
    
    def store_agent_output(
        self, 
        agent_name: str, 
        output_data: Dict[str, Any],
        run_id: str = None
    ) -> str:
        """
        Store the output data from an agent.
        
        Args:
            agent_name: Name of the agent
            output_data: Output data from the agent
            run_id: ID of the processing run (defaults to timestamp)
            
        Returns:
            Path to the stored data file
        """
        # Generate run_id if not provided
        if run_id is None:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create the output directory
        agent_dir = self.runtime_data_dir / agent_name
        os.makedirs(agent_dir, exist_ok=True)
        
        # Create the output file path
        output_file = agent_dir / f"{run_id}_{agent_name}_output.json"
        
        # Add metadata to the output data
        output_with_metadata = {
            "data": output_data,
            "metadata": {
                "agent": agent_name,
                "run_id": run_id,
                "timestamp": datetime.now().isoformat(),
                "version": self._get_next_version(agent_name, run_id)
            }
        }
        
        # Save the output data
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_with_metadata, f, ensure_ascii=False, indent=2)
        
        # Store in runtime data
        self.runtime_data[f"{agent_name}_{run_id}"] = output_with_metadata
        
        # Track data provenance
        self._track_provenance(agent_name, run_id, output_file)
        
        logger.info(f"Stored output from {agent_name} to {output_file}")
        
        return str(output_file)
    
    def get_agent_output(
        self, 
        agent_name: str, 
        run_id: str = None, 
        latest: bool = True
    ) -> Dict[str, Any]:
        """
        Get the output data from an agent.
        
        Args:
            agent_name: Name of the agent
            run_id: ID of the processing run (defaults to latest)
            latest: Whether to get the latest output (ignored if run_id is provided)
            
        Returns:
            Output data from the agent
        """
        # Check runtime data first
        if run_id is not None:
            runtime_key = f"{agent_name}_{run_id}"
            if runtime_key in self.runtime_data:
                logger.info(f"Retrieved {agent_name} output from runtime data")
                return self.runtime_data[runtime_key]["data"]
        
        # Look in filesystem if not in runtime data
        agent_dir = self.runtime_data_dir / agent_name
        
        if not agent_dir.exists():
            logger.warning(f"No data directory found for agent {agent_name}")
            return None
        
        # Find matching or latest file
        if run_id is not None:
            # Find file with matching run_id
            matching_files = list(agent_dir.glob(f"{run_id}_{agent_name}_output.json"))
            if not matching_files:
                logger.warning(f"No output file found for {agent_name} with run_id {run_id}")
                return None
            output_file = matching_files[0]
        elif latest:
            # Find the latest file
            all_files = list(agent_dir.glob(f"*_{agent_name}_output.json"))
            if not all_files:
                logger.warning(f"No output files found for {agent_name}")
                return None
            output_file = max(all_files, key=os.path.getmtime)
        else:
            logger.warning(f"Either run_id or latest must be specified")
            return None
        
        # Load the output data
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                output_data = json.load(f)
            
            # Store in runtime data
            extracted_run_id = output_file.stem.split('_')[0]
            runtime_key = f"{agent_name}_{extracted_run_id}"
            self.runtime_data[runtime_key] = output_data
            
            logger.info(f"Retrieved {agent_name} output from {output_file}")
            
            return output_data["data"]
        except Exception as e:
            logger.error(f"Error loading output data from {output_file}: {e}")
            return None
    
    def store_memory(
        self, 
        agent_name: str, 
        memory_data: Dict[str, Any],
        memory_type: str = "general"
    ) -> str:
        """
        Store memory data for an agent.
        
        Args:
            agent_name: Name of the agent
            memory_data: Memory data to store
            memory_type: Type of memory data
            
        Returns:
            Path to the stored memory file
        """
        # Create the memory directory
        agent_memory_dir = self.memory_data_dir / agent_name
        os.makedirs(agent_memory_dir, exist_ok=True)
        
        # Create the memory file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        memory_file = agent_memory_dir / f"{memory_type}_{timestamp}.json"
        
        # Add metadata to the memory data
        memory_with_metadata = {
            "data": memory_data,
            "metadata": {
                "agent": agent_name,
                "memory_type": memory_type,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Save the memory data
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memory_with_metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Stored {memory_type} memory for {agent_name} to {memory_file}")
        
        return str(memory_file)
    
    def get_memory(
        self, 
        agent_name: str, 
        memory_type: str = "general", 
        latest: bool = True
    ) -> Dict[str, Any]:
        """
        Get memory data for an agent.
        
        Args:
            agent_name: Name of the agent
            memory_type: Type of memory data
            latest: Whether to get the latest memory
            
        Returns:
            Memory data for the agent
        """
        # Create the memory directory path
        agent_memory_dir = self.memory_data_dir / agent_name
        
        if not agent_memory_dir.exists():
            logger.warning(f"No memory directory found for agent {agent_name}")
            return None
        
        # Find matching memory files
        matching_files = list(agent_memory_dir.glob(f"{memory_type}_*.json"))
        
        if not matching_files:
            logger.warning(f"No {memory_type} memory found for agent {agent_name}")
            return None
        
        # Get latest or all memory files
        if latest:
            memory_file = max(matching_files, key=os.path.getmtime)
            
            # Load the memory data
            try:
                with open(memory_file, "r", encoding="utf-8") as f:
                    memory_data = json.load(f)
                
                logger.info(f"Retrieved {memory_type} memory for {agent_name} from {memory_file}")
                
                return memory_data["data"]
            except Exception as e:
                logger.error(f"Error loading memory data from {memory_file}: {e}")
                return None
        else:
            # Load all memory files
            all_memory = []
            
            for memory_file in sorted(matching_files, key=os.path.getmtime):
                try:
                    with open(memory_file, "r", encoding="utf-8") as f:
                        memory_data = json.load(f)
                    
                    all_memory.append(memory_data["data"])
                except Exception as e:
                    logger.error(f"Error loading memory data from {memory_file}: {e}")
            
            logger.info(f"Retrieved {len(all_memory)} {memory_type} memories for {agent_name}")
            
            return all_memory
    
    def archive_data(
        self, 
        agent_name: str, 
        run_id: str, 
        archive_name: str = None
    ) -> str:
        """
        Archive data from a completed run.
        
        Args:
            agent_name: Name of the agent
            run_id: ID of the processing run
            archive_name: Name for the archive (defaults to agent_name + run_id)
            
        Returns:
            Path to the archived data file
        """
        # Get the output data
        output_data = self.get_agent_output(agent_name, run_id)
        
        if output_data is None:
            logger.warning(f"No output data found for {agent_name} with run_id {run_id}")
            return None
        
        # Create the archive name if not provided
        if archive_name is None:
            archive_name = f"{agent_name}_{run_id}"
        
        # Create the archive directory
        archive_dir = self.archive_data_dir / archive_name
        os.makedirs(archive_dir, exist_ok=True)
        
        # Create the archive file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_file = archive_dir / f"{agent_name}_{timestamp}.json"
        
        # Add metadata to the output data
        archive_data = {
            "data": output_data,
            "metadata": {
                "agent": agent_name,
                "run_id": run_id,
                "archive_timestamp": datetime.now().isoformat(),
                "archive_name": archive_name
            }
        }
        
        # Save the archive data
        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(archive_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Archived {agent_name} data from run {run_id} to {archive_file}")
        
        return str(archive_file)
    
    def get_data_lineage(self, agent_name: str, run_id: str) -> Dict[str, Any]:
        """
        Get the data lineage for a specific agent output.
        
        Args:
            agent_name: Name of the agent
            run_id: ID of the processing run
            
        Returns:
            Data lineage information
        """
        # Check if we have provenance information
        provenance_key = f"{agent_name}_{run_id}"
        
        if provenance_key not in self.data_provenance:
            logger.warning(f"No provenance information found for {agent_name} with run_id {run_id}")
            return None
        
        return self.data_provenance[provenance_key]
    
    def _get_next_version(self, agent_name: str, run_id: str) -> str:
        """
        Get the next version number for an agent output.
        
        Args:
            agent_name: Name of the agent
            run_id: ID of the processing run
            
        Returns:
            Next version number
        """
        version_key = f"{agent_name}_{run_id}"
        
        if version_key not in self.data_versions:
            self.data_versions[version_key] = 1
            return "v1"
        else:
            next_version = self.data_versions[version_key] + 1
            self.data_versions[version_key] = next_version
            return f"v{next_version}"
    
    def _track_provenance(self, agent_name: str, run_id: str, output_file: Path) -> None:
        """
        Track the provenance of agent output data.
        
        Args:
            agent_name: Name of the agent
            run_id: ID of the processing run
            output_file: Path to the output file
        """
        provenance_key = f"{agent_name}_{run_id}"
        
        if provenance_key not in self.data_provenance:
            self.data_provenance[provenance_key] = {
                "agent": agent_name,
                "run_id": run_id,
                "first_created": datetime.now().isoformat(),
                "files": [],
                "versions": [],
                "inputs": [],
                "processors": [agent_name]
            }
        
        # Add this file to the provenance
        self.data_provenance[provenance_key]["files"].append(str(output_file))
        self.data_provenance[provenance_key]["versions"].append(
            self._get_next_version(agent_name, run_id)
        )
        self.data_provenance[provenance_key]["last_updated"] = datetime.now().isoformat()
    
    def register_input_dependency(
        self, 
        agent_name: str, 
        run_id: str, 
        input_agent: str, 
        input_run_id: str
    ) -> None:
        """
        Register an input dependency for an agent output.
        
        Args:
            agent_name: Name of the agent
            run_id: ID of the processing run
            input_agent: Name of the input agent
            input_run_id: ID of the input run
        """
        provenance_key = f"{agent_name}_{run_id}"
        input_key = f"{input_agent}_{input_run_id}"
        
        if provenance_key not in self.data_provenance:
            self._track_provenance(agent_name, run_id, Path("unknown"))
        
        # Add the input dependency
        if input_key not in self.data_provenance[provenance_key]["inputs"]:
            self.data_provenance[provenance_key]["inputs"].append(input_key)
        
        # Update the processors list
        if input_agent not in self.data_provenance[provenance_key]["processors"]:
            self.data_provenance[provenance_key]["processors"].append(input_agent)
        
        logger.info(f"Registered input dependency from {input_agent} (run {input_run_id}) "
                  f"for {agent_name} (run {run_id})")
    
    def get_runtime_data(self) -> Dict[str, Any]:
        """
        Get all runtime data currently in memory.
        
        Returns:
            Dictionary of all runtime data
        """
        return self.runtime_data
    
    def clear_runtime_data(self) -> None:
        """Clear all runtime data currently in memory."""
        self.runtime_data = {}
        logger.info("Cleared all runtime data")
    
    def export_data_provenance(self, output_file: str = None) -> Dict[str, Any]:
        """
        Export all data provenance information.
        
        Args:
            output_file: Optional file to save the provenance data
            
        Returns:
            Dictionary of all provenance data
        """
        if output_file is not None:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.data_provenance, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported data provenance to {output_file}")
        
        return self.data_provenance
    
    def compute_data_hash(self, data: Dict[str, Any]) -> str:
        """
        Compute a hash for the provided data.
        
        Args:
            data: Data to hash
            
        Returns:
            Hash of the data
        """
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode("utf-8")).hexdigest()
    
    def detect_duplicates(self, agent_name: str = None) -> Dict[str, List[str]]:
        """
        Detect duplicate data outputs for an agent or all agents.
        
        Args:
            agent_name: Optional name of the agent to check
            
        Returns:
            Dictionary mapping data hashes to file paths
        """
        # Get the directory to check
        if agent_name is not None:
            dirs_to_check = [self.runtime_data_dir / agent_name]
        else:
            dirs_to_check = [d for d in self.runtime_data_dir.iterdir() if d.is_dir()]
        
        # Find all output files
        all_files = []
        for d in dirs_to_check:
            if d.exists():
                all_files.extend(d.glob("*_output.json"))
        
        # Compute hashes and find duplicates
        hash_map = {}
        
        for file_path in all_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                
                # Compute hash of just the data (excluding metadata)
                data_hash = self.compute_data_hash(file_data.get("data", {}))
                
                if data_hash not in hash_map:
                    hash_map[data_hash] = []
                
                hash_map[data_hash].append(str(file_path))
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
        
        # Filter to only duplicates
        duplicates = {h: files for h, files in hash_map.items() if len(files) > 1}
        
        logger.info(f"Found {len(duplicates)} sets of duplicate data")
        
        return duplicates

    def store_output(self, output_type: str, output_data: Dict[str, Any], run_id: str = None) -> str:
        """
        Store output data of a specific type (not necessarily from an agent).
        
        Args:
            output_type: Type of the output
            output_data: Output data to store
            run_id: ID of the processing run (defaults to timestamp)
            
        Returns:
            Path to the stored data file
        """
        # Simply use store_agent_output with the output_type as the agent_name
        return self.store_agent_output(output_type, output_data, run_id)

    def archive_run_data(self, run_id: str) -> Dict[str, str]:
        """
        Archive all data from a specific run.
        
        Args:
            run_id: ID of the processing run
            
        Returns:
            Dictionary mapping agent names to archive paths
        """
        logger.info(f"Archiving all data for run {run_id}")
        
        archives = {}
        
        # Get all runtime data for this run
        run_data = {k: v for k, v in self.runtime_data.items() if k.endswith(f"_{run_id}")}
        
        # Archive each agent's data
        for runtime_key, data in run_data.items():
            try:
                agent_name = runtime_key.replace(f"_{run_id}", "")
                archive_path = self.archive_data(agent_name, run_id)
                
                if archive_path:
                    archives[agent_name] = archive_path
            except Exception as e:
                logger.error(f"Error archiving data for {runtime_key}: {str(e)}")
        
        logger.info(f"Archived data for {len(archives)} agents from run {run_id}")
        
        return archives 