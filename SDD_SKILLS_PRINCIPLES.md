# SDD Specification: Coder Agent Skill Development Principles

## Overview
This specification defines the core principles and architectural standards for developing coder agent skills within the SDD (Skill-Driven Development) framework. These principles ensure that skills are reusable, maintainable, and aligned with the established programming style of the project.

## Core Principles

### 1. Atomicity and Single Responsibility
Each skill must perform a single, well-defined task. 
- **Guideline**: If a skill requires more than 3 distinct steps or interacts with more than 2 separate services, it should be decomposed into smaller sub-skills.
- **Example**: Instead of `CreateFullFeature`, use `GeneratePydanticSchema`, `CreateServiceLogic`, and `AddApiRoute`.

### 2. Context Awareness (Project-Aware)
Skills must be designed to adapt to the target project's environment.
- **Initialization**: Before execution, a skill should scan for configuration files (e.g., `app/config.py`, `.env`) and existing patterns.
- **Standards**: Inherit existing logging formats, exception handling, and naming conventions (CamelCase for classes, snake_case for functions).

### 3. Schema-First Development
All data-driven skills must start with a formal schema definition.
- **Validation**: Use Pydantic models (placed in `app/models/schemas.py`) as the single source of truth for data contracts.
- **AI Integration**: When using LLMs for extraction or generation, always provide a Pydantic schema to enforce Structured Output.

### 4. Self-Documentation
Skills are responsible for maintaining the project's documentation standards.
- **Docstrings**: Every generated function or class must include Google-style docstrings.
- **Type Hinting**: Mandatory use of Python type hints for all parameters and return values.

### 5. Non-Blocking Execution
Since the framework is built on FastAPI, skills must respect the asynchronous nature of the application.
- **IO Operations**: Any blocking call (e.g., `subprocess`, heavy file IO) must be wrapped in `run_in_threadpool` or use asynchronous alternatives.

## Implementation Standards

### Skill Structure
A skill should be packaged with:
1. `SKILL.md`: Human-readable description and usage instructions.
2. `logic.py`: The executable code or prompt templates.
3. `tests/`: Unit tests ensuring the skill performs as expected.

### Error Handling
- Use the project's centralized logging system.
- Implement retries using `tenacity` for any external API dependencies (Gemini, Vertex AI, AlloyDB).

## Style Alignment
- **Personas**: Skills should reflect the "Polyphemus" persona—direct, analytical, and professional.
- **Formatting**: Adherence to `black` and `isort` standards.

## Evolution
This specification is a living document. As new patterns emerge in the `PDF2Alloydb` project, they should be distilled into these principles.
