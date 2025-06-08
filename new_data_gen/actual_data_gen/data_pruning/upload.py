from datasets import Dataset, DatasetDict
import json

with open("combined_conversations.json") as f:
    raw_data = json.load(f)

dataset = Dataset.from_list(raw_data)
dataset.push_to_hub("CodCodingCode/clinical-conversations-V1.2")
