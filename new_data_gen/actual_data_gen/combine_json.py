import json
import sys

def combine_json_files(file1_path, file2_path, output_path):
    """
    Combine two JSON files into one output file
    
    Args:
        file1_path (str): Path to first JSON file
        file2_path (str): Path to second JSON file  
        output_path (str): Path for combined output file
    """
    try:
        # Read first JSON file
        with open(file1_path, 'r', encoding='utf-8') as f1:
            data1 = json.load(f1)
        
        # Read second JSON file
        with open(file2_path, 'r', encoding='utf-8') as f2:
            data2 = json.load(f2)
        
        # Combine the data
        combined_data = []
        
        # Handle first file - convert to list if single object
        if isinstance(data1, list):
            combined_data.extend(data1)
        else:
            combined_data.append(data1)
        
        # Handle second file - convert to list if single object
        if isinstance(data2, list):
            combined_data.extend(data2)
        else:
            combined_data.append(data2)
        
        # Write combined data to output file
        with open(output_path, 'w', encoding='utf-8') as output_file:
            json.dump(combined_data, output_file, indent=2, ensure_ascii=False)
        
        print(f"Successfully combined {len(combined_data)} records!")
        print(f"Output saved to: {output_path}")
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) != 4:
        print("Usage: python combine_json.py <file1.json> <file2.json> <output.json>")
        sys.exit(1)
    
    file1_path = sys.argv[1]
    file2_path = sys.argv[2]
    output_path = sys.argv[3]
    
    combine_json_files(file1_path, file2_path, output_path)

# Alternative function for direct use without command line
def combine_files(file1_name="file1.json", file2_name="file2.json", output_name="combined.json"):
    """Direct function call version"""
    combine_json_files(file1_name, file2_name, output_name)

def run_combine():
    """Non-command line version - just run this function"""
    # Edit these filenames as needed
    file1_name = "medical_research_results.json"
    file2_name = "medical_research_results2.json" 
    output_name = "combined.json"
    
    print("🔗 Combining JSON files...")
    print(f"   File 1: {file1_name}")
    print(f"   File 2: {file2_name}")
    print(f"   Output: {output_name}")
    
    combine_files(file1_name, file2_name, output_name)

if __name__ == "__main__":
    # Just run the combine function directly
    run_combine()