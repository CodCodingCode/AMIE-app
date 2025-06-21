import json
import os
from openai import OpenAI
from collections import defaultdict

# Initialize OpenAI client
client = OpenAI(
    api_key="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"
)


class ImprovementTracker:
    def __init__(self):
        self.improvements = {
            "patient": [],
            "summarizer": [],
            "diagnoser": [],
            "questioner": [],
            "treatment": [],
        }

    def add_improvement(self, component, improvement_dict):
        """Add improvement if it's not a duplicate"""
        existing_improvements = self.improvements[component]

        # Simple duplicate check based on problem description
        for existing in existing_improvements:
            if (
                existing.get("problem", "").lower()
                in improvement_dict.get("problem", "").lower()
                or improvement_dict.get("problem", "").lower()
                in existing.get("problem", "").lower()
            ):
                return False  # It's a duplicate

        self.improvements[component].append(improvement_dict)
        return True

    def get_all_improvements(self):
        return self.improvements

    def get_improvement_count(self, component):
        return len(self.improvements[component])


# Global improvement tracker
improvement_tracker = ImprovementTracker()

# Define the function schema for OpenAI function calling
improvement_function = {
    "name": "report_improvements",
    "description": "Report improvements needed for clinical training data",
    "parameters": {
        "type": "object",
        "properties": {
            "improvements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "problem": {
                            "type": "string",
                            "description": "Description of the issue",
                        },
                        "evidence": {
                            "type": "string",
                            "description": "Quote of problematic text",
                        },
                        "code_fix": {
                            "type": "string",
                            "description": "Specific solution needed",
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["Critical", "High", "Medium", "Low"],
                        },
                        "component": {
                            "type": "string",
                            "description": "Which component needs fixing",
                        },
                    },
                    "required": [
                        "problem",
                        "evidence",
                        "code_fix",
                        "priority",
                        "component",
                    ],
                },
            }
        },
        "required": ["improvements"],
    },
}


def analyze_patient_followups(data):
    """Analyze patient followup responses for quality and realism"""

    sample_entries = data[:10] if len(data) > 10 else data  # Increased sample size
    simplified_data = []
    for entry in sample_entries:
        simplified_data.append(
            {
                "vignette_index": entry.get("vignette_index"),
                "answer": entry.get("answer", ""),
                "thinking_snippet": (entry.get("thinking", "")),
                "gold_diagnosis": entry.get("gold_diagnosis", ""),
                "turn_count": entry.get("turn_count", 0),
            }
        )

    analysis_prompt = f"""You are an EXTREMELY STRICT clinical training data quality analyst. Your job is to ruthlessly identify EVERY flaw in patient simulation outputs.

PATIENT SIMULATION DATA:
{json.dumps(simplified_data, indent=2)}

STRICT EVALUATION CRITERIA:
Apply these standards with ZERO tolerance:

1. LANGUAGE AUTHENTICITY:
- Flag ANY medical terminology that a layperson wouldn't use
- Flag ANY overly articulate or clinical descriptions
- Flag ANY responses that sound like they're from a medical textbook
- Flag ANY age-inappropriate language or sophistication level

2. RESPONSE REALISM:
- Flag ANY responses that are too detailed for a typical patient
- Flag ANY responses that show medical knowledge patients shouldn't have
- Flag ANY responses that are too coherent or well-organized
- Flag ANY responses that don't reflect appropriate confusion or uncertainty

3. DEMOGRAPHIC CONSISTENCY:
- Flag ANY language that doesn't match the patient's stated age/background
- Flag ANY responses that ignore cultural, educational, or generational factors
- Flag ANY responses that don't reflect realistic health literacy levels

4. SYMPTOM CONSISTENCY:
- Flag ANY contradictions in symptom descriptions across responses
- Flag ANY symptom descriptions that are medically implausible
- Flag ANY responses that add symptoms not mentioned in the source material

5. EMOTIONAL AUTHENTICITY:
- Flag ANY responses that don't reflect appropriate anxiety, fear, or confusion
- Flag ANY responses that are too calm or matter-of-fact for serious symptoms
- Flag ANY responses that don't show realistic patient psychology

INSTRUCTIONS:
- Examine EVERY response for violations of these criteria
- Be RUTHLESS - if something seems even slightly off, flag it
- Look for subtle issues like slightly too-clinical word choices
- Consider how a REAL patient with these exact characteristics would actually speak
- Find flaws that would make this data unsuitable for training realistic patient models

For EVERY issue found, provide specific evidence and actionable fixes."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": "You are an EXTREMELY STRICT clinical training data quality analyst. Find EVERY flaw, no matter how minor. Be ruthless in your evaluation.",
                },
                {"role": "user", "content": analysis_prompt},
            ],
            functions=[improvement_function],
            function_call={"name": "report_improvements"},
            max_tokens=3000,
            temperature=0.0,
        )

        # Extract function call result
        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "report_improvements":
            analysis_data = json.loads(function_call.arguments)
            added_count = 0
            for improvement in analysis_data.get("improvements", []):
                improvement["component"] = "patient"  # Ensure correct component
                if improvement_tracker.add_improvement("patient", improvement):
                    added_count += 1
            print(f"   Added {added_count} unique patient improvements")
            return analysis_data
        else:
            print("   ⚠️ No function call returned")
            return {"improvements": []}

    except Exception as e:
        print(f"   ❌ Error in patient analysis: {e}")
        return {"improvements": []}


def analyze_summarizer_outputs(data):
    """Analyze clinical summarizer outputs for accuracy and completeness"""

    sample_entries = data[:10] if len(data) > 10 else data
    simplified_data = []
    for entry in sample_entries:
        simplified_data.append(
            {
                "vignette_index": entry.get("vignette_index"),
                "turn_count": entry.get("turn_count"),
                "answer": entry.get("answer", ""),
                "thinking_snippet": (entry.get("thinking", "")),
                "gold_diagnosis": entry.get("gold_diagnosis", ""),
                "input_snippet": (str(entry.get("input", ""))),
            }
        )

    analysis_prompt = f"""You are an EXTREMELY STRICT clinical documentation quality analyst. Your job is to ruthlessly identify EVERY flaw in clinical summarization outputs.

