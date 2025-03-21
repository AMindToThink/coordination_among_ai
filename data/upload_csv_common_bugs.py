from datasets import Dataset, Features, Sequence, Value
import pandas as pd
import json
import os

# Read your CSV files
df_first_five = pd.read_csv('coding-quiz-csv-reformatted.csv')
df_first_fifteen = pd.read_csv('coding-quiz-csv-expanded.csv')

# Parse the choices column from string to dict for both dataframes
df_first_five['choices'] = df_first_five['choices'].apply(json.loads)
df_first_fifteen['choices'] = df_first_fifteen['choices'].apply(json.loads)

# Define the features schema
features = Features({
    'id': Value('string'),
    'question': Value('string'),
    'choices': Sequence({
        'label': Value('string'),
        'text': Value('string')
    }),
    'answerKey': Value('string')
})

# Convert to Hugging Face datasets
dataset_first_five = Dataset.from_pandas(df_first_five, features=features)
dataset_first_fifteen = Dataset.from_pandas(df_first_fifteen, features=features)

# Push each dataset separately with its own name
dataset_first_five.push_to_hub(
    'AMindToThink/common_bugs', 
    token=os.environ.get('HUGGINGFACE_WRITE_KEY', None),
    config_name="first_five"
)

dataset_first_fifteen.push_to_hub(
    'AMindToThink/common_bugs', 
    token=os.environ.get('HUGGINGFACE_WRITE_KEY', None),
    config_name="first_fifteen"
)

# Also push first_five as the default configuration
dataset_first_five.push_to_hub(
    'AMindToThink/common_bugs', 
    token=os.environ.get('HUGGINGFACE_WRITE_KEY', None),
    config_name="default"
)
