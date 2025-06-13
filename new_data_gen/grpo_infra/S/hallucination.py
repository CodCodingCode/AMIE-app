import os
import re
from datasets import load_dataset
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import GRPOConfig, GRPOTrainer
import torch

# ─── 0. HF TOKEN ─────────────────────────────────────────────────
HF_TOKEN = "token"
print("[debug] HF_TOKEN:", HF_TOKEN[:8] + "…" if HF_TOKEN else None)
if not HF_TOKEN:
    raise RuntimeError("Missing HUGGINGFACE_HUB_TOKEN")

# ─── 1. Download model + checkpoint via snapshot_download ────────
REPO_ID = "CodCodingCode/llama-3.1-8b-clinical-v1.3"
SUBFOLDER = "checkpoint-6508"
print(f"[debug] Downloading {REPO_ID}…")
cache_dir = snapshot_download(repo_id=REPO_ID, token=HF_TOKEN)
print("[debug] snapshot_download complete, cache_dir:", cache_dir)
model_path = os.path.join(cache_dir, SUBFOLDER)
tokenizer_path = cache_dir
print("[debug] model_path exists?", os.path.isdir(model_path))
print("[debug] tokenizer_path exists?", os.path.isdir(tokenizer_path))

# ─── 2. Load tokenizer & model from disk ─────────────────────────
print("[debug] Loading tokenizer from:", tokenizer_path)
hf_tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, use_fast=True)
print("[debug] hf_tokenizer type:", type(hf_tokenizer))

print("[debug] Loading model from:", model_path)
hf_model = AutoModelForCausalLM.from_pretrained(
    model_path,
    device_map="auto",
    torch_dtype=torch.bfloat16,  # ← load weights in BF16
)
hf_model.gradient_checkpointing_enable()
print("[debug] hf_model loaded. device_map:", hf_model.hf_device_map)

# ─── 3. Load & filter your dataset ────────────────────────────────
print("[debug] Loading clinical-conversations dataset…")
ds = load_dataset("CodCodingCode/clinical-conversations-V1.2", split="train")
print("[debug] Original dataset size:", len(ds))
ds = ds.filter(
    lambda ex: ex["instruction"]
    != "You are simulating a real patient in conversation with their doctor."
)
print("[debug] Filtered dataset size:", len(ds))


# ─── 4. Build prompt‐only column ──────────────────────────────────
def make_prompt(ex):
    instr = ex["instruction"].strip()
    inp = ex.get("input", "").strip()

    full = f"""Instruction: {instr} 
    Input: {(inp if inp else "")} 
    Output: THINKING: 
    """
    return {"prompt": full}


print("[debug] Mapping make_prompt…")
prompt_ds = ds.map(make_prompt, remove_columns=ds.column_names)
print("[debug] prompt_ds columns:", prompt_ds.column_names)
print("[debug] example prompt:", prompt_ds[0]["prompt"][:200].replace("\n", "\\n"))


# ─── 5. Tokenize (batched!) ───────────────────────────────────────
# ─── 5. Tokenize ──────────────────────────────────────────────────
def tokenize_batch(batch):
    print(f"[debug] Tokenizing batch of size: {len(batch['prompt'])}")
    out = hf_tokenizer(
        batch["prompt"],
        truncation=True,
        padding="max_length",
        max_length=512,
    )
    return out


print("[debug] Starting tokenization…")
# remove remove_columns, so prompt stays in the dataset
tokenized = prompt_ds.map(
    tokenize_batch,
    batched=True,
    # remove_columns=["prompt"],  ←←←  drop this line
)
print("[debug] Tokenized columns:", tokenized.column_names)
# you'll now see ['prompt','input_ids','attention_mask']
print("[debug] Tokenized dataset columns:", tokenized.column_names)
print(
    "[debug] Example tokenized features:",
    {k: tokenized[0][k] for k in tokenized.column_names},
)


# ─── 6. Define your ChatGPT-based anti-hallucination reward fn ────────────────────
from openai import OpenAI
from itertools import islice
import random
import json

# Initialize OpenAI client
client = OpenAI(api_key="api")
model = "gpt-4.1-nano"


