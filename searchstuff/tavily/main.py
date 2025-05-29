import csv

def convert_text_to_csv(input_file_path, output_file_path):
    """
    Convert a tab-separated text file to CSV format
    """
    try:
        with open(input_file_path, 'r', encoding='utf-8') as input_file:
            with open(output_file_path, 'w', newline='', encoding='utf-8') as output_file:
                csv_writer = csv.writer(output_file)
                
                # Define headers based on your data structure
                headers = [
                    'id', 
                    'effectiveTime', 
                    'active', 
                    'moduleId', 
                    'conceptId', 
                    'languageCode', 
                    'typeId', 
                    'term', 
                    'caseSignificanceId'
                ]
                
                # Write headers
                csv_writer.writerow(headers)
                
                # Process each line
                for line_num, line in enumerate(input_file, 1):
                    line = line.strip()
                    
                    # Skip empty lines
                    if not line:
                        continue
                    
                    # Split by tabs (assuming tab-separated)
                    columns = line.split('\t')
                    
                    # Handle cases where there might be fewer columns
                    while len(columns) < len(headers):
                        columns.append('')
                    
                    # Write the row
                    csv_writer.writerow(columns[:len(headers)])
                    
                    # Print progress for large files
                    if line_num % 1000 == 0:
                        print(f"Processed {line_num} lines...")
        
        print(f"Conversion completed successfully!")
        print(f"Output saved to: {output_file_path}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file_path}' not found.")
    except Exception as e:
        print(f"Error during conversion: {str(e)}")

def convert_with_auto_detection(input_file_path, output_file_path):
    """
    Convert text file to CSV with automatic delimiter detection
    """
    try:
        with open(input_file_path, 'r', encoding='utf-8') as input_file:
            # Read first few lines to detect delimiter
            sample_lines = []
            for i, line in enumerate(input_file):
                if i < 5:  # Check first 5 lines
                    sample_lines.append(line.strip())
                else:
                    break
            
            # Reset file pointer
            input_file.seek(0)
            
            # Detect delimiter
            delimiter = '\t'  # Default to tab
            for line in sample_lines:
                if '\t' in line and len(line.split('\t')) > 3:
                    delimiter = '\t'
                    break
                elif '|' in line and len(line.split('|')) > 3:
                    delimiter = '|'
                    break
                elif ';' in line and len(line.split(';')) > 3:
                    delimiter = ';'
                    break
            
            print(f"Detected delimiter: {'Tab' if delimiter == '\\t' else delimiter}")
            
            with open(output_file_path, 'w', newline='', encoding='utf-8') as output_file:
                csv_writer = csv.writer(output_file)
                
                for line_num, line in enumerate(input_file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Split by detected delimiter
                    columns = line.split(delimiter)
                    
                    # Clean up columns (remove extra whitespace)
                    columns = [col.strip() for col in columns]
                    
                    csv_writer.writerow(columns)
                    
                    if line_num % 1000 == 0:
                        print(f"Processed {line_num} lines...")
        
        print(f"Conversion completed successfully!")
        print(f"Output saved to: {output_file_path}")
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")

# Usage example
if __name__ == "__main__":
    # Replace these paths with your actual file paths
    input_file = "sct2_Description_Full-en_INT_20250501.txt"  # Updated input file
    output_file = "output.csv"  # Updated output CSV file
    
    print("Starting conversion...")
    print("=" * 50)
    
    # Try automatic detection first
    convert_with_auto_detection(input_file, output_file)
    
    # Alternative: Use the structured approach if you know the exact format
    # convert_text_to_csv(input_file, output_file)
    
    print("=" * 50)
    print("Conversion process finished!")

# Additional utility function for large files
def convert_large_file_chunked(input_file_path, output_file_path, chunk_size=10000):
    """
    Convert large text files to CSV in chunks to handle memory efficiently
    """
    try:
        with open(input_file_path, 'r', encoding='utf-8') as input_file:
            with open(output_file_path, 'w', newline='', encoding='utf-8') as output_file:
                csv_writer = csv.writer(output_file)
                
                chunk = []
                total_lines = 0
                
                for line in input_file:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Split by tabs and clean
                    columns = [col.strip() for col in line.split('\t')]
                    chunk.append(columns)
                    
                    # Write chunk when it reaches the specified size
                    if len(chunk) >= chunk_size:
                        csv_writer.writerows(chunk)
                        total_lines += len(chunk)
                        print(f"Processed {total_lines} lines...")
                        chunk = []
                
                # Write remaining lines
                if chunk:
                    csv_writer.writerows(chunk)
                    total_lines += len(chunk)
                
                print(f"Total lines processed: {total_lines}")
        
        print(f"Large file conversion completed!")
        print(f"Output saved to: {output_file_path}")
        
    except Exception as e:
        print(f"Error during large file conversion: {str(e)}")

