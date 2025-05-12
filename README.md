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
├── doctor_oriented_qa_with_ids.jsonl # Doctor-patient dialogue dataset
├── doctor_patient_qa.jsonl         # Doctor-patient dialogue dataset (potentially different format/source)
├── aci-bench/                      # Benchmarking suite for clinical NLP tasks (e.g., Automatic Clinical Impression)
│   ├── README.md
│   ├── SETUP.md
│   ├── baselines/                  # Baseline model implementations for the benchmark
│   ├── data/                       # Datasets for the aci-bench benchmark
│   ├── evaluation/                 # Evaluation scripts for the benchmark
│   ├── metric/                     # Custom metrics for evaluation
│   ├── results/                    # Stored results from benchmark runs
│   └── tables/                     # Formatted tables of benchmark results
├── datasets/                       # General datasets for model training and experimentation
│   ├── SFT/                        # Datasets specifically for Supervised Fine-Tuning
│   │   ├── counter_d.json          # Dataset for counter-deductive reasoning questions
│   │   ├── augmented_clinical_notes_qa.jsonl # (If present) Augmented QA from clinical notes
│   │   └── combined_dataset.jsonl    # (If present) A combined dataset for SFT
│   ├── icliniq.json                # (If present) Dataset from iCliniq
│   ├── prompts_gpto1mini_0912_toshare.json # Dataset of prompts
│   └── other/                      # Other miscellaneous datasets
├── doctorpoc/                      # Proof-of-concept for the "AI Doctor" diagnostic process
│   └── src/
│       ├── __init__.py
│       ├── agents/
│       │   └── probability_agent.py # Agent for managing disease probabilities
│       ├── models/
│       │   ├── __init__.py
│       │   ├── blocks.py           # Defines different diagnostic questioning blocks (early, late, expanding)
│       │   └── case.py             # Defines patient case structures and example cases
│       ├── runners/
│       │   ├── __init__.py
│       │   ├── diagnostic_utils.py # Utilities for the diagnostic process
│       │   ├── run_counter.py      # Runner for counter-deductive questions
│       │   ├── run_deductive.py    # Runner for deductive/elimination questions
│       │   ├── run_expand.py       # Runner for expanding disease hypotheses
│       │   ├── run_gpt.py          # Runner for GPT-based doctor benchmark
│       │   └── run_info_gain.py    # Runner for information gain based questions
│       ├── benchmark_main.py       # Main script for running benchmarks on the diagnostic process
│       └── working.py              # Main script for running/testing the modular diagnostic process
├── explanation/
│   └── file_explanation.txt        # Developer notes and explanations of various project files
├── machine_learning/
│   ├── SFT/                        # Scripts and resources for Supervised Fine-Tuning
│   │   ├── guide.txt               # Guide or notes on SFT process
│   │   └── train_llama_maverick.py # Training script for SFT (e.g., on Llama3-OpenBioLLM)
│   ├── dataset_generation/         # Scripts for creating or transforming datasets
│   │   ├── patient_GRPO.py         # Script to transform prompts for GRPO/PPO
│   │   └── SFT/
│   │       └── iCliniq/
│   │           └── add.py          # Script to convert iCliniq data to instruction format
│   └── GRPO/                       # Scripts and resources for GRPO/PPO
│       └── perform_grpo.py         # Script to perform GRPO (combines SFT and PPO)
├── sft_output/                     # Default output directory for SFT models
└── ... (other_project_files_or_directories)/ # Placeholder for any other top-level items
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