def run_summarizer_hallucination_check(idx, completion, conversation_history):
    try:
        evaluation_prompt = f"""You are an expert clinical fact-checker. Compare the patient conversation with the clinical summary to identify genuine problems.

PATIENT CONVERSATION:
{conversation_history}

CLINICAL SUMMARY TO EVALUATE:
{completion}

IMPORTANT DISTINCTIONS:

HALLUCINATIONS (ONLY count these - things that are factually wrong):
- Symptoms the patient explicitly denied or never mentioned
- Demographics that contradict patient statements (wrong age, gender, etc.)
- Specific details that are fabricated (exact frequencies, durations, severity levels not provided)
- Medical history the patient never mentioned

DO NOT count as hallucinations:
- Reasonable clinical interpretations ("suggests possible diagnosis")
- Standard clinical language ("patient reports", "indicates", "appears")
- Paraphrasing patient statements in clinical terms
- Clinical observations about communication patterns

CRITICAL OMISSIONS (ONLY count truly important missing information):
- Major symptoms the patient clearly described but summary completely missed
- Key demographic information patient provided
- Significant timeline information (duration, onset) patient specified
- Important context that changes clinical picture

DO NOT count as omissions:
- Minor wording differences ("sometimes" vs "occasionally") 
- Exact quotes vs reasonable paraphrasing
- Details that don't significantly impact clinical understanding
- Missing information that patient was vague about

ACCURATE ITEMS (give credit for):
- Correctly captured symptoms and concerns
- Accurate demographics and timeline information
- Appropriate clinical interpretations of patient statements
- Reasonable paraphrasing that preserves meaning

Respond with ONLY a JSON object:
{{"hallucinated_items": ["specific fabricated fact 1", "specific fabricated fact 2"], "omitted_items": ["major missing symptom", "important timeline"], "accurate_items": ["correct symptom", "accurate demographic", "appropriate interpretation"], "score": 0}}

Base score calculation: -3 points per hallucination, -1 point per critical omission, +1 point per accurate item. Range: -10 to +10."""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": evaluation_prompt}],
            temperature=0.1,
            max_tokens=1000,  # Increased to prevent truncation
        )

        raw_content = response.choices[0].message.content.strip()

        # ROBUST JSON EXTRACTION - MULTIPLE STRATEGIES
        score = 0.0

        # Strategy 1: Try to find complete JSON
        json_matches = re.findall(
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", raw_content, re.DOTALL
        )

        for json_candidate in json_matches:
            try:
                # Clean up the JSON string
                cleaned_json = json_candidate.strip()
                # Fix common issues
                cleaned_json = re.sub(
                    r",\s*}", "}", cleaned_json
                )  # Remove trailing commas
                cleaned_json = re.sub(
                    r",\s*]", "]", cleaned_json
                )  # Remove trailing commas in arrays

                result = json.loads(cleaned_json)
                score = float(result.get("score", 0.0))
                hallucinated = result.get("hallucinated_items", [])
                omitted = result.get("omitted_items", [])
                accurate = result.get("accurate_items", [])

                # CALCULATE EXPECTED SCORE BASED ON YOUR RULES
                expected_score = 0
                expected_score -= 2 * len(hallucinated)  # -2 per hallucination
                print(hallucinated)
                expected_score -= 1 * len(omitted)  # -1 per omission
                print(omitted)
                expected_score += 0.5 * len(accurate)  # +0.5 per accurate
                print(accurate)
                expected_score = max(-10, min(10, expected_score))
                expected_score = expected_score / 2

                print(
                    f"[debug reward] #{idx} → ChatGPT score: {score}, CALCULATED score: {expected_score}, hallucinated: {len(hallucinated)}, omitted: {len(omitted)}, accurate: {len(accurate)}"
                )

                # USE THE CALCULATED SCORE INSTEAD OF CHATGPT'S SCORE
                score = expected_score
                break  # Success!

            except json.JSONDecodeError:
                continue  # Try next JSON candidate

        else:
            # Strategy 2: Extract just the score if JSON parsing fails
            score_match = re.search(r'"score":\s*(-?\d+(?:\.\d+)?)', raw_content)
            if score_match:
                score = float(score_match.group(1))
                print(f"[debug reward] #{idx} → extracted score only: {score}")
            else:
                print(f"[debug reward] #{idx} → JSON parsing failed, using 0.0")
                score = 0.0

        # Ensure score is in valid range
        return max(-10, min(10, score))

    except Exception as e:
        print(f"[debug reward] #{idx} → API error: {e}")
        score = 0.0