CLINICAL SUMMARIZER DATA:
{json.dumps(simplified_data, indent=2)}

STRICT EVALUATION CRITERIA:
Apply these standards with ZERO tolerance:

1. FACTUAL PRECISION:
- Flag ANY information that wasn't explicitly stated in the source conversation
- Flag ANY inferences, assumptions, or interpretations added by the summarizer
- Flag ANY paraphrasing that changes the meaning or adds implications
- Flag ANY medical interpretations not directly stated by the patient

2. COMPLETENESS VALIDATION:
- Flag ANY patient statements that are missing from the summary
- Flag ANY symptom descriptions that are incomplete or abbreviated
- Flag ANY timeline information that is omitted or unclear
- Flag ANY demographic or contextual information that's missing

3. TERMINOLOGY ACCURACY:
- Flag ANY medical terms used when the patient used lay language
- Flag ANY lay terms converted incorrectly to medical terminology
- Flag ANY terminology that adds clinical significance not stated by patient
- Flag ANY diagnostic language that implies conclusions not drawn

4. ORGANIZATIONAL INTEGRITY:
- Flag ANY information that's placed in wrong sections
- Flag ANY missing standard sections that should be included
- Flag ANY poor chronological organization of events
- Flag ANY unclear or confusing presentation of information

5. OBJECTIVITY MAINTENANCE:
- Flag ANY subjective assessments or clinical judgments
- Flag ANY interpretive language that goes beyond patient statements
- Flag ANY diagnostic reasoning that belongs in clinical assessment, not summary
- Flag ANY speculation about patient condition or prognosis

INSTRUCTIONS:
- Examine EVERY summary for violations of these criteria
- Be RUTHLESS - if information is added, missing, or incorrectly interpreted, flag it
- Look for subtle bias or interpretation in word choices
- Consider whether the summary would mislead clinicians about what the patient actually said
- Find flaws that would make this data unsuitable for training accurate clinical summarizers

For EVERY issue found, provide specific evidence and actionable fixes."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": "You are an EXTREMELY STRICT clinical documentation quality analyst. Find EVERY flaw in clinical summarization, no matter how minor. Be ruthless.",
                },
                {"role": "user", "content": analysis_prompt},
            ],
            functions=[improvement_function],
            function_call={"name": "report_improvements"},
            max_tokens=3000,
            temperature=0.0,
        )

        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "report_improvements":
            analysis_data = json.loads(function_call.arguments)
            added_count = 0
            for improvement in analysis_data.get("improvements", []):
                improvement["component"] = "summarizer"
                if improvement_tracker.add_improvement("summarizer", improvement):
                    added_count += 1
            print(f"   Added {added_count} unique summarizer improvements")
            return analysis_data
        else:
            print("   ⚠️ No function call returned")
            return {"improvements": []}

    except Exception as e:
        print(f"   ❌ Error in summarizer analysis: {e}")
        return {"improvements": []}


