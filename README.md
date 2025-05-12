# AMIE-app

AMIE (Artificial Medical Intelligence Engine) is the most accurate AI doctor, designed to provide medical diagnostics with unparalleled precision and reliability.

## Overview

This application leverages advanced machine learning models trained on comprehensive medical datasets to deliver accurate diagnostic suggestions and medical guidance.

## Features

- Highly accurate medical diagnostics
- Natural language understanding of patient symptoms
- Evidence-based medical recommendations
- User-friendly interface for both patients and healthcare providers

## File Structure

```
AMIE-app/
├── .gitignore
├── README.md
├── todos.txt
├── aci-bench/                  # Benchmarking suite for clinical NLP tasks
│   ├── README.md
│   ├── SETUP.md
│   ├── baselines/              # Baseline model implementations
│   ├── data/                   # Benchmark datasets
│   └── evaluation/             # Evaluation scripts
├── datasets/                   # Datasets for training and experimentation
│   ├── SFT/                    # Datasets for Supervised Fine-Tuning
│   │   ├── counter_d.json
│   │   ├── augmented_clinical_notes_qa.jsonl
│   │   └── combined_dataset.jsonl
│   └── icliniq.json
├── doctorpoc/                  # Proof-of-concept or components for "doctor" functionality
│   └── src/
│       ├── __init__.py
│       └── models/
│           └── __init__.py
├── explanation/
│   └── file_explanation.txt    # Explanations of different project files
├── machine_learning/
│   ├── SFT/                    # Scripts and guides for Supervised Fine-Tuning
│   │   ├── guide.txt
│   │   ├── train_llama_maverick.py  # Example SFT training script (if present)
│   │   └── iCliniq/                 # iCliniq specific SFT processing
│   │       └── add.py
│   ├── dataset_generation/     # Scripts for generating or processing datasets
│   │   └── SFT/
│   │       └── iCliniq/
│   │           └── add.py      # Script to process iCliniq data (from your active file)
│   └── ... (other_ml_components)/
├── sft_output/                 # Default output directory for SFT models (from .gitignore)
└── ... (other_project_files_or_directories)/
```

## Machine Learning Approach

Our core machine learning strategy involves a two-stage process to develop a highly capable medical AI:

1.  **Supervised Fine-Tuning (SFT):**
    *   We plan to start by fine-tuning powerful pre-trained language models. The primary candidates for this stage are **BioLlama 8B** (a Llama model specialized for the biomedical domain) or **Llama 4 Maverick**.
    *   SFT will be performed using curated medical datasets, including question-answer pairs, clinical notes, and medical dialogues, to adapt the base model to understand and generate clinically relevant text. The datasets in the `datasets/SFT/` directory are intended for this purpose.

2.  **Reinforcement Learning (RL) for Response Optimization:**
    *   Following SFT, we intend to further refine the model's responses using reinforcement learning techniques.
    *   Specifically, we are exploring methods like **GRPO (Generative Reinforcement Policy Optimization)** or **PPO (Proximal Policy Optimization)**.
    *   The goal of this RL stage is to improve the quality, safety, and helpfulness of the model's outputs by training it against a reward model that scores responses based on medical accuracy, clarity, and adherence to clinical guidelines. This will help in generating more nuanced and contextually appropriate medical advice or diagnostic questions.

This iterative approach of SFT followed by RL aims to create a robust and reliable AI doctor.