def run_questionning_agent_check(idx, differential, vignette, completion):
    try:
        evaluation_prompt = f"""You are an expert clinical fact-checker. Compare the *Differential Diagnosis & Vignette Summary* (considered as the source facts) with the *questions generated by the model* to identify any hallucinations or omissions.

SOURCE (DIFFERENTIAL + VIGNETTE SUMMARY):
{differential} + {vignette}

MODEL-GENERATED QUESTIONS:
{completion}

IMPORTANT DISTINCTIONS:

HALLUCINATIONS (things that should be *punished*):
- Questions introducing symptoms, demographics, or history not in the source.
- Asking about conditions or tests not suggested by the summary.

OMISSIONS (also penalized if serious):
- Failing to ask about key symptoms, history, timeline, or findings explicitly mentioned in source.
- Ignoring major differential diagnoses that require exploration.

DO NOT penalize:
- Paraphrasing source content into question form.
- Asking reasonable follow-up clarifications based only on the source.

CORRECT ITEMS (should be rewarded):
- Questions correctly focusing on major symptoms, history, timeline, or differential considerations present in the source.
- Appropriately structured clinical questions that align directly with vignette information.

Respond with ONLY a JSON object:
{{
  "hallucinated_items": [<list of invented or irrelevant questions>],
  "omitted_items": [<list of key source aspects not questioned>],
  "accurate_items": [<list of well-grounded questions>],
  "score": <integer from -10 to +10>
}}

SCORING RULES:
- Each hallucinated question: −3 points
- Each serious omission: −2 points
- Each accurate/good question: +1 point
- Final score clipped to range [−10, +10]"""
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": evaluation_prompt}],
            temperature=0.1,
            max_tokens=1000,  # Increased to prevent truncation
        )

        raw_content = response.choices[0].message.content.strip()

        # ROBUST JSON EXTRACTION - MULTIPLE STRATEGIES
        score = 0.0

        # Strategy 1: Try to find complete JSON
        json_matches = re.findall(
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", raw_content, re.DOTALL
        )

        for json_candidate in json_matches:
            try:
                # Clean up the JSON string
                cleaned_json = json_candidate.strip()
                # Fix common issues
                cleaned_json = re.sub(
                    r",\s*}", "}", cleaned_json
                )  # Remove trailing commas
                cleaned_json = re.sub(
                    r",\s*]", "]", cleaned_json
                )  # Remove trailing commas in arrays

                result = json.loads(cleaned_json)
                score = float(result.get("score", 0.0))
                hallucinated = result.get("hallucinated_items", [])
                omitted = result.get("omitted_items", [])
                accurate = result.get("accurate_items", [])

                # CALCULATE EXPECTED SCORE BASED ON YOUR RULES
                expected_score = 0
                expected_score -= 2 * len(hallucinated)  # -2 per hallucination
                print(hallucinated)
                expected_score -= 1 * len(omitted)  # -1 per omission
                print(omitted)
                expected_score += 0.5 * len(accurate)  # +0.5 per accurate
                print(accurate)
                expected_score = max(-10, min(10, expected_score))

                print(
                    f"[debug reward] #{idx} → ChatGPT score: {score}, CALCULATED score: {expected_score}, hallucinated: {len(hallucinated)}, omitted: {len(omitted)}, accurate: {len(accurate)}"
                )

                # USE THE CALCULATED SCORE INSTEAD OF CHATGPT'S SCORE
                score = expected_score
                break  # Success!

            except json.JSONDecodeError:
                continue  # Try next JSON candidate

        else:
            # Strategy 2: Extract just the score if JSON parsing fails
            score_match = re.search(r'"score":\s*(-?\d+(?:\.\d+)?)', raw_content)
            if score_match:
                score = float(score_match.group(1))
                print(f"[debug reward] #{idx} → extracted score only: {score}")
            else:
                print(f"[debug reward] #{idx} → JSON parsing failed, using 0.0")
                score = 0.0

        # Ensure score is in valid range
        return max(-10, min(10, score))

    except Exception as e:
        print(f"[debug reward] #{idx} → API error: {e}")
        score = 0.0


