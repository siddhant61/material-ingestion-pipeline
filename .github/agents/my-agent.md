---
name: Material Pipeline Builder
description: Develops and refactors the Material Ingestion Pipeline project, focusing on migrating the procedural logic into its formal, modular agent-based architecture (`MaterialIngestionPipeline`).
---

# My Agent: Material Ingestion Pipeline Workflow

Always follow this structured, context-driven workflow. Your primary goal is to **migrate the logic from `run_enhanced_pipeline.py` into the `core/pipeline/material_ingestion_pipeline.py` orchestrator**, externalize configuration, and build production-ready interfaces (CLI, API).

### 1. Evaluate the Given Task

Deconstruct the task by mapping it to the project's defined pipeline stages and architectural layers.

| Context | Focus Area | Project Example |
| :--- | :--- | :--- |
| **Universal Context** (Overall Goal) | The complete **Material Ingestion Pipeline** flow: **Ingest (Info, Transcripts, Slides) $\rightarrow$ Fuse $\rightarrow$ Supervise $\rightarrow$ Knowledge Graph $\rightarrow$ Visualize & Embed**. | Adding a new data source (e.g., video) must be a new, registerable `BaseAgent`. |
| **Global Context** (Feature/Domain) | Specific **Pipeline Stages** or **Key Components**: e.g., Context Extraction (`core/agents/course_context`), Supervision (`core/agents/supervisor`), or Orchestration (`core/pipeline/material_ingestion_pipeline.py`). | Implementing a new "Visual Agent" for image analysis belongs to the **Slide Processing** stage. |
| **Local Context** (Component Implementation) | Specific **Python Modules** or **Classes**: e.g., the `AIModelFactory` (`core/utils/ai_models.py`), the `SupervisorAgent` class (`core/agents/supervisor/agent.py`), or a function signature in `core/pipeline/knowledge_graph.py`. | Modifying the `AIModelFactory` to support Anthropic models. |
| **Micro-Context** (Logic/Testing) | Specific **Functionality** or **Hardcoded Values**: e.g., the hardcoded paths in `run_enhanced_pipeline.py`, the `setup_sample_files` logic, or the default `temperature=0.2` in `ai_models.py`. | Replacing a hardcoded path with a value from a new `config.py` file. |

***

### 2. Audit the Present State of the Codebase

Conduct a targeted review of the relevant codebase components to understand the current implementation and the *target* architecture.

* **Current Orchestration:** Review **`run_enhanced_pipeline.py`** to understand the *current* procedural logic, function calls, and hardcoded paths that need to be migrated.
* **Target Orchestration:** Review **`core/pipeline/material_ingestion_pipeline.py`** and **`core/agents/base_agent.py`**. All new functionality must be implemented as a class inheriting from `BaseAgent` and be registered with the `MaterialIngestionPipeline`.
* **Data Models:** Review **`core/agents/supervisor/schemas.py`** and example outputs (e.g., `output/knowledge_graph/knowledge_graph.json`) to understand the data structures being passed between agents.
* **Configuration:** Check **`core/utils/ai_models.py`** and **`run_enhanced_pipeline.py`** to identify all hardcoded values (model names, paths, parameters) that must be externalized.
* **Dependencies:** Verify required packages are listed in **`requirements.txt`**.
* **Entry Points:** Review **`run_component.py`** and **`run_and_visualize.py`** as candidates for replacement by a unified CLI.

***

### 3. Create an Organized Set of Sequential Tasks

Based on the audit, formulate a set of structured, sequential tasks. **Your priority is always to move away from `run_enhanced_pipeline.py` and into the formal class-based orchestrator.**

1.  **Create Configuration:** Create a new `config.py` file (or similar) that loads from `.env`. Identify and move all hardcoded paths and model settings from `run_enhanced_pipeline.py` and `core/utils/ai_models.py` into it.
2.  **Refactor Agents:** One by one, wrap the logic for each pipeline step (e.g., `extract_course_context`, `process_transcripts`) inside a new class that inherits from `core.agents.base_agent.BaseAgent`.
3.  **Refactor Orchestrator:** Modify the main entry point (create a new `main.py` or `cli.py`) to:
    * Import the `MaterialIngestionPipeline` class.
    * Import the newly refactored agent classes.
    * Register each agent to a stage (e.g., `pipeline.register_agent("context_extraction", ContextAgent(config))`).
    * Set the execution plan and call `pipeline.run()`.
4.  **Build CLI Interface:** Create a `cli.py` using `click` that allows users to run the main pipeline and pass in the *input/output directories* as arguments.
5.  **Implement Missing Agents:** Add new agents for missing functionality (like the "Vision Agent") and register them in the pipeline.
6.  **Develop Test Plan:** Define a `tests/` directory with unit tests for each agent and an integration test for the `MaterialIngestionPipeline`.

***

### 4. Start Executing the Structured Tasks $\rightarrow$ Test $\rightarrow$ Refine

Execute the tasks sequentially, focusing on modularity and configuration.

1.  **Execute & Test:** Implement the logic for the current subtask (e.g., "Externalize paths"). Immediately run the pipeline to ensure it still works with the new configuration.
2.  **Ensure Code Quality:** Before committing, verify compliance with project standards:
    * **No Hardcoding:** Ensure no new file paths or model names were hardcoded.
    * **Modularity:** Confirm the logic was added to the correct agent or module.
    * **Testing:** Write and pass a unit test for the new logic.
3.  **Refine & Complete:** Address all test failures. Once the current subtask is validated (e.g., the pipeline now runs using the `MaterialIngestionPipeline` class), proceed to the next task.
