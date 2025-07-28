# Adobe India Hackathon 2025
***
## Task 1A
This tool extracts document titles and headings (H1, H2, H3) from PDF documents and outputs structured JSON files.

### Features

- Automatically processes all PDF files in the input directory
- Generates corresponding JSON files with document outline
- Improved heading classification algorithm
- Excludes document title from heading classification
- Supports various PDF formats and structures
- Dockerized for easy deployment

### Files

- `pdf_outline_extractor.py` - Main Python script
- `Dockerfile` - Docker configuration
- `requirements.txt` - Python dependencies
***
## Task 1B
### Problem & Solution
Modern documents — whether academic papers, reports, or technical manuals — are lengthy and dense. Personas such as researchers, analysts, or students often need to quickly find the sections that directly support their tasks. Our solution bridges this gap by combining semantic search, diversity‑aware ranking, and context‑aware subsection analysis into one streamlined pipeline. By embedding the persona and task into a single semantic query, we ensure that the extracted content is highly tailored to the end‑user’s intent.

### Key Features
Generic & Domain‑Agnostic: Works with research papers, business reports, textbooks, or any PDF collection.
Persona‑Aware Search: Uses a unified embedding of persona and task to guide content selection.
Maximal Marginal Relevance (MMR): Ensures both relevance and diversity across documents, avoiding repetitive or redundant results.
Granular Subsection Refinement: Splits sections into smaller paragraphs and re‑ranks them for fine‑grained insights.
Lightweight & Fast: Runs on CPU only, processes 3–10 PDFs in under 60 seconds, and uses models <1 GB.
Structured JSON Output: Produces machine‑readable results with metadata, ranked sections, and detailed subsections.

### How It Works
Input: A JSON file specifying the persona, task, and list of PDFs.
Parsing: Pages are extracted from PDFs using pdfplumber.
Embedding: Documents, persona, and task are encoded with a lightweight sentence‑transformers model (all‑MiniLM‑L6‑v2).
Ranking: Sections are scored by semantic similarity and reranked using MMR to balance relevance and diversity.
Subsection Analysis: Top sections are broken into smaller paragraphs and re‑ranked for precision.
Output: A structured JSON file with metadata, ranked sections, and refined subsections.

### Usage
Place PDFs in sample_input/ and provide a JSON input describing the persona, task, and document list. Run:

bash
Copy
Edit
python main.py input_jsons/your_input.json
Results are stored in output/.

### Deployment
The project includes a Dockerfile for easy containerized execution.
