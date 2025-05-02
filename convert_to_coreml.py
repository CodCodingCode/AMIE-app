import coremltools as ct
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load your trained model - example with a fine-tuned LLM
model_path = "./results/medical_diagnostic_model"  # Your model's path
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

# For smaller models like classification models:
# Convert to Core ML format
# This is just an example - actual conversion depends on your model type
mlmodel = ct.convert(
    model,
    inputs=[ct.TensorType(name="input_ids", shape=(1, 128), dtype=np.int32)],
    minimum_deployment_target=ct.target.iOS15,
)

# Save the Core ML model
mlmodel.save("MedicalDiagnosticModel.mlmodel")

print("Model converted and saved as MedicalDiagnosticModel.mlmodel")
