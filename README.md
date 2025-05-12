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

