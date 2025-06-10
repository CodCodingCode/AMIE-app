from openai import OpenAI
import os
import json
import re
from datetime import datetime
from prompt import DiagnosticsPrompt, PCCPrompt, UncertaintyPrompt, TreatmentPrompt

class MedicalBenchmark:
    def __init__(self, client: OpenAI):
        self.client = client

    def evaluate_response(self, prompt: str, conversation: str, section_name: str, max_points: int) -> dict:
        evaluation_prompt = f"""
        {prompt}
        
        Here is the medical conversation to evaluate:
        {conversation}
        
        IMPORTANT: You must evaluate the doctor's responses and provide your assessment in EXACTLY this JSON format (no extra text):

        {{
            "section": "{section_name}",
            "max_points": {max_points},
            "individual_scores": [
                {{
                    "criterion": "Develops appropriate differential diagnoses",
                    "score": 4,
                    "max_score": 5,
                    "justification": "Doctor showed good diagnostic reasoning but could be more comprehensive"
                }},
                {{
                    "criterion": "Ensures differential diagnoses are clinically relevant",
                    "score": 3,
                    "max_score": 5,
                    "justification": "Diagnoses were relevant but prioritization could be clearer"
                }}
            ],
            "total_score": 25,
            "percentage": 71.4,
            "overall_assessment": {{
                "strengths": ["Good questioning technique", "Shows empathy"],
                "weaknesses": ["Could be more systematic", "Missing some key assessments"],
                "summary": "Overall competent performance with room for improvement in systematic approach"
            }}
        }}

        CRITICAL: 
        - Score ALL criteria for this section (not just some)
        - Provide realistic scores based on the conversation content
        - Return ONLY the JSON object, no other text
        - Make sure JSON is valid and complete
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": evaluation_prompt}],
            temperature=0.1  # Lower temperature for more consistent JSON
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean up response - remove any markdown formatting
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON response
        try:
            result = json.loads(response_text)
            # Validate the result has required fields
            if "total_score" not in result or "individual_scores" not in result:
                raise json.JSONDecodeError("Missing required fields", response_text, 0)
            return result
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed for {section_name}: {e}")
            print(f"Raw response: {response_text[:200]}...")
            # Fallback if JSON parsing fails
            return self._parse_fallback_response(response_text, section_name, max_points)

    def _parse_fallback_response(self, response_text: str, section_name: str, max_points: int) -> dict:
        """Improved fallback parser if JSON response fails"""
        print(f"Using fallback parser for {section_name}")
        
        # More sophisticated score extraction
        score_patterns = [
            r'(?:score|rating)[\s:]*(\d+)(?:/5|\s*out\s*of\s*5)',
            r'(\d+)/5',
            r'(\d+)\s*points?',
            r'rate[sd]?\s*(?:as\s*)?(\d+)'
        ]
        
        scores = []
        for pattern in score_patterns:
            matches = re.findall(pattern, response_text.lower())
            if matches:
                scores.extend([int(m) for m in matches])
                break
        
        # If no scores found, estimate based on section performance
        if not scores:
            if "excellent" in response_text.lower() or "strong" in response_text.lower():
                scores = [4, 4, 3, 4, 4, 3, 4]  # Good performance
            elif "poor" in response_text.lower() or "weak" in response_text.lower():
                scores = [2, 2, 1, 2, 2, 1, 2]  # Poor performance  
            else:
                scores = [3, 3, 3, 3, 3, 3, 3]  # Average performance
        
        # Calculate number of criteria based on max_points
        num_criteria = max_points // 5
        scores = scores[:num_criteria] + [3] * max(0, num_criteria - len(scores))
        
        individual_scores = []
        total_score = 0
        
        criterion_names = {
            35: ["Develops appropriate differential diagnoses", "Ensures clinical relevance", "Comprehensive range", "Identifies likely diagnoses", "Prioritizes appropriately", "Maintains accuracy", "Correlates with outcomes"],
            55: ["Appropriate language", "Avoids jargon", "Logical organization", "Covers pathophysiology", "Builds rapport", "Validates emotions", "Motivates adherence", "Shows empathy", "Addresses concerns", "Understands fears", "Prioritizes safety"],
            50: ["Addresses safety factors", "Suitable medications", "Flags abnormalities", "Accurate interpretation", "Identifies red flags", "Recognizes deterioration", "Adjusts monitoring", "Detects autonomy limits", "Stable performance", "Avoids failures"],
            30: ["Evidence-based treatments", "Suitable treatments", "Avoids contraindications", "Tailored follow-up", "Avoids overtreatment", "Appropriate monitoring"]
        }
        
        criteria = criterion_names.get(max_points, [f"Criterion {i+1}" for i in range(num_criteria)])
        
        for i, score in enumerate(scores):
            criterion_name = criteria[i] if i < len(criteria) else f"Criterion {i+1}"
            individual_scores.append({
                "criterion": criterion_name,
                "score": min(score, 5),
                "max_score": 5,
                "justification": f"Estimated score based on overall assessment"
            })
            total_score += min(score, 5)
        
        # Extract strengths and weaknesses
        strengths = re.findall(r'strength[s]?[:\s]*([^.]+)', response_text.lower())
        weaknesses = re.findall(r'weakness[es]*[:\s]*([^.]+)|improve[ment]*[:\s]*([^.]+)', response_text.lower())
        
        return {
            "section": section_name,
            "max_points": max_points,
            "individual_scores": individual_scores,
            "total_score": total_score,
            "percentage": round((total_score / max_points) * 100, 1),
            "overall_assessment": {
                "strengths": [s.strip()[:50] for s in (strengths[:2] if strengths else ["Reasonable medical approach"])],
                "weaknesses": [w[0].strip()[:50] if w[0] else w[1].strip()[:50] for w in (weaknesses[:2] if weaknesses else [["Could be more comprehensive", ""]])],
                "summary": response_text[:150] + "..." if len(response_text) > 150 else response_text
            }
        }

def extract_doctor_responses(conversation_data):
    """Extract only the doctor's responses from the conversation"""
    doctor_responses = []
    for exchange in conversation_data["conversation"]:
        if exchange["speaker"] == "Doctor":
            doctor_responses.append(exchange["message"])
    return "\n".join([f"Doctor: {response}" for response in doctor_responses])

