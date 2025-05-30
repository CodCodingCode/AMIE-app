import os
import re
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from typing import List

# ─── OpenAI client ───────────────────────────────────────────────
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ─── Your fixed reference for formatting (must be length 10) ─────
reference_diseases = [
    "Asthma",
    "COPD",
    "Pneumonia",
    "Bronchitis",
    "Tuberculosis",
    "Emphysema",
    "Cystic fibrosis",
    "Lung cancer",
    "Pulmonary edema",
    "Sarcoidosis",
]


# ─── Pydantic models ─────────────────────────────────────────────
class DiseaseCheck(BaseModel):
    count: int
    diseases: List[str]
    reasoning: str


def parse_disease_check(resp_text: str) -> DiseaseCheck:
    try:
        return DiseaseCheck.parse_raw(resp_text)
    except ValidationError:
        return DiseaseCheck(count=0, diseases=[], reasoning="invalid response")


class ReferenceList(BaseModel):
    diseases: List[str]


# ─── Prompt for ChatGPT to produce its own 10 diagnoses ───────────
DIAGNOSIS_LIST_PROMPT = """
You are a board-certified clinician.
Given the patient vignette below, list the 10 most likely diagnoses.
Return ONLY a JSON object with key "diseases" mapping to an array of 10 diagnosis strings.

Patient vignette:
{vignette}
"""


# ─── Combined 50/50 reward function ──────────────────────────────
def combined_openai_reward_fn(
    prompts: List[str], generations: List[str]
) -> List[List[float]]:
    all_rewards: List[List[float]] = []
    expected_count = len(reference_diseases)
    ref_lower = [d.lower() for d in reference_diseases]

    for vignette, gen_json in zip(prompts, generations):
        # ── 1) Formatting check ──────────────────────────────────
        dc = parse_disease_check(gen_json)
        gen_lower = [d.strip().lower() for d in dc.diseases]

        # penalty if not exactly 10
        factor = max(0.0, min(1.0, dc.count / expected_count))

        # exact‐match per index
        fmt_pairs = list(zip(ref_lower, gen_lower))
        f_rewards = [1.0 if ref == gen else 0.0 for ref, gen in fmt_pairs]
        if len(f_rewards) < expected_count:
            f_rewards += [0.0] * (expected_count - len(f_rewards))
        else:
            f_rewards = f_rewards[:expected_count]
        # apply count penalty
        f_rewards = [r * factor for r in f_rewards]

        # ── 2) Diagnostic accuracy check ────────────────────────
        chat_resp = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a board-certified clinician."},
                {
                    "role": "user",
                    "content": DIAGNOSIS_LIST_PROMPT.format(vignette=vignette),
                },
            ],
            temperature=0.0,
            max_tokens=200,
        )
        try:
            ref_list = ReferenceList.parse_raw(chat_resp.choices[0].message.content)
            ref_sample_lower = [d.strip().lower() for d in ref_list.diseases]
        except ValidationError:
            ref_sample_lower = []

        # compare ChatGPT’s list to the model’s
        diag_pairs = list(zip(ref_sample_lower, gen_lower))
        d_rewards = [1.0 if ref == gen else 0.0 for ref, gen in diag_pairs]
        if len(d_rewards) < expected_count:
            d_rewards += [0.0] * (expected_count - len(d_rewards))
        else:
            d_rewards = d_rewards[:expected_count]

        # ── 3) Combine 50/50 ───────────────────────────────────
        combined = [0.5 * f + 0.5 * d for f, d in zip(f_rewards, d_rewards)]
        all_rewards.append(combined)

    return all_rewards