def run_treatment_plan_check(idx, differential, vignette, conversation, completion):
    try:
        evaluation_prompt = f"""You are an expert clinical fact-checker. Your task is to evaluate whether the following *treatment plan* is accurate, grounded in the provided clinical context, and free from hallucinated medical content.

SOURCE FACTS:

DIFFERENTIAL DIAGNOSIS:
{differential}

VIGNETTE SUMMARY:
{vignette}

PATIENT CONVERSATION:
{conversation}

MODEL-GENERATED TREATMENT PLAN:
{completion}

EVALUATION CRITERIA:

❌ HALLUCINATIONS (DO penalize):
- Treatments unrelated to any condition in the differential
- Medications, procedures, or diagnostics not justified by the vignette or conversation
- Referrals to specialists for conditions not supported by context
- Any fabricated symptoms, test results, or patient preferences

⚠️ OMISSIONS (DO penalize):
- Not treating or addressing the most likely or dangerous conditions in the differential
- Ignoring clear patient-reported symptoms or clinical red flags
- Failure to recommend necessary follow-ups or safety netting for key conditions

✅ CORRECT ITEMS (DO reward):
- Treatments clearly justified by patient symptoms or the differential
- Appropriate first-line therapies and safety guidance
- Well-structured, realistic, patient-appropriate care plans based on the vignette and dialogue

DO NOT penalize:
- Clinical wording differences (“NSAID” vs “ibuprofen”)
- Reasonable interpretation of ambiguous information
- Standard phrasing of treatment guidance

Respond with ONLY a JSON object:
{{
  "hallucinated_items": ["unjustified antibiotic for viral case", "referral to cardiology with no relevant symptoms"],
  "omitted_items": ["no plan for severe abdominal pain", "no follow-up for red-flag headache"],
  "accurate_items": ["recommendation for migraine treatment", "safety-netting advice for return precautions"],
  "score": 0
}}

SCORING RULES:
- Deduct 3 points per hallucinated treatment recommendation
- Deduct 2 points per serious omission of necessary care
- Add 1 point per accurate and clinically appropriate treatment action
- Final score should be clipped between −10 and +10
"""
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": evaluation_prompt}],
            temperature=0.1,
            max_tokens=1000,  # Increased to prevent truncation
        )

        raw_content = response.choices[0].message.content.strip()

        # ROBUST JSON EXTRACTION - MULTIPLE STRATEGIES
        score = 0.0

        # Strategy 1: Try to find complete JSON
        json_matches = re.findall(
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", raw_content, re.DOTALL
        )

        for json_candidate in json_matches:
            try:
                # Clean up the JSON string
                cleaned_json = json_candidate.strip()
                # Fix common issues
                cleaned_json = re.sub(
                    r",\s*}", "}", cleaned_json
                )  # Remove trailing commas
                cleaned_json = re.sub(
                    r",\s*]", "]", cleaned_json
                )  # Remove trailing commas in arrays

                result = json.loads(cleaned_json)
                score = float(result.get("score", 0.0))
                hallucinated = result.get("hallucinated_items", [])
                omitted = result.get("omitted_items", [])
                accurate = result.get("accurate_items", [])

                # CALCULATE EXPECTED SCORE BASED ON YOUR RULES
                expected_score = 0
                expected_score -= 2 * len(hallucinated)  # -2 per hallucination
                print(hallucinated)
                expected_score -= 1 * len(omitted)  # -1 per omission
                print(omitted)
                expected_score += 0.5 * len(accurate)  # +0.5 per accurate
                print(accurate)
                expected_score = max(-10, min(10, expected_score))

                print(
                    f"[debug reward] #{idx} → ChatGPT score: {score}, CALCULATED score: {expected_score}, hallucinated: {len(hallucinated)}, omitted: {len(omitted)}, accurate: {len(accurate)}"
                )

                # USE THE CALCULATED SCORE INSTEAD OF CHATGPT'S SCORE
                score = expected_score
                break  # Success!

            except json.JSONDecodeError:
                continue  # Try next JSON candidate

        else:
            # Strategy 2: Extract just the score if JSON parsing fails
            score_match = re.search(r'"score":\s*(-?\d+(?:\.\d+)?)', raw_content)
            if score_match:
                score = float(score_match.group(1))
                print(f"[debug reward] #{idx} → extracted score only: {score}")
            else:
                print(f"[debug reward] #{idx} → JSON parsing failed, using 0.0")
                score = 0.0

        # Ensure score is in valid range
        return max(-10, min(10, score))

    except Exception as e:
        print(f"[debug reward] #{idx} → API error: {e}")
        score = 0.0


