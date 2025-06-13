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