def analyze_diagnosing_outputs(data):
    """Analyze diagnostic reasoning outputs for clinical accuracy"""

    sample_entries = []
    for stage in ["E", "M", "L"]:
        stage_entries = [d for d in data if d.get("letter") == stage]
        if stage_entries:
            sample_entries.extend(stage_entries[:4])  # Increased sample

    if not sample_entries:
        sample_entries = data[:12] if len(data) > 12 else data

    simplified_data = []
    for entry in sample_entries:
        simplified_data.append(
            {
                "vignette_index": entry.get("vignette_index"),
                "stage": entry.get("letter", "Unknown"),
                "answer": entry.get("answer", ""),
                "thinking_snippet": (entry.get("thinking", "")),
                "gold_diagnosis": entry.get("gold_diagnosis", ""),
                "turn_count": entry.get("turn_count", 0),
                "input_snippet": (str(entry.get("input", ""))),
            }
        )

    analysis_prompt = f"""You are an EXTREMELY STRICT clinical diagnostic quality analyst. Your job is to ruthlessly identify EVERY flaw in diagnostic reasoning outputs.

DIAGNOSTIC REASONING DATA:
{json.dumps(simplified_data, indent=2)}

STRICT EVALUATION CRITERIA:
Apply these standards with ZERO tolerance:

1. CLINICAL REASONING RIGOR:
- Flag ANY diagnostic reasoning that lacks proper clinical logic
- Flag ANY conclusions not supported by the presented evidence
- Flag ANY reasoning that ignores key clinical features
- Flag ANY diagnostic approaches that don't follow systematic methodology

2. DIFFERENTIAL DIAGNOSIS QUALITY:
- Flag ANY diagnoses that are clinically inappropriate for the presentation
- Flag ANY missing diagnoses that should be considered for this clinical picture
- Flag ANY diagnoses ranked incorrectly based on probability
- Flag ANY "can't miss" life-threatening diagnoses that are omitted

3. EVIDENCE UTILIZATION:
- Flag ANY failure to incorporate key clinical evidence
- Flag ANY misinterpretation of patient symptoms or signs
- Flag ANY reasoning that contradicts the available clinical data
- Flag ANY evidence that's overlooked or dismissed inappropriately

4. STAGE-APPROPRIATE COMPLEXITY:
- Flag ANY reasoning that's too simple for the diagnostic stage
- Flag ANY reasoning that's inappropriately complex for early stages
- Flag ANY failure to build on previous diagnostic iterations
- Flag ANY stage-inappropriate diagnostic strategies

5. GOLD STANDARD ALIGNMENT:
- Flag ANY cases where the gold diagnosis isn't properly considered
- Flag ANY rankings that don't appropriately weight the correct diagnosis
- Flag ANY reasoning that would lead away from the correct diagnosis
- Flag ANY failure to recognize key features supporting the gold diagnosis

6. SYSTEMATIC COMPLETENESS:
- Flag ANY incomplete systematic review of possibilities
- Flag ANY failure to consider patient demographics in differential
- Flag ANY missing consideration of urgency or acuity
- Flag ANY inadequate risk stratification

INSTRUCTIONS:
- Examine EVERY diagnostic output for violations of these criteria
- Be RUTHLESS - if reasoning is flawed, incomplete, or misleading, flag it
- Look for subtle errors in clinical logic or probability assessment
- Consider whether this reasoning would lead to correct clinical decisions
- Find flaws that would make this data unsuitable for training competent diagnostic models

For EVERY issue found, provide specific evidence and actionable fixes."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": "You are an EXTREMELY STRICT clinical diagnostic quality analyst. Find EVERY flaw in diagnostic reasoning, no matter how minor. Lives depend on diagnostic accuracy - be ruthless.",
                },
                {"role": "user", "content": analysis_prompt},
            ],
            functions=[improvement_function],
            function_call={"name": "report_improvements"},
            max_tokens=4000,
            temperature=0.0,
        )

        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "report_improvements":
            analysis_data = json.loads(function_call.arguments)
            added_count = 0
            for improvement in analysis_data.get("improvements", []):
                improvement["component"] = "diagnoser"
                if improvement_tracker.add_improvement("diagnoser", improvement):
                    added_count += 1
            print(f"   Added {added_count} unique diagnoser improvements")
            return analysis_data
        else:
            print("   ⚠️ No function call returned")
            return {"improvements": []}

    except Exception as e:
        print(f"   ❌ Error in diagnoser analysis: {e}")
        return {"improvements": []}


def analyze_questioning_outputs(data):
    """Analyze clinical questioning outputs for diagnostic effectiveness"""

    sample_entries = data[:15] if len(data) > 15 else data  # Increased sample
    simplified_data = []
    for entry in sample_entries:
        simplified_data.append(
            {
                "vignette_index": entry.get("vignette_index"),
                "stage": entry.get("letter", "Unknown"),
                "answer": entry.get("answer", ""),
                "thinking_snippet": entry.get("thinking", ""),
                "gold_diagnosis": entry.get("gold_diagnosis", ""),
                "input_snippet": str(entry.get("input", "")),
            }
        )

    analysis_prompt = f"""You are an EXTREMELY STRICT clinical interviewing quality analyst. Your job is to ruthlessly identify EVERY flaw in clinical questioning outputs.

