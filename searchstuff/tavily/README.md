# Medical Information System

A comprehensive medical information research system that uses Tavily for web search and OpenAI for intelligent summarization. The system can process diseases from a CSV database, search for medical information, and store structured results.

## Features

- 🔍 **Advanced Medical Search**: Uses Tavily API for comprehensive medical information retrieval
- 🤖 **AI-Powered Summarization**: OpenAI GPT-4 structures information into standardized medical categories
- 📊 **CSV Database Integration**: Reads disease names from SNOMED CT medical terminology database
- 💾 **Dual Storage**: Saves results in both CSV and JSON formats
- 🔄 **Batch Processing**: Process multiple diseases with rate limiting
- 🎯 **Interactive Mode**: User-friendly interface for single disease queries
- 📈 **Structured Output**: Organizes information into symptoms, causes, treatments, etc.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API Keys

You need API keys for both Tavily and OpenAI:

```bash
export TAVILY_API_KEY="your_tavily_api_key"
export OPENAI_API_KEY="your_openai_api_key"
```

Or create a `.env` file:
```
TAVILY_API_KEY=your_tavily_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 3. Verify CSV Database

Ensure `output.csv` exists in the same directory. This file should contain medical terminology data with a `term` column containing disease names.

## Usage

### Interactive Mode

Run the main system for interactive use:

```bash
python medical_info_system.py
```

Choose from:
1. **Interactive mode**: Query individual diseases
2. **Batch processing**: Process multiple diseases from CSV
3. **Single query**: One-time disease lookup

### Demo Script

Run the demo to see the system in action:

```bash
python demo.py
```

### Programmatic Usage

```python
from medical_info_system import MedicalInfoSystem

# Initialize system
system = MedicalInfoSystem()

# Single disease query
result = system.process_disease("pneumonia")
print(result)

# Get diseases from CSV
diseases = system.get_diseases_from_csv(limit=10, filter_terms=['syndrome'])

# Batch processing
results = system.batch_process_diseases(diseases, delay=2.0)
```

## Output Structure

### CSV Output (`medical_research_results.csv`)
- `timestamp`: When the research was conducted
- `disease_name`: Name of the disease
- `search_query`: Query used for search
- `symptoms`: List of symptoms (semicolon-separated)
- `causes`: List of causes (semicolon-separated)
- `treatment_options`: Treatment approaches (semicolon-separated)
- `diagnosis_methods`: Diagnostic procedures (semicolon-separated)
- `risk_factors`: Risk factors (semicolon-separated)
- `prevention`: Prevention strategies (semicolon-separated)
- `prognosis`: Prognosis information
- `sources_count`: Number of sources used
- `search_confidence`: Average confidence score
- `raw_sources`: Complete source data (JSON)

### JSON Output (`medical_research_results.json`)
```json
{
  "disease_name": "Pneumonia",
  "symptoms": ["Cough with phlegm", "Fever", "Shortness of breath"],
  "causes": ["Bacterial infection", "Viral infection", "Fungal infection"],
  "treatment_options": ["Antibiotics", "Rest", "Supportive care"],
  "diagnosis_methods": ["Chest X-ray", "Blood tests", "Sputum culture"],
  "risk_factors": ["Age over 65", "Weakened immune system"],
  "prevention": ["Vaccination", "Good hygiene"],
  "prognosis": "Good with proper treatment",
  "summary": "Pneumonia is a lung infection...",
  "timestamp": "2024-01-01T12:00:00",
  "sources_count": 5,
  "search_confidence": 0.85,
  "raw_sources": [...]
}
```

## System Components

### `MedicalInfoSystem` Class

Main class that handles:
- API client initialization
- Disease extraction from CSV
- Medical information search and structuring
- Data storage in multiple formats

### Key Methods

- `get_diseases_from_csv()`: Extract diseases from CSV database
- `search_medical_info()`: Search and structure medical information
- `process_disease()`: Complete processing pipeline for one disease
- `batch_process_diseases()`: Process multiple diseases with rate limiting
- `interactive_mode()`: User-friendly interactive interface

## Configuration

### Filter Terms for CSV Extraction

Default filter terms for identifying diseases in CSV:
```python
disease_indicators = [
    'syndrome', 'disease', 'disorder', 'condition', 
    'infection', 'deficiency', 'tumor', 'cancer',
    'pneumonia', 'arthritis', 'diabetes', 'hypertension'
]
```

### Rate Limiting

- Default delay between API calls: 2 seconds
- Configurable in batch processing mode
- Prevents API rate limit violations

## Error Handling

The system includes comprehensive error handling:
- API failures are logged and stored
- Malformed responses are handled gracefully
- Large CSV files are processed in chunks
- Failed JSON parsing falls back to text processing

## Files Created

- `medical_research_results.csv`: Structured data for analysis
- `medical_research_results.json`: Detailed information with metadata
- Log files with timestamps and error information

## Requirements

- Python 3.8+
- Valid Tavily API key
- Valid OpenAI API key
- Internet connection for web searches
- CSV file with medical terminology data

## Limitations

- Depends on external APIs (Tavily, OpenAI)
- Information quality depends on web search results
- Rate limited by API quotas
- Large CSV processing may take time

## License

This project is for educational and research purposes. Please ensure compliance with API terms of service and medical information regulations.

## Support

For issues or questions:
1. Check API key configuration
2. Verify internet connection
3. Review log files for detailed errors
4. Ensure CSV file format is correct 