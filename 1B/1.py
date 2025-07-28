import os
import sys
import json
from datetime import datetime
from utils import extract_text_by_page, rank_sections, refine_subsections

# -------------------- Configurable Parameters --------------------
INPUT_FOLDER = "sample_input"
OUTPUT_FOLDER = "output"
TOP_K_SECTIONS = 5
TOP_K_SUBSECTIONS = 3
MMR_LAMBDA = 0.7  # Controls relevance vs. diversity (0.7 = relevance-heavy)

# -------------------- Handle Input JSON --------------------
if len(sys.argv) < 2:
    print("❌ Please provide the input JSON file path.")
    print("👉 Usage: python main.py path/to/input.json")
    sys.exit(1)

INPUT_JSON_PATH = sys.argv[1]

if not os.path.exists(INPUT_JSON_PATH):
    print(f"❌ JSON file not found: {INPUT_JSON_PATH}")
    sys.exit(1)

with open(INPUT_JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Extract metadata
persona = data.get("persona", {}).get("role", "Unknown Persona")
job = data.get("job_to_be_done", {}).get("task", "Unknown Task")
query = f"{persona}. Task: {job}"

# Read PDF list
pdf_files = [os.path.join(INPUT_FOLDER, doc["filename"]) for doc in data.get("documents", [])]

# Optional output filename from challenge_id
challenge_id = data.get("challenge_info", {}).get("challenge_id")
test_case = data.get("challenge_info", {}).get("test_case_name")
output_basename = f"result_{challenge_id}_{test_case}" if challenge_id and test_case else os.path.splitext(os.path.basename(INPUT_JSON_PATH))[0]
output_path = os.path.join(OUTPUT_FOLDER, output_basename + ".json")

# -------------------- Extract Text from PDFs --------------------
all_chunks = []
missing_files = []

for pdf in pdf_files:
    if not os.path.exists(pdf):
        missing_files.append(os.path.basename(pdf))
        continue
    chunks = extract_text_by_page(pdf)
    all_chunks.extend(chunks)

if not all_chunks:
    print("❌ No valid documents found to process.")
    sys.exit(1)

# -------------------- Rank and Refine Sections --------------------
ranked_sections = rank_sections(query, all_chunks, top_k=TOP_K_SECTIONS, lambda_param=MMR_LAMBDA)
refined = refine_subsections(query, ranked_sections, top_k=TOP_K_SUBSECTIONS)

# -------------------- Generate Output JSON --------------------
output = {
    "metadata": {
        "documents": [os.path.basename(f) for f in pdf_files],
        "persona": persona,
        "job": job,
        "processing_timestamp": datetime.now().isoformat(),
        "missing_files": missing_files
    },
    "extracted_sections": [
        {
            "document": os.path.basename(sec["document"]),
            "page": sec["page"],
            "section_title": sec["title"],
            "importance_rank": i + 1
        }
        for i, sec in enumerate(ranked_sections)
    ],
    "subsection_analysis": refined
}

# -------------------- Save Output --------------------
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print(f"✅ Output saved to {output_path}")
if missing_files:
    print(f"⚠️ Warning: {len(missing_files)} PDF(s) were missing:")
    for name in missing_files:
        print(f"   - {name}")