def run_diagnostic_model_check(idx, completion, conversation, vignette):
    try:
        evaluation_prompt = f"""You are an expert clinical fact-checker. Your task is to evaluate whether the following *diagnosis or diagnostic reasoning* is medically accurate, grounded in the provided clinical context, and free from hallucinations.

SOURCE FACTS:

VIGNETTE SUMMARY:
{vignette}

PATIENT CONVERSATION:
{conversation}

MODEL-GENERATED DIAGNOSIS:
{completion}

EVALUATION CRITERIA:

❌ HALLUCINATIONS (DO penalize):
- Diagnoses that are not supported by symptoms, demographics, timeline, or context
- Inclusion of test results or findings not present in the vignette or conversation
- Fabricated past medical history or risk factors
- Contradictions to clearly stated patient facts

⚠️ OMISSIONS (DO penalize):
- Failure to include likely or high-risk differential diagnoses based on symptoms
- Ignoring demographic or timeline data that should alter diagnostic reasoning
- Excluding common causes for the presentation
- Not referencing red flags or “must not miss” conditions

✅ CORRECT ITEMS (DO reward):
- Diagnoses clearly grounded in symptoms and presentation
- Logical, step-by-step reasoning that matches the vignette and conversation
- Consideration of multiple possibilities if uncertainty exists
- Recognition of urgent or serious conditions needing attention

DO NOT penalize:
- Reasonable paraphrasing of clinical language
- Use of umbrella terms (e.g., “viral syndrome”) when justified
- Mention of appropriate next steps or tests (if grounded in context)

Respond with ONLY a JSON object:
{{
  "hallucinated_items": ["diagnosis of meningitis with no stiff neck or fever", "claims seizure history with no mention in vignette"],
  "omitted_items": ["missed migraine despite photophobia and throbbing pain", "no mention of GI causes in abdominal pain case"],
  "accurate_items": ["migraine is appropriate for photophobia, nausea, unilateral pain", "consideration of tension headache"],
  "score": 0
}}

SCORING RULES:
- Deduct 3 points per hallucinated diagnosis or fabricated evidence
- Deduct 2 points per critical missed differential or omission
- Add 1 point per well-justified and accurate diagnostic element
- Final score should be clipped between −10 and +10
"""
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": evaluation_prompt}],
            temperature=0.1,
            max_tokens=1000,  # Increased to prevent truncation
        )

        raw_content = response.choices[0].message.content.strip()

        # ROBUST JSON EXTRACTION - MULTIPLE STRATEGIES
        score = 0.0

        # Strategy 1: Try to find complete JSON
        json_matches = re.findall(
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", raw_content, re.DOTALL
        )

        for json_candidate in json_matches:
            try:
                # Clean up the JSON string
                cleaned_json = json_candidate.strip()
                # Fix common issues
                cleaned_json = re.sub(
                    r",\s*}", "}", cleaned_json
                )  # Remove trailing commas
                cleaned_json = re.sub(
                    r",\s*]", "]", cleaned_json
                )  # Remove trailing commas in arrays

                result = json.loads(cleaned_json)
                score = float(result.get("score", 0.0))
                hallucinated = result.get("hallucinated_items", [])
                omitted = result.get("omitted_items", [])
                accurate = result.get("accurate_items", [])

                # CALCULATE EXPECTED SCORE BASED ON YOUR RULES
                expected_score = 0
                expected_score -= 2 * len(hallucinated)  # -2 per hallucination
                print(hallucinated)
                expected_score -= 1 * len(omitted)  # -1 per omission
                print(omitted)
                expected_score += 0.5 * len(accurate)  # +0.5 per accurate
                print(accurate)
                expected_score = max(-10, min(10, expected_score))

                print(
                    f"[debug reward] #{idx} → ChatGPT score: {score}, CALCULATED score: {expected_score}, hallucinated: {len(hallucinated)}, omitted: {len(omitted)}, accurate: {len(accurate)}"
                )

                # USE THE CALCULATED SCORE INSTEAD OF CHATGPT'S SCORE
                score = expected_score
                break  # Success!

            except json.JSONDecodeError:
                continue  # Try next JSON candidate

        else:
            # Strategy 2: Extract just the score if JSON parsing fails
            score_match = re.search(r'"score":\s*(-?\d+(?:\.\d+)?)', raw_content)
            if score_match:
                score = float(score_match.group(1))
                print(f"[debug reward] #{idx} → extracted score only: {score}")
            else:
                print(f"[debug reward] #{idx} → JSON parsing failed, using 0.0")
                score = 0.0

        # Ensure score is in valid range
        return max(-10, min(10, score))

    except Exception as e:
        print(f"[debug reward] #{idx} → API error: {e}")
        score = 0.0


