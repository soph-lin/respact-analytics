# ReSpAct Analytics

A Python-based analysis tool for processing and analyzing dialogue interactions, with a focus on identifying patterns, classifications, and insights from conversational data.

## Overview

This codebase provides tools for:

- Analyzing dialogue patterns and interactions
- Classifying user statements and responses
- Processing and aggregating conversation data
- Generating insights from dialogue analysis

## Features

- Dialogue pattern analysis
- Statement classification
- Token counting and analysis
- Feedback pattern detection
- Question pattern identification
- Data aggregation and visualization
- Google Sheets integration for annotation management

## Technology Stack

- **Python 3.x**
- **Data Processing & Analysis**
  - pandas
  - numpy
  - scikit-learn
- **Visualization**
  - matplotlib
  - seaborn
- **API Integration**
  - together
  - openai
- **Utilities**
  - python-dotenv
  - pathlib
- **Google Apps Script**
  - Spreadsheet integration
  - JSON conversion utilities

## Setup

1. Clone the repository:

```bash
git clone [repository-url]
cd respact-analyze
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

   - Create a `.env` file in the root directory
   - Add your API keys:
     ```
     TOGETHER_API_KEY=your_api_key_here
     ```

5. Google Apps Script Setup:
   - Open your Google Spreadsheet with annotations
   - Go to Extensions > Apps Script
   - Copy the contents of `src/google-app-script/Annotations.gs` into the script editor
   - Save and authorize the script

## Project Structure

```
respact-analyze/
├── src/
│   ├── analyze/         # Analysis tools and utilities
│   ├── annotate/        # Annotation and classification tools
│   ├── utils/           # Utility functions and shared code
│   └── google-app-script/  # Google Apps Script utilities
│       └── Annotations.gs  # Script for spreadsheet integration
├── annotations/         # Annotation data
├── classification/      # Classification results
├── rollouts/           # Processed data and results
├── requirements.txt    # Project dependencies
└── .env               # Environment variables
```

## Data Pipeline

1. **Annotation Collection**:

   - Annotations are collected in Google Spreadsheets
   - Multiple versions (v1, v2) can be maintained and compared

2. **Data Extraction**:

   - Google Apps Script (`Annotations.gs`) converts spreadsheet data to JSON
   - Features include:
     - Conversion of spreadsheet annotations to JSON format
     - Version comparison between v1 and v2 annotations
     - Automatic file creation in Google Drive

3. **Analysis Pipeline**:
   - JSON files are processed by the Python analysis tools
   - `DialogueAnalyzer` processes the converted data
   - Results are stored in the classification and rollouts directories

## Usage

### Google Apps Script Functions

1. `convertAnnotationsToJSON()`:

   - Converts spreadsheet annotations to JSON format
   - Creates separate JSON files for each folder
   - Supports multiple versions (v1, v2)

2. `compareAnnotations()`:
   - Compares annotations between v1 and v2
   - Creates a "Comparison" sheet highlighting differences
   - Helps track changes in annotation patterns

### Python Analysis Components

- `DialogueAnalyzer`: Core analysis class for processing dialogue data
- `Classifier`: Tools for categorizing and labeling statements
- Various utility functions for data processing and visualization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
