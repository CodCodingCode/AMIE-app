import os
from huggingface_hub import HfApi, HfFolder

# 1) Configuration
LOCAL_FOLDER = "outputs/full_finetune"  # path to your fine-tuned model directory
REPO_ID = "CodCodingCode/llama-3.1-8b-clinical"  # target HF repo (create if needed)

# 2) Authenticate (reads from env var)
token = "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"
if not token:
    raise ValueError(
        "Please set the HUGGINGFACE_HUB_TOKEN environment variable before running this script."
    )
HfFolder.save_token(token)

# 3) Create the repository if it doesn't already exist
api = HfApi()
api.create_repo(repo_id=REPO_ID, exist_ok=True, token=token)

# 4) Upload all files under LOCAL_FOLDER to the root of the model repo
api.upload_folder(
    folder_path=LOCAL_FOLDER,
    path_in_repo="",
    repo_id=REPO_ID,
    token=token,
    repo_type="model",
)

print(f"✅ Uploaded contents of '{LOCAL_FOLDER}' to https://huggingface.co/{REPO_ID}")
