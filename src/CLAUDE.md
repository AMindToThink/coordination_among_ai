# AI Agent Coordination Research Codebase Guidelines

## Commands
- Run evaluations: `python 2v1Evaluation.py --config <config_file.json> [--limit N]`
- Basic evaluation: `python GroupChatEvaluator.py <model_name> <rate_limit>`
- Example: `python 2v1Evaluation.py --config 2v1Evaluation_configs/r1_saboteur2v1_config.json --limit 10`

## Code Style
- Python version: 3.8+
- Type hints for function parameters and return values
- Snake_case for files/functions, CamelCase for classes
- Docstrings for classes and functions
- Use autogen_agentchat and autogen_core conventions
- Async/await pattern for parallel execution
- Configuration via JSON files in 2v1Evaluation_configs/
- Exception handling with try/finally blocks
- Assertions for validation

## Code Structure
- Main evaluation logic in GroupChatEvaluator.py
- Prompting templates in prompting.py
- VoteMentionTermination.py defines termination conditions
- Results stored in 2v1Evaluation_results/ and results/ directories