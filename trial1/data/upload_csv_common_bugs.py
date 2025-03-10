from datasets import Dataset, Features, Sequence, Value
import pandas as pd
import json

# Read your CSV
df = pd.read_csv('coding-quiz-csv-reformatted.csv')
df2 = pd.read_csv('coding-quiz-csv-expanded.csv')
# Parse the choices column from string to dict
df['choices'] = df['choices'].apply(json.loads)

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

# Convert to Hugging Face dataset
dataset = Dataset.from_pandas(df, features=features)

# Push to hub
import os
dataset.push_to_hub('AMindToThink/common_bugs', token=os.environ.get('HUGGINGFACE_WRITE_KEY', None))