CLINICAL QUESTIONING DATA:
{json.dumps(simplified_data, indent=2)}

STRICT EVALUATION CRITERIA:
Apply these standards with ZERO tolerance:

1. DIAGNOSTIC VALUE ASSESSMENT:
- Flag ANY questions that don't advance diagnostic understanding
- Flag ANY questions that gather irrelevant or low-yield information
- Flag ANY questions that fail to distinguish between competing diagnoses
- Flag ANY questions that don't target the most important diagnostic gaps

2. QUESTIONING TECHNIQUE RIGOR:
- Flag ANY leading questions that bias patient responses
- Flag ANY compound questions that confuse or overwhelm patients
- Flag ANY questions that are poorly worded or ambiguous
- Flag ANY questions that assume facts not in evidence

3. STAGE-APPROPRIATE STRATEGY:
- Flag ANY questions that are too broad for late-stage interviewing
- Flag ANY questions that are too narrow for early-stage exploration
- Flag ANY questions that don't build logically on previous information
- Flag ANY questions that don't match the diagnostic stage objectives

4. EFFICIENCY AND REDUNDANCY:
- Flag ANY questions that repeat previously asked information
- Flag ANY questions that could be combined for better efficiency
- Flag ANY questions that explore tangential rather than core issues
- Flag ANY questions that waste limited interview time

5. CLINICAL REASONING QUALITY:
- Flag ANY questions not justified by sound clinical reasoning
- Flag ANY questions that ignore the differential diagnosis priorities
- Flag ANY questions that don't consider the gold diagnosis appropriately
- Flag ANY questions that show poor understanding of the clinical context

6. PATIENT-CENTERED APPROACH:
- Flag ANY questions that are insensitive to patient demographics
- Flag ANY questions that ignore patient's stated concerns
- Flag ANY questions that use inappropriate medical terminology
- Flag ANY questions that don't consider patient's emotional state

INSTRUCTIONS:
- Examine EVERY question for violations of these criteria
- Be RUTHLESS - if a question is suboptimal, inefficient, or inappropriate, flag it
- Look for subtle issues like slightly poor wording or missed opportunities
- Consider whether each question represents the BEST possible choice at that moment
- Find flaws that would make this data unsuitable for training effective clinical interviewers

For EVERY issue found, provide specific evidence and actionable fixes."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": "You are an EXTREMELY STRICT clinical interviewing quality analyst. Find EVERY flaw in questioning strategy, no matter how minor. Effective questioning is critical for diagnosis - be ruthless.",
                },
                {"role": "user", "content": analysis_prompt},
            ],
            functions=[improvement_function],
            function_call={"name": "report_improvements"},
            max_tokens=3000,
            temperature=0.0,
        )

        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "report_improvements":
            analysis_data = json.loads(function_call.arguments)
            added_count = 0
            for improvement in analysis_data.get("improvements", []):
                improvement["component"] = "questioner"
                if improvement_tracker.add_improvement("questioner", improvement):
                    added_count += 1
            print(f"   Added {added_count} unique questioner improvements")
            return analysis_data
        else:
            print("   ⚠️ No function call returned")
            return {"improvements": []}

    except Exception as e:
        print(f"   ❌ Error in questioner analysis: {e}")
        return {"improvements": []}


