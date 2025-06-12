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

    sample_entries = data
    simplified_data = []
    for entry in sample_entries:
        simplified_data.append(
            {
                "vignette_index": entry.get("vignette_index"),
                "answer": entry.get("answer", ""),
                "thinking_snippet": (entry.get("thinking", "") + "..."),
                "gold_diagnosis": entry.get("gold_diagnosis", ""),
            }
        )

    analysis_prompt = f"""Analyze these patient simulation outputs for quality issues:

DATA: {json.dumps(simplified_data, indent=2)}

Find problems with:
1. Medical jargon in patient speech (patients shouldn't use clinical terms)
2. Unrealistic responses for the patient's age/background
3. Overly detailed or textbook-like answers
4. Inconsistent symptom descriptions

For each issue found, identify the problem, quote evidence, suggest a code fix, set priority, and mark component as "patient"."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical training data quality analyst. Use the function to report all improvements needed.",
                },
                {"role": "user", "content": analysis_prompt},
            ],
            functions=[improvement_function],
            function_call={"name": "report_improvements"},
            max_tokens=2000,
            temperature=0.1,
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

    sample_entries = data[:3] if len(data) > 3 else data
    simplified_data = []
    for entry in sample_entries:
        simplified_data.append(
            {
                "vignette_index": entry.get("vignette_index"),
                "turn_count": entry.get("turn_count"),
                "answer": entry.get("answer", ""),
                "thinking_snippet": (
                    entry.get("thinking", "")[:300] + "..."
                    if len(entry.get("thinking", "")) > 300
                    else entry.get("thinking", "")
                ),
                "gold_diagnosis": entry.get("gold_diagnosis", ""),
            }
        )

    analysis_prompt = f"""Analyze these clinical summarizer outputs for quality issues:

DATA: {json.dumps(simplified_data, indent=2)}

Find problems with:
1. Added information not stated by patient
2. Missing key patient statements  
3. Incorrect medical terminology translations
4. Poor organization or missing sections
5. Subjective interpretations instead of objective facts

For each issue found, identify the problem, quote evidence, suggest a code fix, set priority, and mark component as "summarizer"."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical documentation quality analyst. Use the function to report all improvements needed.",
                },
                {"role": "user", "content": analysis_prompt},
            ],
            functions=[improvement_function],
            function_call={"name": "report_improvements"},
            max_tokens=2000,
            temperature=0.1,
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
            sample_entries.extend(stage_entries[:2])

    if not sample_entries:
        sample_entries = data[:3]

    simplified_data = []
    for entry in sample_entries:
        simplified_data.append(
            {
                "vignette_index": entry.get("vignette_index"),
                "stage": entry.get("letter", "Unknown"),
                "answer": entry.get("answer", ""),
                "thinking_snippet": (
                    entry.get("thinking", "")[:400] + "..."
                    if len(entry.get("thinking", "")) > 400
                    else entry.get("thinking", "")
                ),
                "gold_diagnosis": entry.get("gold_diagnosis", ""),
            }
        )

    analysis_prompt = f"""Analyze these diagnostic reasoning outputs for quality issues:

DATA: {json.dumps(simplified_data, indent=2)}

Find problems with:
1. Poor clinical reasoning or flawed logic
2. Inappropriate differential diagnoses
3. Missing critical "can't miss" diagnoses
4. Stage-inappropriate reasoning complexity
5. Gold diagnosis not properly considered
6. Weak evidence utilization

For each issue found, identify the problem, quote evidence, suggest a code fix, set priority, and mark component as "diagnoser"."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical diagnostic quality analyst. Use the function to report all improvements needed.",
                },
                {"role": "user", "content": analysis_prompt},
            ],
            functions=[improvement_function],
            function_call={"name": "report_improvements"},
            max_tokens=2500,
            temperature=0.1,
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

    sample_entries = data[:6] if len(data) > 6 else data
    simplified_data = []
    for entry in sample_entries:
        simplified_data.append(
            {
                "vignette_index": entry.get("vignette_index"),
                "stage": entry.get("letter", "Unknown"),
                "answer": entry.get("answer", ""),
                "thinking_snippet": (
                    entry.get("thinking", "")[:300] + "..."
                    if len(entry.get("thinking", "")) > 300
                    else entry.get("thinking", "")
                ),
                "gold_diagnosis": entry.get("gold_diagnosis", ""),
            }
        )

    analysis_prompt = f"""Analyze these clinical questioning outputs for quality issues:

DATA: {json.dumps(simplified_data, indent=2)}

Find problems with:
1. Low diagnostic value questions
2. Stage-inappropriate questioning strategies  
3. Leading or poorly formulated questions
4. Weak reasoning behind question selection
5. Redundant or inefficient questioning
6. Questions that don't help narrow toward gold diagnosis

For each issue found, identify the problem, quote evidence, suggest a code fix, set priority, and mark component as "questioner"."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical interviewing quality analyst. Use the function to report all improvements needed.",
                },
                {"role": "user", "content": analysis_prompt},
            ],
            functions=[improvement_function],
            function_call={"name": "report_improvements"},
            max_tokens=2000,
            temperature=0.1,
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

    sample_entries = data[:3] if len(data) > 3 else data
    simplified_data = []
    for entry in sample_entries:
        simplified_data.append(
            {
                "vignette_index": entry.get("vignette_index"),
                "turn_count": entry.get("turn_count"),
                "answer": entry.get("answer", ""),
                "thinking_snippet": (
                    entry.get("thinking", "")[:400] + "..."
                    if len(entry.get("thinking", "")) > 400
                    else entry.get("thinking", "")
                ),
                "gold_diagnosis": entry.get("gold_diagnosis", ""),
            }
        )

    analysis_prompt = f"""Analyze these treatment planning outputs for quality issues:

DATA: {json.dumps(simplified_data, indent=2)}

Find problems with:
1. Inappropriate or non-evidence-based treatments
2. Missing aspects of care (immediate/short-term/long-term)
3. Vague or non-actionable recommendations
4. Missing safety considerations or monitoring
5. Generic plans not tailored to patient context
6. Treatments inappropriate for gold diagnosis

For each issue found, identify the problem, quote evidence, suggest a code fix, set priority, and mark component as "treatment"."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical treatment quality analyst. Use the function to report all improvements needed.",
                },
                {"role": "user", "content": analysis_prompt},
            ],
            functions=[improvement_function],
            function_call={"name": "report_improvements"},
            max_tokens=2000,
            temperature=0.1,
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
    for component, improvements in improvement_tracker.get_all_improvements().items():
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
    analyze_all_outputs()
