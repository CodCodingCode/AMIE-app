from huggingface_hub import HfApi, HfFolder, upload_folder, create_repo

# Define repository details
username = "CodCodingCode"  # Replace with your Hugging Face username
repo_name = "llama-medical-diagnosis"  # Replace with your desired repository name
repo_id = f"{username}/{repo_name}"  # Full repository ID
local_dir = "./h100_fp16_peft_output"  # Path to your trained model directory

# Ensure the repository exists
api = HfApi()
try:
    api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
    print(f"Repository {repo_id} is ready.")
except Exception as e:
    print(f"Failed to create or access the repository: {e}")
    exit(1)

# Upload the model directory to Hugging Face
try:
    upload_folder(
        folder_path=local_dir,
        repo_id=repo_id,
        repo_type="model",  # Use "model" for model repositories
        token=HfFolder.get_token(),  # Automatically uses your logged-in token
    )
    print(f"Model uploaded to https://huggingface.co/{repo_id}")
except Exception as e:
    print(f"Failed to upload the model: {e}")
