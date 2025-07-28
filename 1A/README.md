# PDF Outline Extractor

This tool extracts document titles and headings (H1, H2, H3) from PDF documents and outputs structured JSON files.

## Features

- Automatically processes all PDF files in the input directory
- Generates corresponding JSON files with document outline
- Improved heading classification algorithm
- Excludes document title from heading classification
- Supports various PDF formats and structures
- Dockerized for easy deployment

## Files

- `pdf_outline_extractor.py` - Main Python script
- `Dockerfile` - Docker configuration
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## Usage

### With Docker (Recommended)

1. **Build the Docker image:**
   ```bash
   docker build --platform linux/amd64 -t pdf-outline-extractor:v1.0 .
   ```

2. **Run the container:**
   ```bash
   docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-outline-extractor:v1.0
   ```

### Manual Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the script:**
   ```bash
   python pdf_outline_extractor.py
   ```

## Input/Output

- **Input:** Place PDF files in the `input/` directory
- **Output:** JSON files will be generated in the `output/` directory with the same name as the PDF

### Output Format

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Chapter 1: Introduction",
      "page": 1
    },
    {
      "level": "H2", 
      "text": "1.1 Overview",
      "page": 2
    },
    {
      "level": "H3",
      "text": "1.1.1 Background",
      "page": 3
    }
  ]
}
```

## Improvements Made

### 1. Enhanced Heading Classification
- **Pattern-based classification**: Recognizes numbered patterns (1., 1.1, 1.1.1)
- **Content-aware classification**: Considers text patterns like "Section", "Chapter"
- **Font-size based fallback**: Uses font sizes when patterns aren't available
- **Context-aware logic**: Better handles edge cases and diverse document structures

### 2. Title Exclusion
- Automatically identifies and excludes the document title from heading classification
- Prevents title from being classified as H1, H2, or H3
- Uses text normalization for accurate comparison

### 3. Robust Processing
- Better error handling for malformed PDFs
- Improved duplicate detection and removal
- Enhanced text extraction and cleaning

### 4. Confidence Scoring System
- Evaluates heading candidates based on multiple factors:
  - Font size relative to document average
  - Bold formatting
  - Pattern matching
  - Text case formatting
- Only includes headings with sufficient confidence scores

## Algorithm Details

### Heading Classification Logic

```python
# 1. Check for numbered patterns first
if re.match(r'^[0-9]+\.\s+', heading.text):  # 1. Pattern
    heading.level = "H1"
elif re.match(r'^[0-9]+\.[0-9]+\s+', heading.text):  # 1.1 Pattern  
    heading.level = "H2"
elif re.match(r'^[0-9]+\.[0-9]+\.[0-9]+\s+', heading.text):  # 1.1.1 Pattern
    heading.level = "H3"
else:
    # Use font size based classification
    if heading.font_size >= unique_sizes[0]:
        heading.level = "H1"
    elif len(unique_sizes) > 1 and heading.font_size >= unique_sizes[1]:
        heading.level = "H2"
    else:
        heading.level = "H3"
```

### Key Improvements Over Original Code

1. **Pattern Recognition First**: Prioritizes content patterns over font sizes
2. **Title Exclusion**: Filters out document title from heading classification
3. **Better Edge Case Handling**: Handles documents with uniform font sizes
4. **Confidence Filtering**: Only processes high-confidence heading candidates

## Docker Configuration

The solution uses a multi-stage approach:
- Base image: Python 3.11-slim
- Installs only necessary system dependencies
- Creates isolated environment for PDF processing
- No network access during execution for security

## Testing

The solution has been tested with various PDF types:
- Simple forms and documents
- Complex technical documents
- Multi-page reports
- Documents with diverse formatting

## Troubleshooting

**Common Issues:**

1. **No headings detected**: PDF may have non-standard formatting
2. **Incorrect classification**: Adjust confidence thresholds in the code
3. **Docker build fails**: Ensure platform compatibility with `--platform linux/amd64`

**Debug Mode:**
Add print statements in the `classify_headings_improved` function to see intermediate results.

## License

This tool is provided as-is for educational and commercial use.