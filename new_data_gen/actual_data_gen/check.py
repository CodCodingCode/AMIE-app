import json
from typing import List, Set, Dict, Any


def extract_disease_names_from_json(file_path: str) -> List[str]:
    """
    Extract only the disease names (keys) from a JSON file

    Args:
        file_path: Path to the JSON file

    Returns:
        List of disease names (keys)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        disease_names = list(data.keys())
        print(f"📁 Loaded {len(disease_names)} disease names from {file_path}")

        return disease_names

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in file: {file_path}")
        return []


def extract_disease_names_with_vignettes(file_path: str) -> List[str]:
    """
    Extract disease names that have actual vignette lists (not "NO")

    Args:
        file_path: Path to the JSON file

    Returns:
        List of disease names that have vignettes
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        diseases_with_vignettes = []
        diseases_without_vignettes = []

        for disease_name, vignettes in data.items():
            if isinstance(vignettes, list) and len(vignettes) > 0:
                diseases_with_vignettes.append(disease_name)
            else:
                diseases_without_vignettes.append(disease_name)

        print(f"📁 Total diseases: {len(data)}")
        print(f"✅ Diseases with vignettes: {len(diseases_with_vignettes)}")
        print(f"❌ Diseases without vignettes: {len(diseases_without_vignettes)}")

        return diseases_with_vignettes

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in file: {file_path}")
        return []


def save_disease_names_to_file(
    disease_names: List[str], output_path: str, format_type: str = "list"
) -> None:
    """
    Save disease names to a file in various formats

    Args:
        disease_names: List of disease names
        output_path: Path for output file
        format_type: "list", "json", "txt", or "csv"
    """
    try:
        if format_type == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(disease_names, f, indent=2, ensure_ascii=False)

        elif format_type == "txt":
            with open(output_path, "w", encoding="utf-8") as f:
                for name in disease_names:
                    f.write(f"{name}\n")

        elif format_type == "csv":
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("disease_name\n")  # Header
                for name in disease_names:
                    f.write(f'"{name}"\n')

        else:  # Default to list format (Python list in text file)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("disease_names = [\n")
                for name in disease_names:
                    f.write(f'    "{name}",\n')
                f.write("]\n")

        print(f"💾 Saved {len(disease_names)} disease names to {output_path}")

    except Exception as e:
        print(f"❌ Error saving file: {e}")


def print_disease_names(disease_names: List[str], limit: int = None) -> None:
    """
    Print disease names to console

    Args:
        disease_names: List of disease names
        limit: Maximum number to print (None for all)
    """
    total = len(disease_names)
    to_print = disease_names[:limit] if limit else disease_names

    print(f"\n📋 DISEASE NAMES ({len(to_print)}/{total}):")
    print("-" * 50)

    for i, name in enumerate(to_print, 1):
        print(f"{i:3d}. {name}")

    if limit and total > limit:
        print(f"... and {total - limit} more diseases")


def get_disease_statistics(disease_names: List[str]) -> Dict[str, Any]:
    """
    Get basic statistics about disease names

    Args:
        disease_names: List of disease names

    Returns:
        Dictionary with statistics
    """
    if not disease_names:
        return {}

    lengths = [len(name) for name in disease_names]
    word_counts = [len(name.split()) for name in disease_names]

    stats = {
        "total_diseases": len(disease_names),
        "avg_name_length": sum(lengths) / len(lengths),
        "min_name_length": min(lengths),
        "max_name_length": max(lengths),
        "avg_word_count": sum(word_counts) / len(word_counts),
        "longest_name": max(disease_names, key=len),
        "shortest_name": min(disease_names, key=len),
    }

    return stats


def print_statistics(stats: Dict[str, Any]) -> None:
    """Print disease name statistics"""
    if not stats:
        print("No statistics available")
        return

    print(f"\n📊 DISEASE NAME STATISTICS:")
    print("-" * 40)
    print(f"Total diseases: {stats['total_diseases']}")
    print(f"Average name length: {stats['avg_name_length']:.1f} characters")
    print(f"Average word count: {stats['avg_word_count']:.1f} words")
    print(
        f"Shortest name: '{stats['shortest_name']}' ({stats['min_name_length']} chars)"
    )
    print(f"Longest name: '{stats['longest_name']}' ({stats['max_name_length']} chars)")


def search_disease_names(disease_names: List[str], search_term: str) -> List[str]:
    """
    Search for diseases containing a specific term

    Args:
        disease_names: List of disease names
        search_term: Term to search for

    Returns:
        List of matching disease names
    """
    search_term_lower = search_term.lower()
    matches = [name for name in disease_names if search_term_lower in name.lower()]

    print(f"🔍 Found {len(matches)} diseases containing '{search_term}':")
    for match in matches:
        print(f"   - {match}")

    return matches


# Main execution
if __name__ == "__main__":
    # File paths
    input_file = "/Users/owner/Downloads/coding projects/AMIE-app/new_data_gen/actual_data_gen/validated_disease_vignettes.json"  # Update this path

    print("🏥 DISEASE NAME EXTRACTOR")
    print("=" * 50)

    # Option 1: Get ALL disease names (including those with "NO")
    print("\n1️⃣ EXTRACTING ALL DISEASE NAMES:")
    all_disease_names = extract_disease_names_from_json(input_file)

    # Option 2: Get only disease names that have vignettes
    print("\n2️⃣ EXTRACTING DISEASES WITH VIGNETTES:")
    diseases_with_vignettes = extract_disease_names_with_vignettes(input_file)

    # Display results
    print("\n" + "=" * 60)
    print("📋 RESULTS:")

    # Show first 10 disease names
    print_disease_names(diseases_with_vignettes, limit=10)

    # Show statistics
    stats = get_disease_statistics(diseases_with_vignettes)
    print_statistics(stats)

    # Save results in different formats
    print(f"\n💾 SAVING RESULTS:")
    save_disease_names_to_file(diseases_with_vignettes, "disease_names.json", "json")
    save_disease_names_to_file(diseases_with_vignettes, "disease_names.txt", "txt")
    save_disease_names_to_file(diseases_with_vignettes, "disease_names.csv", "csv")
    save_disease_names_to_file(diseases_with_vignettes, "disease_names_list.py", "list")

    # Example search
    print(f"\n🔍 EXAMPLE SEARCH:")
    search_disease_names(diseases_with_vignettes, "Syndrome")

    print(
        f"\n✨ COMPLETE! Extracted {len(diseases_with_vignettes)} disease names with vignettes."
    )

    # Usage examples
    print(f"\n💡 USAGE EXAMPLES:")
    print("# Access the disease names list:")
    print("disease_names = extract_disease_names_with_vignettes('your_file.json')")
    print("print(disease_names[0])  # First disease name")
    print("print(len(disease_names))  # Count of diseases")
    print()
    print("# Search for specific diseases:")
    print("matches = search_disease_names(disease_names, 'Cancer')")
    print()
    print("# Get all names (including 'NO' entries):")
    print("all_names = extract_disease_names_from_json('your_file.json')")