def chatgpt_hallucination_reward(prompts, completions, **kwargs):
    rewards = []
    for idx, (prompt, completion) in enumerate(zip(prompts, completions)):

        # Extract conversation data if it's a clinical summarizer task
        if "clinical summarizer" in prompt.lower():
            # Extract conversation history
            conv_match = re.search(
                r"CONVERSATION HISTORY:\s*(\[.*?\])", prompt, re.DOTALL
            )
            # Extract previous vignette
            vignette_match = re.search(
                r"PREVIOUS VIGNETTE:\s*(.*?)(?:Output:|$)", prompt, re.DOTALL
            )

            if conv_match:
                conversation_history = conv_match.group(1).strip()
                previous_vignette = (
                    vignette_match.group(1).strip() if vignette_match else ""
                )

                score = run_summarizer_hallucination_check(
                    idx, completion, conversation_history
                )

                # Create ChatGPT prompt to evaluate hallucination

        elif "questionning agent" in prompt.lower():
            # Extract conversation history
            differential = re.search(r"1.\s*(\[.*?\])", prompt, re.DOTALL)
            # Extract previous vignette
            vignette = re.search(
                r"Chief Complaint:\s*(.*?)(?:Output:|$)", prompt, re.DOTALL
            )

            if conv_match:
                score = run_questionning_agent_check(
                    idx, differential, vignette, completion
                )

        elif "treatment plan" in prompt.lower():
            # Extract conversation history
            diagnosis = re.search(r"DIAGNOSIS:\s*(\[.*?\])", prompt, re.DOTALL)
            # Extract previous vignette
            vignette_match = re.search(
                r"VIGNETTE:\s*(.*?)(?:Output:|$)", prompt, re.DOTALL
            )

            conversation = re.search(
                r"conversation:\s*(.*?)(?:Output:|$)", prompt, re.DOTALL
            )

            if conv_match:
                score = run_treatment_plan_check(
                    idx, differential, vignette, conversation, completion
                )
        elif "diagnostic reasoning model" in prompt.lower():
            # Extract conversation history
            vignette = re.search(r"Chief Complaint:\s*(\[.*?\])", prompt, re.DOTALL)
            # Extract previous vignette

            conversation = re.search(
                r"conversation:\s*(.*?)(?:Output:|$)", prompt, re.DOTALL
            )

            if conv_match:

                score = run_diagnostic_model_check(
                    idx, completion, conversation, vignette
                )

            else:
                score = 0.0
        else:
            score = 0.0

        rewards.append(score)
    return rewards


# ─── 7. Configure GRPO ───────────────────────────────────────────
training_args = GRPOConfig(
    # Essential parameters
    output_dir="llama-3.1-8b-think-answer-debug",
    num_train_epochs=1,
    max_steps=2450,  # For debugging, use a small number of steps
    per_device_train_batch_size=4,  # We want to get all generations in one device batch
    bf16=True,
    # Optional but useful
    gradient_accumulation_steps=2,
    learning_rate=1e-5,
    logging_steps=10,
    # GRPO specific (optional)
)

# ─── 8. Instantiate & train ───────────────────────────────────────
trainer = GRPOTrainer(
    model=hf_model,
    args=training_args,
    train_dataset=tokenized,
    reward_funcs=chatgpt_hallucination_reward,
)
print("[debug] Starting trainer.train()…")


if __name__ == "__main__":
    trainer.train()
