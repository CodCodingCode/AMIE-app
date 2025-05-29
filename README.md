# AMIE-app

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![License](https://img.shields.io/badge/license-MIT-blue)

AMIE (Artificial Medical Intelligence Engine) is the most accurate AI doctor, designed to provide medical diagnostics with unparalleled precision and reliability.

## NEIGHBOURHOOD INFORMATION:

Here is my model please use for the medical-test repo! [Model](ttps://huggingface.co/spaces/CodCodingCode/medical-test/tree/main)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Machine Learning Approach](#machine-learning-approach)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

## Overview

This application leverages advanced machine learning models trained on comprehensive medical datasets to deliver accurate diagnostic suggestions and medical guidance. AMIE aims to assist healthcare professionals with accurate diagnostics and provide reliable medical information to patients.

## Features

- Highly accurate medical diagnostics
- Natural language understanding of patient symptoms
- Evidence-based medical recommendations
- User-friendly interface for both patients and healthcare providers
- Automated patient vignette generation from conversations
- Treatment plan generation

## Installation

### Prerequisites

- Python 3.8+
- PyTorch 1.13+
- Hugging Face Transformers library

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/AMIE-app.git
cd AMIE-app

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download necessary model weights (if applicable)
python scripts/download_models.py
```

## Usage

### Diagnostic Process

```python
from doctorpoc.src import working

# Initialize the diagnostic process
diagnosis = working.start_diagnostic_process(patient_data)

# Get diagnostic questions
questions = diagnosis.get_next_questions()

# Process patient responses
diagnosis.update_with_responses(patient_responses)

# Get final diagnosis
final_diagnosis = diagnosis.get_diagnosis()
```

### Fine-tuning AMIE Model

```bash
# Run Supervised Fine-Tuning
python machine_learning/SFT/train_llama_maverick.py --dataset datasets/SFT/combined_dataset.jsonl

# Run GRPO optimization
python machine_learning/GRPO/perform_grpo.py --model-path sft_output/model
```

## File Structure

```
AMIE-app/
├── .gitignore
├── README.md
├── todos.txt
├── requirements.txt                # Project dependencies

# ===== Datasets =====
├── datasets/                       # General datasets for model training and experimentation
│   ├── SFT/                        # Datasets for Supervised Fine-Tuning
│   │   ├── counter_d.json          # Dataset for counter-deductive reasoning questions
│   │   ├── augmented_clinical_notes_qa.jsonl # Augmented QA from clinical notes
│   │   └── combined_dataset.jsonl  # Combined dataset for SFT
│   ├── SFT-FUTURE/                 # Future/planned SFT datasets
│   │   ├── generalize1.json        # Generalization dataset 1
│   │   ├── generalize2.json        # Generalization dataset 2
│   │   └── converted_augmented_clinical_notes_qa.jsonl
│   ├── icliniq.json                # Dataset from iCliniq
│   ├── prompts_gpto1mini_0912_toshare.json # Dataset of prompts
│   └── other/                      # Other miscellaneous datasets
├── medical_dataset/                # Core medical knowledge database
├── doctor_oriented_qa_with_ids.jsonl # Doctor-patient dialogue dataset
├── doctor_patient_qa.jsonl         # Doctor-patient dialogue dataset

# ===== Diagnostic Process Components =====
├── questioning_doctor_outputs/     # Outputs from questioning phase
├── patient_followups/              # Patient follow-up data
├── summarizer_outputs/             # Conversation summary outputs
├── diagnosing_doctor_outputs/      # Diagnostic outputs
├── treatment_plans/                # Generated treatment plans
├── validated_disease_vignettes.json # Verified disease presentations

# ===== Benchmarking Tools =====
├── aci-bench/                      # Benchmarking suite for clinical NLP tasks
│   ├── README.md
│   ├── SETUP.md
│   ├── baselines/                  # Baseline model implementations
│   ├── data/                       # Benchmark datasets
│   ├── evaluation/                 # Evaluation scripts
│   ├── metric/                     # Custom metrics
│   ├── results/                    # Stored results
│   └── tables/                     # Formatted results tables

# ===== Diagnostic Process Implementation =====
├── doctorpoc/                      # Proof-of-concept for the "AI Doctor"
│   └── src/
│       ├── __init__.py
│       ├── agents/
│       │   └── probability_agent.py # Agent for disease probabilities
│       ├── models/
│       │   ├── __init__.py
│       │   ├── blocks.py           # Diagnostic questioning blocks
│       │   └── case.py             # Patient case structures
│       ├── runners/
│       │   ├── __init__.py
│       │   ├── diagnostic_utils.py # Diagnostic utilities
│       │   ├── run_counter.py      # Counter-deductive questions runner
│       │   ├── run_deductive.py    # Deductive/elimination questions runner
│       │   ├── run_expand.py       # Disease hypothesis expansion runner
│       │   ├── run_gpt.py          # GPT-based doctor benchmark
│       │   └── run_info_gain.py    # Information gain questions runner
│       ├── benchmark_main.py       # Benchmarking script
│       └── working.py              # Main diagnostic process script

# ===== Machine Learning Components =====
├── machine_learning/
│   ├── SFT/                        # Supervised Fine-Tuning resources
│   │   ├── guide.txt               # SFT process guide
│   │   └── train_llama_maverick.py # Training script for SFT
│   ├── dataset_generation/         # Dataset creation scripts
│   │   ├── patient_GRPO.py         # Transform prompts for GRPO/PPO
│   │   └── SFT/
│   │       └── iCliniq/
│   │           └── add.py          # Convert iCliniq data to instructions
│   └── GRPO/                       # GRPO/PPO resources
│       ├── perform_grpo.py         # Script to perform GRPO
│       └── summarize.py            # Conversation to Patient Vignette converter
├── sft_output/                     # Default output directory for SFT models
├── explanation/
│   └── file_explanation.txt        # Developer notes on project files
```

## Machine Learning Approach

Our core machine learning strategy involves a two-stage process to develop a highly capable medical AI:

1.  **Supervised Fine-Tuning (SFT):**

    - We plan to start by fine-tuning powerful pre-trained language models. The primary candidates for this stage are **BioLlama 8B** (a Llama model specialized for the biomedical domain) or **Llama 4 Maverick**.
    - SFT will be performed using curated medical datasets, including question-answer pairs, clinical notes, and medical dialogues, to adapt the base model to understand and generate clinically relevant text. The datasets in the `datasets/SFT/` directory are intended for this purpose.

2.  **Reinforcement Learning (RL) for Response Optimization:**
    - Following SFT, we intend to further refine the model's responses using reinforcement learning techniques.
    - Specifically, we are exploring methods like **GRPO (Generative Reinforcement Policy Optimization)** or **PPO (Proximal Policy Optimization)**.
    - The goal of this RL stage is to improve the quality, safety, and helpfulness of the model's outputs by training it against a reward model that scores responses based on medical accuracy, clarity, and adherence to clinical guidelines. This will help in generating more nuanced and contextually appropriate medical advice or diagnostic questions.

This iterative approach of SFT followed by RL aims to create a robust and reliable AI doctor.

## Roadmap

### Short-term Goals

- Add treatment plan output capabilities to both dataset and model
- Implement grounding mechanisms to prevent hallucinations
- Complete frontend application with Google authentication
- Create datasets for information gain, counter-deductive, and deductive reasoning
- Develop automated patient vignette generation from conversations

### Long-term Goals

- Enhance diagnostic accuracy through iterative model improvements
- Expand support for multiple medical specialties
- Develop mobile applications for broader accessibility
- Implement multilingual support
- Secure relevant medical certifications and compliance

## Contributing

We welcome contributions to AMIE-app! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