def analyze_treatment_plans(data):
    """Analyze treatment planning outputs for clinical appropriateness"""

    sample_entries = data[:8] if len(data) > 8 else data  # Increased sample
    simplified_data = []
    for entry in sample_entries:
        simplified_data.append(
            {
                "vignette_index": entry.get("vignette_index"),
                "turn_count": entry.get("turn_count"),
                "answer": entry.get("answer", ""),
                "thinking_snippet": entry.get("thinking", ""),
                "gold_diagnosis": entry.get("gold_diagnosis", ""),
                "input_snippet": str(entry.get("input", "")),
            }
        )

    analysis_prompt = f"""You are an EXTREMELY STRICT clinical treatment planning quality analyst. Your job is to ruthlessly identify EVERY flaw in treatment planning outputs.

TREATMENT PLANNING DATA:
{json.dumps(simplified_data, indent=2)}

STRICT EVALUATION CRITERIA:
Apply these standards with ZERO tolerance:

1. EVIDENCE-BASED APPROPRIATENESS:
- Flag ANY treatments that aren't first-line evidence-based for the condition
- Flag ANY treatments that contradict established clinical guidelines
- Flag ANY treatments that are inappropriate for patient demographics
- Flag ANY treatments that ignore contraindications or precautions

2. CLINICAL SAFETY RIGOR:
- Flag ANY missing safety monitoring requirements
- Flag ANY missing contraindication assessments
- Flag ANY missing drug interaction considerations
- Flag ANY missing allergy or adverse reaction precautions

3. COMPREHENSIVE CARE COMPLETENESS:
- Flag ANY missing immediate/acute management steps
- Flag ANY missing short-term management components
- Flag ANY missing long-term care considerations
- Flag ANY missing preventive or maintenance elements

4. SPECIFICITY AND ACTIONABILITY:
- Flag ANY vague or non-specific recommendations
- Flag ANY recommendations without clear dosing, timing, or parameters
- Flag ANY recommendations that can't be practically implemented
- Flag ANY recommendations without clear success metrics

5. PATIENT-SPECIFIC TAILORING:
- Flag ANY generic plans that ignore individual patient factors
- Flag ANY plans that don't consider patient age, comorbidities, or context
- Flag ANY plans that ignore socioeconomic or practical barriers
- Flag ANY plans that don't address patient-specific risk factors

6. MULTIDISCIPLINARY COORDINATION:
- Flag ANY missing specialist referral needs
- Flag ANY missing care team coordination requirements
- Flag ANY missing follow-up or monitoring schedules
- Flag ANY missing patient education or communication needs

7. GOLD DIAGNOSIS ALIGNMENT:
- Flag ANY treatments inappropriate for the gold diagnosis
- Flag ANY treatments that don't address the specific pathophysiology
- Flag ANY treatments that ignore condition-specific considerations
- Flag ANY treatments that would be suboptimal for the actual diagnosis

INSTRUCTIONS:
- Examine EVERY treatment plan for violations of these criteria
- Be RUTHLESS - if any aspect of care is suboptimal, incomplete, or unsafe, flag it
- Look for subtle omissions in monitoring, follow-up, or safety considerations
- Consider whether this plan would provide optimal patient outcomes
- Find flaws that would make this data unsuitable for training safe, effective treatment planners

For EVERY issue found, provide specific evidence and actionable fixes."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": "You are an EXTREMELY STRICT clinical treatment planning quality analyst. Find EVERY flaw in treatment planning, no matter how minor. Patient safety depends on treatment quality - be ruthless.",
                },
                {"role": "user", "content": analysis_prompt},
            ],
            functions=[improvement_function],
            function_call={"name": "report_improvements"},
            max_tokens=3000,
            temperature=0.0,
        )

        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "report_improvements":
            analysis_data = json.loads(function_call.arguments)
            added_count = 0
            for improvement in analysis_data.get("improvements", []):
                improvement["component"] = "treatment"
                if improvement_tracker.add_improvement("treatment", improvement):
                    added_count += 1
            print(f"   Added {added_count} unique treatment improvements")
            return analysis_data
        else:
            print("   ⚠️ No function call returned")
            return {"improvements": []}

    except Exception as e:
        print(f"   ❌ Error in treatment analysis: {e}")
        return {"improvements": []}


def generate_comprehensive_report():
    """Generate comprehensive improvement report organized by component"""

    all_improvements = improvement_tracker.get_all_improvements()

    total_improvements = sum(
        len(improvements) for improvements in all_improvements.values()
    )

    report_content = []
    report_content.append("COMPREHENSIVE OUTPUT QUALITY ANALYSIS AND IMPROVEMENT PLAN")
    report_content.append("=" * 70)
    report_content.append(f"Total Unique Improvements Identified: {total_improvements}")
    report_content.append("")

    # Component-by-component breakdown
    for component, improvements in all_improvements.items():
        if improvements:
            report_content.append(
                f"{component.upper()} COMPONENT - {len(improvements)} Unique Improvements:"
            )
            report_content.append("-" * 50)

            # Sort by priority
            priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
            sorted_improvements = sorted(
                improvements,
                key=lambda x: priority_order.get(x.get("priority", "Low"), 3),
            )

            for i, improvement in enumerate(sorted_improvements, 1):
                report_content.append(
                    f"{i}. [{improvement.get('priority', 'Unknown')}] {improvement.get('problem', 'No problem description')}"
                )
                report_content.append(
                    f"   Evidence: {improvement.get('evidence', 'No evidence provided')}"
                )
                report_content.append(
                    f"   Fix: {improvement.get('code_fix', 'No fix provided')}"
                )
                report_content.append("")
        else:
            report_content.append(
                f"{component.upper()} COMPONENT - No improvements needed"
            )
            report_content.append("")

    return "\n".join(report_content)


def analyze_all_outputs():
    """Main function to analyze all output files and generate improvement recommendations"""

    print("🔍 Starting comprehensive output quality analysis with function calling...")

    analyses = {}

    # Load and analyze each file type
    files_to_analyze = [
        ("2patient_followups.json", "Patient Followups", analyze_patient_followups),
        ("2summarizer_outputs.json", "Summarizer Outputs", analyze_summarizer_outputs),
        (
            "2diagnosing_doctor_outputs.json",
            "Diagnostic Outputs",
            analyze_diagnosing_outputs,
        ),
        (
            "2questioning_doctor_outputs.json",
            "Questioning Outputs",
            analyze_questioning_outputs,
        ),
        ("2treatment_plans.json", "Treatment Plans", analyze_treatment_plans),
    ]

    for filename, description, analyze_func in files_to_analyze:
        if os.path.exists(filename):
            print(f"\n📊 Analyzing {description}...")

            try:
                with open(filename, "r") as f:
                    data = json.load(f)

                if data:
                    analysis = analyze_func(data)
                    analyses[description] = analysis
                    print(f"✅ {description} analysis complete")
                else:
                    print(f"⚠️ {description} file is empty")

            except Exception as e:
                print(f"❌ Error analyzing {description}: {e}")
        else:
            print(f"⚠️ {filename} not found")

    # Generate comprehensive report
    print("\n📝 Generating comprehensive improvement report...")

    report_content = generate_comprehensive_report()

    # Save comprehensive report
    with open("new_data_gen/actual_data_gen/output_quality_analysis.txt", "w") as f:
        f.write(report_content)

    # Save structured improvements as JSON for programmatic access
    with open("new_data_gen/actual_data_gen/structured_improvements.json", "w") as f:
        json.dump(improvement_tracker.get_all_improvements(), f, indent=2)

    # Print summary
    print("\n✅ Analysis complete!")
    print(f"📈 Improvement Summary:")
    all_improvements = improvement_tracker.get_all_improvements()
    print(f"\n🔍 DEBUG - Report generation data:")
    for component, improvements in all_improvements.items():
        print(f"   {component}: {len(improvements)} improvements")
        count = len(improvements)
        if count > 0:
            critical_count = len(
                [i for i in improvements if i.get("priority") == "Critical"]
            )
            print(
                f"   {component.capitalize()}: {count} improvements ({critical_count} critical)"
            )
        else:
            print(f"   {component.capitalize()}: No improvements needed")

    print(f"\n📄 Reports saved:")
    print(f"   - output_quality_analysis.txt (human-readable)")
    print(f"   - structured_improvements.json (programmatic access)")


if __name__ == "__main__":
    # DEBUG: Print raw tracker data before summary
    print(f"\n🔍 DEBUG - Console summary data:")
    raw_data = improvement_tracker.get_all_improvements()
    for component, improvements in raw_data.items():
        print(f"   {component}: {len(improvements)} raw improvements")

    all_improvements = improvement_tracker.get_all_improvements()
    analyze_all_outputs()