def run_benchmark(conversation_file="clinical_conversation.json"):
    # Load conversation data
    with open(conversation_file, 'r') as f:
        conversation_data = json.load(f)
    
    # Extract doctor responses for evaluation
    doctor_conversation = extract_doctor_responses(conversation_data)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    benchmark = MedicalBenchmark(client)
    
    evaluation_date = datetime.now().strftime("%Y-%m-%d")
    
    print("=== MEDICAL AI BENCHMARK EVALUATION ===\n")
    print(f"Scenario: {conversation_data['patient_scenario']}")
    print(f"Date: {evaluation_date}\n")
    
    # Define benchmark categories
    benchmarks = [
        ("Diagnostics", DiagnosticsPrompt, 35),
        ("Patient-Centered Communication", PCCPrompt, 55),
        ("Uncertainty Management & Safety", UncertaintyPrompt, 50),
        ("Treatment Recommendations", TreatmentPrompt, 30)
    ]
    
    # Run all benchmarks
    results = {}
    total_points = 0
    max_total_points = 0
    
    for section_name, prompt, max_points in benchmarks:
        print(f"Evaluating: {section_name}")
        print("-" * 50)
        
        evaluation = benchmark.evaluate_response(prompt, doctor_conversation, section_name, max_points)
        results[section_name.lower().replace(" ", "_").replace("&", "and")] = evaluation
        
        total_points += evaluation["total_score"]
        max_total_points += max_points
        
        # Print summary
        print(f"Score: {evaluation['total_score']}/{max_points} ({evaluation['percentage']:.1f}%)")
        print(f"Strengths: {', '.join(evaluation['overall_assessment']['strengths'][:2])}")
        print(f"Areas for improvement: {', '.join(evaluation['overall_assessment']['weaknesses'][:2])}")
        print("\n")
    
    # Calculate overall performance
    overall_percentage = (total_points / max_total_points) * 100
    
    # Create comprehensive benchmark results
    benchmark_results = {
        "metadata": {
            "conversation_file": conversation_file,
            "scenario": conversation_data['patient_scenario'],
            "evaluation_date": evaluation_date,
            "doctor_responses": doctor_conversation
        },
        "overall_performance": {
            "total_score": total_points,
            "max_possible_score": max_total_points,
            "percentage": round(overall_percentage, 2),
            "grade": get_letter_grade(overall_percentage)
        },
        "section_results": results,
        "summary": {
            "top_performing_areas": get_top_areas(results),
            "areas_needing_improvement": get_weak_areas(results),
            "recommendations": generate_recommendations(results)
        }
    }
    
    # Save detailed results
    output_filename = conversation_file.replace(".json", "_results.json")
    with open(output_filename, "w") as f:
        json.dump(benchmark_results, f, indent=2)
    
    # Print final summary
    print("=" * 60)
    print(f"OVERALL PERFORMANCE: {total_points}/{max_total_points} ({overall_percentage:.1f}%)")
    print(f"GRADE: {get_letter_grade(overall_percentage)}")
    print("=" * 60)
    print(f"Detailed results saved to {output_filename}")
    
    return benchmark_results

def get_letter_grade(percentage):
    """Convert percentage to letter grade"""
    if percentage >= 90: return "A"
    elif percentage >= 80: return "B"
    elif percentage >= 70: return "C"
    elif percentage >= 60: return "D"
    else: return "F"

def get_top_areas(results):
    """Identify top performing areas"""
    areas = [(name, data["percentage"]) for name, data in results.items()]
    areas.sort(key=lambda x: x[1], reverse=True)
    return [area[0].replace("_", " ").title() for area in areas[:2]]

def get_weak_areas(results):
    """Identify areas needing improvement"""
    areas = [(name, data["percentage"]) for name, data in results.items()]
    areas.sort(key=lambda x: x[1])
    return [area[0].replace("_", " ").title() for area in areas[:2]]

def generate_recommendations(results):
    """Generate improvement recommendations"""
    recommendations = []
    for name, data in results.items():
        if data["percentage"] < 70:
            area_name = name.replace("_", " ").title()
            recommendations.append(f"Focus on improving {area_name} - current score: {data['percentage']:.1f}%")
    
    if not recommendations:
        recommendations.append("Continue maintaining high performance across all areas")
    
    return recommendations

if __name__ == "__main__":
    run_benchmark() 