# Read our report [here](https://docs.google.com/document/d/1dogqMtQU0etSDeAtb06RIWhXnuhXe9LOC45Yh_2-_ao/edit?usp=sharing).
# To evaluate an AI team (optionally with saboteurs):
```
cd src
```
make a config json file. For example `src/NVK_evaluation_configs/common_bugs_dataset/4o/common_bugs_config_sabotage03-09.json`:

```
{
  "model": "gpt-4o-mini-2024-07-18",
  "collaborators": 2,
  "saboteurs": 1,
  "rate_limit": 0.0,
  "turns": 2,
  "output_dir": "./results/model_counts/in_order/common_bugs_dataset",
  "log_file": "{filename}_chat_logs.txt",
  "end_condition": "turns",
  "dataset_dict": {
    "path": "AMindToThink/common_bugs",
    "split": "train"
  }
}
```
Evaluates gpt 4o mini on a team with 2 collaborators and 1 saboteur. Each model gets 2 turns to speak. It evaluates on the train split of the common_bugs dataset, and saves the output and logs.

run the test with 
```
python NvKEvaluation.py --config <path to config> --limit (optional, defaults to no limit. If provided, only does evaluates on the first `limit` questions)
```

# To evaluate i saboteurs vs i + 1 collaborators
```
cd src
```
Make a base config file, for example `src/i_plus_one_vs_i_configs/base_config_1.json`

```
{
  "model": "gpt-4o-mini-2024-07-18",
  "rate_limit": 0.0,
  "turns": 2,
  "output_dir": "./results/i_plus_one_vs_i",
  "log_file": "{filename}_chat_logs.txt",
  "end_condition": "turns",
  "max_i": 10,
  "iterations": 5
}
```

This tests GPT-4o mini for i from 0 to 10 (inclusive) for 2 turns each question and for 5 iterations (so you can find confidence intervals).

# To find the summary statistics of a folder of json:
```cd src
python summary_statistics.py <Directory containing evaluation JSON files (e.g., "./results/model_counts/triple_sabotage_no_colab")>
```
# Interpretation
## to make a plot from i vs i + 1, 
use `src/interpretation/i_plus_one_vs_i_viewer.py`

## To find the successful sabotage examples:
You need to use the two scripts `src/interpretation/sabotage_success_finder.py` and `src/interpretation/sabotage_success_printer.py`.
You use the finder script first:
Give it the json results file without sabotage and the json results with sabotage. Give it a the place to create the output file with `--output`.
Then use the `printer`. It takes the output from the `finder`, the log file from the experiment, and `--output` as a path to where to store the printer's results. 
The result of this is a file which contains the logs of the questions where the saboteur succeeded.

# Note:
All API keys are removed. Go to the relevant website to get your own api key and make it an environment variable.
