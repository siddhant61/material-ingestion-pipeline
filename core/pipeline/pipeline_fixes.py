#!/usr/bin/env python3
"""
Pipeline Fixes

This module consolidates all pipeline fixes into a single location:
1. Template fixes for Document Loader Agent
2. Template fixes for Transcript Processor
3. Datetime import fixes
4. Pipeline structure and dependency fixes

This module should be imported and the appropriate methods called as needed.
"""

import os
import re
import json
import logging
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("pipeline_fixes")

# Path constants
DOCUMENT_LOADER_PATH = Path("core/agents/document_loader")
ASSISTANTS_PATH = DOCUMENT_LOADER_PATH / "assistants"
TRANSCRIPT_PROCESSOR_PATH = Path("core/agents/transcript_processor/transcript_processor.py")

# Regular expressions for finding and fixing datetime imports
DATETIME_IMPORT_PATTERN = re.compile(r'^import\s+datetime\s*$', re.MULTILINE)
DATETIME_USAGE_PATTERN = re.compile(r'datetime\.datetime\.')
CORRECT_IMPORT = 'from datetime import datetime'

#############################
# Document Loader Template Fixes
#############################

class TemplateFixer:
    """Fixes template issues in Document Loader Agent Assistants."""

    def __init__(self):
        """Initialize the fixer with paths."""
        self.assistants_path = ASSISTANTS_PATH
        
    def fix_all_assistants(self):
        """Fix templates in all assistant files."""
        logger.info(f"Scanning assistant files in {self.assistants_path}")
        
        total_fixes = 0
        
        # Walk through assistants directory
        for file_path in self.assistants_path.glob("**/*.py"):
            if file_path.is_file():
                fixes = self.fix_file(file_path)
                total_fixes += fixes
                
        logger.info(f"Total fixes applied: {total_fixes}")
        return total_fixes
    
    def fix_file(self, file_path):
        """Fix template issues in a single file."""
        try:
            logger.info(f"Processing file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            original_content = content
            fixes_applied = 0
            
            # Apply each fix type and count the fixes
            whitespace_result = self._fix_whitespace_in_variables(file_path, content)
            if isinstance(whitespace_result, tuple):
                fixes_applied += whitespace_result[0]
                content = whitespace_result[1]
            
            duplicate_result = self._fix_duplicate_variables(file_path, content)
            if isinstance(duplicate_result, tuple):
                fixes_applied += duplicate_result[0]
                content = duplicate_result[1]
            
            curly_braces_result = self._fix_literal_curly_braces(file_path, content)
            if isinstance(curly_braces_result, tuple):
                fixes_applied += curly_braces_result[0]
                content = curly_braces_result[1]
            
            # Write back if content was changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                logger.info(f"Applied {fixes_applied} fixes to {file_path}")
                return fixes_applied
            else:
                logger.info(f"No fixes needed for {file_path}")
                return 0
            
        except Exception as e:
            logger.error(f"Error fixing file {file_path}: {str(e)}")
            return 0
        
    def _fix_whitespace_in_variables(self, file_path, content):
        """
        Fix issues with whitespace in variables, such as:
        "\n            \"document_structure\""
        """
        pattern = re.compile(r'(\"[^\"]*?)(\s+)(\"[a-zA-Z_]+\")')
        
        def replace_whitespace(match):
            full_match = match.group(0)
            prefix = match.group(1)
            whitespace = match.group(2)
            variable = match.group(3)
            
            # Replace with clean version
            clean = f"{prefix}{variable}"
            logger.debug(f"Whitespace fix in {file_path}: '{full_match}' -> '{clean}'")
            return clean
        
        new_content = re.sub(pattern, replace_whitespace, content)
        fixes = sum(1 for _ in re.finditer(pattern, content))
        
        if fixes > 0:
            logger.info(f"Fixed {fixes} whitespace issues in variables in {file_path}")
            return fixes, new_content
        return 0
        
    def _fix_duplicate_variables(self, file_path, content):
        """
        Fix duplicate variables in expected variable lists.
        E.g., ["title", "document_structure", "title"] -> ["title", "document_structure"]
        """
        # Pattern to find JSON arrays in docstrings or comments
        pattern = re.compile(r'(\[(?:[^\[\]]|\"[^\"]*\")*\])')
        
        def deduplicate_variables(match):
            array_str = match.group(0)
            
            try:
                # Try to parse as JSON
                array = json.loads(array_str)
                
                # Check if this is actually a list of strings
                if isinstance(array, list) and all(isinstance(x, str) for x in array):
                    # Deduplicate
                    unique_array = []
                    for item in array:
                        if item not in unique_array:
                            unique_array.append(item)
                    
                    # If we removed duplicates, return the new array
                    if len(unique_array) < len(array):
                        logger.debug(f"Deduplication in {file_path}: {array} -> {unique_array}")
                        return json.dumps(unique_array)
            except json.JSONDecodeError:
                pass
            
            # If not a valid JSON array or no duplicates, return unchanged
            return array_str
        
        # Keep track of original for comparison
        original_content = content
        new_content = re.sub(pattern, deduplicate_variables, content)
        
        # Count only cases where we actually deduplicated
        fixes = 0
        if new_content != original_content:
            # Rough count - one fix per modified list
            fixes = len(re.findall(r'\[.*?\]', original_content)) - len(re.findall(r'\[.*?\]', new_content))
            logger.info(f"Deduplicated {fixes} variable lists in {file_path}")
            return fixes, new_content
        return 0
    
    def _fix_literal_curly_braces(self, file_path, content):
        """
        Fix improperly escaped curly braces in prompts, e.g.
        "Here is a JSON: { key: value }" -> "Here is a JSON: {{ key: value }}"
        """
        # Pattern to find system prompts in triple quotes
        pattern = re.compile(r'(\"\"\"[^\"]*?{[^\"]*?}[^\"]*?\"\"\")')
        
        def escape_curly_braces(match):
            system_prompt = match.group(0)
            
            # Replace unescaped curly braces with double braces ({{ and }})
            # But avoid replacing already doubled braces
            fixed_prompt = re.sub(r'(?<!\{)\{(?!\{)', '{{', system_prompt)
            fixed_prompt = re.sub(r'(?<!\})\}(?!\})', '}}', fixed_prompt)
            
            return fixed_prompt
        
        # Keep track of original for comparison
        original_content = content
        new_content = re.sub(pattern, escape_curly_braces, content)
        
        fixes = 0
        if new_content != original_content:
            # Estimate fixes by counting the difference in { and } characters
            original_count = content.count('{') + content.count('}')
            new_count = new_content.count('{') + new_content.count('}')
            fixes = (new_count - original_count) // 2  # Each fix adds one extra { and one extra }
            logger.info(f"Fixed {fixes} curly brace escaping issues in {file_path}")
            return fixes, new_content
        return 0

def fix_document_loader_templates():
    """Fix templates in Document Loader Agent."""
    logger.info("Fixing template issues in Document Loader Agent...")
    try:
        fixer = TemplateFixer()
        total_fixes = fixer.fix_all_assistants()
        logger.info(f"Template fixes completed: {total_fixes} issues fixed")
        return True
    except Exception as e:
        logger.error(f"Error fixing templates: {str(e)}")
        return False

#############################
# Transcript Processor Template Fixes
#############################

class TranscriptTemplateFixer:
    """
    Fixes template issues in the Transcript Processor files.
    """
    
    def __init__(self):
        """Initialize the fixer with paths."""
        self.transcript_processor_path = TRANSCRIPT_PROCESSOR_PATH
        
    def fix_transcript_processor(self):
        """Fix templates in transcript processor."""
        logger.info(f"Scanning transcript processor at {self.transcript_processor_path}")
        
        total_fixes = 0
        transcript_processor_path = self.transcript_processor_path
        
        # Process main transcript processor file
        if transcript_processor_path.exists():
            fixes = self.fix_file(transcript_processor_path)
            total_fixes += fixes
                
        logger.info(f"Total transcript processor fixes applied: {total_fixes}")
        return total_fixes
    
    def fix_file(self, file_path):
        """Fix template issues in the transcript processor file."""
        try:
            logger.info(f"Processing transcript file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            original_content = content
            fixes_applied = 0
            
            # Apply whitespace fixes
            content = self._fix_whitespace_in_variables(file_path, content)
            
            # Apply JSON structure fixes in prompts
            content = self._fix_json_structure_in_prompts(file_path, content)
            
            # Apply variable reference fixes
            content = self._ensure_proper_variable_references(file_path, content)
            
            # Write back if content was changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                logger.info(f"Applied fixes to transcript processor file {file_path}")
                return 1
            else:
                logger.info(f"No fixes needed for transcript processor file {file_path}")
                return 0
            
        except Exception as e:
            logger.error(f"Error fixing transcript processor file {file_path}: {str(e)}")
            return 0
        
    def _fix_whitespace_in_variables(self, file_path, content):
        """
        Fix issues with whitespace in variables, such as:
        "\n            \"document_structure\""
        """
        pattern = re.compile(r'(\"[^\"]*?)(\s+)(\"[a-zA-Z_]+\")')
        
        def replace_whitespace(match):
            full_match = match.group(0)
            prefix = match.group(1)
            whitespace = match.group(2)
            variable = match.group(3)
            
            # Replace with clean version
            clean = f"{prefix}{variable}"
            logger.debug(f"Whitespace fix in {file_path}: '{full_match}' -> '{clean}'")
            return clean
        
        fixed_content = re.sub(pattern, replace_whitespace, content)
        return fixed_content
        
    def _fix_json_structure_in_prompts(self, file_path, content):
        """
        Fix issues with JSON structures in system prompts, particularly:
        - Single curly braces in JSON examples
        - Ensuring consistency in formatting
        """
        # Pattern to find system prompts with JSON examples
        system_prompt_pattern = re.compile(r'(\"\"\"[^\"]*?{[^\"]*?}[^\"]*?\"\"\")')
        
        def fix_json_example(match):
            system_prompt = match.group(0)
            
            # Double any single curly braces but avoid doubling already doubled braces
            # This ensures that literal JSON in langchain templates is properly escaped
            fixed_prompt = re.sub(r'(?<!\{)\{(?!\{)', '{{', system_prompt)
            fixed_prompt = re.sub(r'(?<!\})\}(?!\})', '}}', fixed_prompt)
            
            return fixed_prompt
        
        fixed_content = re.sub(system_prompt_pattern, fix_json_example, content)
        return fixed_content
    
    def _ensure_proper_variable_references(self, file_path, content):
        """
        Ensure that variable references in prompts are properly formatted without extra whitespace
        and match the expected variables in input_variables.
        """
        # Pattern to find variable references like {variable_name} with potential whitespace
        pattern = re.compile(r'{(\s*)([a-zA-Z_]+)(\s*)}')
        
        def fix_variable_reference(match):
            full_match = match.group(0)
            leading_space = match.group(1)
            variable_name = match.group(2)
            trailing_space = match.group(3)
            
            # Remove any whitespace inside the curly braces
            clean = f"{{{variable_name}}}"
            return clean
        
        fixed_content = re.sub(pattern, fix_variable_reference, content)
        return fixed_content

def manually_fix_transcript_processor():
    """
    Apply some specific manual fixes to the transcript processor file.
    These are fixes that might be too specific for the general fix methods.
    """
    file_path = TRANSCRIPT_PROCESSOR_PATH
    
    if not file_path.exists():
        logger.warning(f"Transcript processor file not found at {file_path}")
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Fix 1: Template string with missing whitespace and quotes
        # Original: format=f"webvtt" -> format="webvtt"
        content = re.sub(
            r'format=f"webvtt"', 
            r'format="webvtt"', 
            content
        )
        
        # Fix 2: Fix the segmentation system prompt which has JSON issues
        segmentation_system_prompt = '''"""
You are an expert in analyzing lecture transcripts. Your task is to segment a lecture transcript into logical units based on topic changes.

Follow these steps:
1. Analyze the transcript to identify natural topic changes or new concepts being introduced.
2. Create segments at these topic change points.
3. For each segment, identify a concise title that reflects the topic.
4. Consider lecture structure indicators like "Now let's discuss..." or "Moving on to..."

For each segment, provide:
1. The segment text (exactly as in the original transcript)
2. A concise title (5-7 words maximum)
3. The timestamp range it covers
4. Any key technical terms or concepts introduced

Return the segmented transcript as a JSON object with this structure:
{{
  "segments": [
    {{
      "title": "Brief segment title",
      "start_time": "HH:MM:SS.mmm",
      "end_time": "HH:MM:SS.mmm",
      "content": "The full text of this segment, exactly as in the original",
      "key_terms": ["term1", "term2"]
    }},
    // additional segments...
  ]
}}

Ensure your segmentation is logical and maintains the educational flow of the lecture.
"""'''
        
        # Replace the system prompt to ensure proper template formatting
        content = re.sub(
            r'"""You are an expert in analyzing lecture transcripts.*?"""',
            segmentation_system_prompt,
            content,
            flags=re.DOTALL
        )
        
        # Fix 3: Ensure proper format for any extraction prompts
        extraction_system_prompt = '''"""
You are an expert in analyzing educational content. Extract key information from this transcript segment.

For this transcript segment, extract:
1. The main topic discussed
2. Key concepts and definitions introduced
3. Any examples provided
4. Any questions posed or discussion points
5. Technical terms with their explanations
6. Any formulas, equations, or mathematical concepts
7. References to external resources or materials

Return the information in this JSON format:
{{
  "main_topic": "The primary subject discussed in this segment",
  "key_concepts": [
    {{
      "concept": "Name of concept",
      "definition": "How the concept is defined or explained"
    }}
  ],
  "examples": ["Example 1", "Example 2"],
  "discussion_points": ["Point 1", "Point 2"],
  "technical_terms": [
    {{
      "term": "Technical term",
      "explanation": "How the term is explained"
    }}
  ],
  "mathematical_content": [
    {{
      "description": "Description of formula or concept",
      "formula": "The formula if mentioned"
    }}
  ],
  "references": ["Reference 1", "Reference 2"]
}}

Focus on information that is explicitly stated in the transcript. If a particular section has no relevant information, use an empty array [] or "None".
"""'''
        
        # Replace the extraction system prompt if it exists
        content = re.sub(
            r'"""You are an expert in analyzing educational content\. Extract key information.*?"""',
            extraction_system_prompt,
            content,
            flags=re.DOTALL
        )
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
            
        logger.info(f"Applied manual fixes to transcript processor file {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error applying manual fixes to transcript processor: {str(e)}")
        return False

def fix_transcript_templates():
    """Fix templates in Transcript Processor."""
    logger.info("Fixing template issues in Transcript Processor...")
    try:
        # First apply the general template fixes
        fixer = TranscriptTemplateFixer()
        fixer.fix_transcript_processor()
        
        # Then apply any manual fixes that might be needed
        manually_fix_transcript_processor()
        
        logger.info("Transcript processor template fixes completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error fixing transcript templates: {str(e)}")
        return False

#############################
# Datetime Import Fixes
#############################

def fix_datetime_imports_in_file(file_path):
    """
    Fix datetime imports in a single file.
    
    Args:
        file_path (Path): Path to the file to fix
        
    Returns:
        bool: Whether fixes were applied
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Check if the file has potential datetime issues
        if 'import datetime' in content and 'datetime.datetime' in content:
            # Replace the import
            updated_content = DATETIME_IMPORT_PATTERN.sub(CORRECT_IMPORT, content)
            
            # Replace usage
            updated_content = DATETIME_USAGE_PATTERN.sub('datetime.', updated_content)
            
            # Only write if changed
            if updated_content != content:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(updated_content)
                logger.info(f"Fixed datetime imports in {file_path}")
                return True
    
    except Exception as e:
        logger.error(f"Error fixing datetime imports in {file_path}: {str(e)}")
    
    return False

def fix_all_datetime_imports():
    """
    Find and fix datetime import issues throughout the codebase.
    
    Returns:
        int: Number of files fixed
    """
    logger.info("Scanning for datetime import issues...")
    fixed_count = 0
    
    # Start from the root directory
    script_dir = Path(".")
    
    for file_path in script_dir.glob("**/*.py"):
        if file_path.is_file():
            if fix_datetime_imports_in_file(file_path):
                fixed_count += 1
                
    logger.info(f"Fixed datetime imports in {fixed_count} files")
    return fixed_count

#############################
# Data Manager Fixes
#############################

def fix_data_manager():
    """
    Fix issues in the DataManager class, specifically:
    1. Add missing tracking methods
    2. Ensure document deduplication works correctly
    
    Returns:
        bool: Whether fixes were applied
    """
    data_manager_path = Path("core/pipeline/material_ingestion_pipeline.py")
    
    if not data_manager_path.exists():
        logger.warning(f"DataManager file not found at {data_manager_path}")
        return False
        
    try:
        with open(data_manager_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Check if we need to add document tracking methods
        if "def is_document_processed" not in content:
            # Find the DataManager class
            data_manager_class_match = re.search(r'class DataManager[^\n]*:.*?def __init__\([^)]*\):[^\n]*', content, re.DOTALL)
            
            if not data_manager_class_match:
                logger.warning("Could not find DataManager class initialization")
                return False
                
            # Add document tracking initialization to __init__
            init_end = data_manager_class_match.end()
            init_addition = """
        # Initialize document tracking
        self.processed_documents = set()
        self.document_results = {}
"""
            
            # Insert after __init__ method
            content = content[:init_end] + init_addition + content[init_end:]
            
            # Add document tracking methods
            # Find the end of the DataManager class
            class_end_match = re.search(r'class (?!DataManager)', content[init_end:])
            if class_end_match:
                class_end = init_end + class_end_match.start()
            else:
                # Use the end of the file if no other class is found
                class_end = len(content)
                
            # Add tracking methods before the end of the class
            tracking_methods = """
    def is_document_processed(self, document_path):
        \"\"\"Check if a document has already been processed.\"\"\"

        return str(document_path) in self.processed_documents
        
    def mark_document_processed(self, document_path, result=None):
        \"\"\"Mark a document as processed and store its result.\"\"\"

        self.processed_documents.add(str(document_path))
        if result:
            self.document_results[str(document_path)] = result
            
    def get_document_result(self, document_path):
        \"\"\"Get the stored result for a processed document.\"\"\"

        return self.document_results.get(str(document_path))
        
    def save_tracking_data(self):
        \"\"\"Save document tracking data to disk.\"\"\"

        tracking_data = {
            "processed_documents": list(self.processed_documents),
            "document_results": self.document_results
        }
        
        # Save to a JSON file in the output directory
        tracking_file = self.output_dir / "data" / "document_tracking.json"
        tracking_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(tracking_file, 'w', encoding='utf-8') as f:
            json.dump(tracking_data, f, indent=2)
            
    def load_tracking_data(self):
        \"\"\"Load document tracking data from disk if available.\"\"\"

        tracking_file = self.output_dir / "data" / "document_tracking.json"
        
        if tracking_file.exists():
            try:
                with open(tracking_file, 'r', encoding='utf-8') as f:
                    tracking_data = json.load(f)
                    
                self.processed_documents = set(tracking_data.get("processed_documents", []))
                self.document_results = tracking_data.get("document_results", {})
                logger.info(f"Loaded tracking data for {len(self.processed_documents)} documents")
                return True
            except Exception as e:
                logger.error(f"Error loading tracking data: {str(e)}")
                return False
        
        return False
"""

            content = content[:class_end] + tracking_methods + content[class_end:]
            
            # Update process_document method to use tracking
            process_doc_pattern = re.compile(r'def process_document\([^)]*\):.*?return\s+[^}]*}', re.DOTALL)
            
            def replace_process_document(match):
                method = match.group(0)
                
                # Check if document is already processed
                check_processed = """
        # Check if document has already been processed
        if self.is_document_processed(document_path):
            logger.info(f"Document {document_path} already processed, retrieving cached result")
            return self.get_document_result(document_path)
"""
                
                # Mark document as processed before returning
                mark_processed = """
        # Mark document as processed and cache the result
        self.mark_document_processed(document_path, result)
        self.save_tracking_data()
"""
                
                # Add checks at beginning of method and before return
                method_lines = method.split('\n')
                modified_lines = []
                
                # Find where to insert the check
                body_start = next((i for i, line in enumerate(method_lines) if 'def process_document' in line), 0) + 1
                
                # Find where to insert the tracking before return
                for i, line in enumerate(method_lines):
                    if i == body_start:
                        modified_lines.append(method_lines[i])
                        modified_lines.append(check_processed)
                    elif 'return' in line and 'result' in line:
                        modified_lines.append(mark_processed)
                        modified_lines.append(line)
                    else:
                        modified_lines.append(line)
                        
                return '\n'.join(modified_lines)
                
            content = process_doc_pattern.sub(replace_process_document, content)
            
            # Write updated content back to file
            with open(data_manager_path, 'w', encoding='utf-8') as file:
                file.write(content)
                
            logger.info(f"Added document tracking methods to DataManager in {data_manager_path}")
            return True
        else:
            logger.info("DataManager already has document tracking methods, no fixes needed")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing DataManager: {str(e)}")
        return False

#############################
# Sample Files Checker
#############################

def ensure_sample_files():
    """
    Ensure that sample course material files are available for testing.
    If files are missing, create minimal files to allow the pipeline to run.
    
    Returns:
        bool: Whether all sample files are available
    """
    # Define paths for sample files
    input_dir = Path("input")
    course_info_dir = input_dir / "course_info"
    transcripts_dir = input_dir / "transcripts"
    slides_dir = input_dir / "slides"
    
    # Create directories if they don't exist
    for directory in [input_dir, course_info_dir, transcripts_dir, slides_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        
    # Create a simple course info file if none exists
    course_info_files = list(course_info_dir.glob("*.pdf"))
    if not course_info_files:
        # Create a simple text file as placeholder
        placeholder_file = course_info_dir / "course_info_placeholder.txt"
        with open(placeholder_file, 'w', encoding='utf-8') as f:
            f.write("""Course Title: Introduction to Quantum Computing
Instructor: Dr. Quantum Expert
Description: This course introduces the basic concepts of quantum computing,
including qubits, superposition, entanglement, and quantum algorithms.

Learning Objectives:
- Understand the principles of quantum mechanics relevant to computing
- Learn about qubits and quantum gates
- Explore quantum algorithms like Grover's and Shor's
- Implement simple quantum circuits

Modules:
1. Quantum Mechanics Fundamentals
2. Qubits and Quantum Gates
3. Quantum Algorithms
4. Quantum Circuit Implementation
""")
        logger.info(f"Created placeholder course info file: {placeholder_file}")
        
    # Create a simple transcript file if none exists
    transcript_files = list(transcripts_dir.glob("*.vtt")) + list(transcripts_dir.glob("*.txt"))
    if not transcript_files:
        # Create a simple WebVTT file as placeholder
        placeholder_file = transcripts_dir / "lecture1_placeholder.vtt"
        with open(placeholder_file, 'w', encoding='utf-8') as f:
            f.write("""WEBVTT

00:00:00.000 --> 00:00:10.000
Welcome to our first lecture on quantum computing.
Today we'll be covering the fundamentals of quantum mechanics.

00:00:10.000 --> 00:00:20.000
Let's start with the concept of superposition.
A qubit can exist in multiple states simultaneously.

00:00:20.000 --> 00:00:30.000
Unlike classical bits which can only be 0 or 1,
qubits can be in a combination of both states.

00:00:30.000 --> 00:00:40.000
This is represented mathematically as:
|ψ⟩ = α|0⟩ + β|1⟩
where α and β are complex numbers.
""")
        logger.info(f"Created placeholder transcript file: {placeholder_file}")
        
    # Create a simple slides file if none exists
    slides_files = list(slides_dir.glob("*.pdf")) + list(slides_dir.glob("*.txt"))
    if not slides_files:
        # Create a simple text file as placeholder
        placeholder_file = slides_dir / "lecture1_slides_placeholder.txt"
        with open(placeholder_file, 'w', encoding='utf-8') as f:
            f.write("""Slide 1: Introduction to Quantum Computing
- Instructor: Dr. Quantum Expert
- Course Overview

Slide 2: Quantum Mechanics Fundamentals
- Superposition
- Entanglement
- Measurement

Slide 3: Understanding Qubits
- Definition: Quantum bits
- States: |0⟩, |1⟩, and superpositions
- Mathematical representation: |ψ⟩ = α|0⟩ + β|1⟩

Slide 4: Quantum Gates
- X Gate (NOT gate)
- H Gate (Hadamard gate)
- CNOT Gate (Controlled-NOT gate)

Slide 5: Quantum Algorithms
- Grover's Algorithm
- Shor's Algorithm
- Quantum Fourier Transform
""")
        logger.info(f"Created placeholder slides file: {placeholder_file}")
        
    # Check if output directory exists
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Return True if all necessary files exist now
    return (
        bool(list(course_info_dir.glob("*"))) and
        bool(list(transcripts_dir.glob("*"))) and
        bool(list(slides_dir.glob("*")))
    )

#############################
# Main Fix Functions
#############################

def apply_all_fixes():
    """
    Apply all pipeline fixes.
    
    Returns:
        bool: Whether all fixes were successfully applied
    """
    success = True
    
    # Fix template issues
    logger.info("Starting template fixes...")
    template_fixes_success = fix_document_loader_templates()
    transcript_fixes_success = fix_transcript_templates()
    success = success and template_fixes_success and transcript_fixes_success
    
    # Fix datetime imports
    logger.info("Starting datetime fixes...")
    datetime_fixes = fix_all_datetime_imports()
    
    # Fix data manager
    logger.info("Starting DataManager fixes...")
    data_manager_fixed = fix_data_manager()
    success = success and bool(data_manager_fixed)
    
    # Ensure sample files
    logger.info("Checking sample files...")
    sample_files_ok = ensure_sample_files()
    success = success and sample_files_ok
    
    # Summary
    if success:
        logger.info("All pipeline fixes applied successfully!")
    else:
        logger.warning("Some pipeline fixes were not successful, check the logs for details.")
        
    return success

if __name__ == "__main__":
    apply_all_fixes() 