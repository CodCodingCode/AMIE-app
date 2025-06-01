import csv
import re
import os

def parse_disease_data_to_csv(input_filename, output_filename='diseases.csv', append_mode=True):
    """
    Parse disease data from text file to CSV with Title and Category columns
    
    Args:
        input_filename (str): Path to the input text file containing disease information
        output_filename (str): Name of the output CSV file
        append_mode (bool): If True, append to existing CSV. If False, overwrite.
    """
    
    # Read the text file
    try:
        with open(input_filename, 'r', encoding='utf-8') as file:
            text_data = file.read()
    except FileNotFoundError:
        print(f"Error: File '{input_filename}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []
    
    # Split the text into lines and clean them
    lines = text_data.strip().split('\n')
    
    diseases = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines, batch headers, and lines that don't contain disease data
        if not line or line.startswith('===') or 'Batch' in line:
            continue
        
        # Handle both formats:
        # 1. "Disease Name, Category: Category Name"
        # 2. "Disease Name: Disease Name, Category: Category Name"
        
        # First try the "Disease Name:" format
        disease_name_pattern = r'^Disease Name:\s*(.+?),\s*Category:\s*(.+)$'
        match = re.match(disease_name_pattern, line)
        
        if not match:
            # Try the standard format
            standard_pattern = r'^(.+?),\s*Category:\s*(.+)$'
            match = re.match(standard_pattern, line)
        
        if match:
            title = match.group(1).strip()
            category = match.group(2).strip()
            diseases.append([title, category])
        else:
            print(f"Warning: Could not parse line: {line}")
    
    # Check if file exists and if we should append
    file_exists = os.path.exists(output_filename)
    write_header = not file_exists or not append_mode
    
    # Open file in appropriate mode
    mode = 'a' if append_mode and file_exists else 'w'
    
    with open(output_filename, mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header only if file is new or we're overwriting
        if write_header:
            writer.writerow(['Title', 'Category'])
        
        # Write disease data
        writer.writerows(diseases)
    
    action = "appended" if append_mode and file_exists else "written"
    print(f"Successfully {action} {len(diseases)} diseases to {output_filename}")
    return diseases

def check_existing_csv(filename):
    """Check if CSV exists and show current count"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                rows = list(reader)
                # Subtract 1 for header row
                existing_count = len(rows) - 1 if len(rows) > 0 else 0
                print(f"Existing CSV has {existing_count} diseases")
                return existing_count
        except Exception as e:
            print(f"Error reading existing CSV: {e}")
            return 0
    else:
        print("CSV file doesn't exist yet - will create new one")
        return 0

# Example usage
if __name__ == "__main__":
    # Specify your input text file name here
    input_file = 'realdatasets/all_responses2.txt'  # Change this to your actual file name
    output_file = 'realdatasets/diseases.csv'
    
    # Check existing CSV
    existing_count = check_existing_csv(output_file)
    
    # Parse and append new diseases
    diseases = parse_disease_data_to_csv(input_file, output_file, append_mode=True)
    
    if diseases:  # Only show summary if parsing was successful
        # Display summary
        print(f"\nSummary:")
        print(f"New diseases added: {len(diseases)}")
        print(f"Total diseases in CSV: {existing_count + len(diseases)}")
        
        # Count by category
        categories = {}
        for title, category in diseases:
            categories[category] = categories.get(category, 0) + 1
        
        print("\nBreakdown of newly added diseases by category:")
        for category, count in sorted(categories.items()):
            print(f"  {category}: {count}")
        
        # Display first few entries as preview
        print(f"\nFirst 5 newly added entries:")
        for i, (title, category) in enumerate(diseases[:5]):
            print(f"  {i+1}. {title} -> {category}")
        
        print(f"\nDiseases successfully appended to '{output_file}'!")