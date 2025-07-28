#!/usr/bin/env python3
"""
PDF Outline Extractor
Extracts title and headings (H1, H2, H3) from PDF documents and outputs structured JSON.
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pymupdf

@dataclass
class HeadingCandidate:
    text: str
    page_num: int
    font_size: float
    font_name: str
    is_bold: bool
    position: Tuple[float, float]
    confidence: float = 0.0
    level: str = ""

# Constants
MAX_PAGES = 50
HEADING_PATTERNS = [
    r'^[0-9]+\.\s+[A-Z][A-Za-z\s]+$',  # 1. Introduction
    r'^[0-9]+\.[0-9]+\s+[A-Z][A-Za-z\s]+$',  # 1.1 Overview
    r'^[0-9]+\.[0-9]+\.[0-9]+\s+[A-Z][A-Za-z\s]+$',  # 1.1.1 Details
    r'^[A-Z][A-Z\s]+$',  # CHAPTER TITLE
    r'^(Section|Chapter|Part)\s+[A-Z\d]+[:.\\s-]+.+$',  # Chapter Title
]

def normalize_footer(text):
    """Normalize footer text for comparison"""
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    normalized_text = ' '.join(text.lower().split())
    return normalized_text

def calculate_confidence(candidate: HeadingCandidate, avg_font_size: float) -> float:
    """Calculate confidence score for a heading candidate"""
    score = 0.0
    
    # Font size scoring
    if candidate.font_size > avg_font_size * 1.2:
        score += 0.3
    elif candidate.font_size > avg_font_size * 1.1:
        score += 0.2
    
    # Bold text scoring
    if candidate.is_bold and candidate.font_size > avg_font_size * 1.1:
        score += 0.2
    
    # Pattern matching scoring
    compiled_patterns = [re.compile(pattern) for pattern in HEADING_PATTERNS]
    for pattern in compiled_patterns:
        if pattern.match(candidate.text):
            score += 0.4
            break
    
    # Case formatting scoring
    if candidate.text.isupper() and len(candidate.text) > 3:
        score += 0.2
    elif candidate.text.istitle():
        score += 0.1
    
    return min(score, 1.0)

def extract_title(headings: List[HeadingCandidate], pdf_path: str) -> str:
    """Extract document title from headings"""
    if not headings:
        return os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Look for the heading with highest font size and confidence
    first_heading = headings[0]
    title_parts = [first_heading.text]
    ref_font_name = first_heading.font_name
    ref_font_size = first_heading.font_size
    ref_confidence = first_heading.confidence
    
    # Check if consecutive headings have similar properties (part of title)
    for i in range(1, len(headings)):
        current_heading = headings[i]
        if (current_heading.font_name == ref_font_name and
            current_heading.font_size == ref_font_size and
            current_heading.confidence == ref_confidence):
            title_parts.append(current_heading.text)
        else:
            break
    
    if title_parts:
        return " ".join(title_parts)
    
    # Fallback to highest confidence heading
    sorted_by_confidence = sorted(headings, key=lambda x: -x.confidence)
    return sorted_by_confidence[0].text if sorted_by_confidence else "Untitled Document"

def extract_candidates_from_pdf(doc) -> List[HeadingCandidate]:
    """Extract heading candidates from PDF document"""
    max_pages = min(len(doc), MAX_PAGES)
    candidates = []
    
    for page_num in range(max_pages):
        page = doc[page_num]
        footer_margin = page.rect.height * 0.90
        text_dict = page.get_text("dict")
        
        for block in text_dict["blocks"]:
            if "lines" in block:
                x0, y0, x1, y1 = block["bbox"]
                if y1 > footer_margin:
                    continue
                
                for line in block["lines"]:
                    if not line["spans"]:
                        continue
                    
                    curr_group = []
                    for span in line["spans"]:
                        if not curr_group or (span["size"] == curr_group[-1]["size"]):
                            curr_group.append(span)
                        else:
                            if curr_group:
                                text = "".join([s["text"] for s in curr_group]).strip()
                                if text and len(text) > 3:
                                    span1 = curr_group[0]
                                    candidate = HeadingCandidate(
                                        text=text,
                                        page_num=page_num + 1,
                                        font_size=span1["size"],
                                        font_name=span1["font"],
                                        is_bold="Bold" in span1["font"].lower() or span1["flags"] & 2**4,
                                        position=(span1["bbox"][0], span1["bbox"][1])
                                    )
                                    candidates.append(candidate)
                            curr_group = [span]
                    
                    # Process the last group
                    if curr_group:
                        text = "".join([s["text"] for s in curr_group]).strip()
                        if text and len(text) > 3:
                            span1 = curr_group[0]
                            candidate = HeadingCandidate(
                                text=text,
                                page_num=page_num + 1,
                                font_size=span1["size"],
                                font_name=span1["font"],
                                is_bold="Bold" in span1["font"].lower() or span1["flags"] & 2**4,
                                position=(span1["bbox"][0], span1["bbox"][1])
                            )
                            candidates.append(candidate)
    
    return candidates

def filter_and_score_candidates(candidates: List[HeadingCandidate]) -> List[HeadingCandidate]:
    """Filter and score heading candidates"""
    # Calculate average font size
    font_sizes = [c.font_size for c in candidates]
    avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 11
    
    # Remove duplicates
    unique_candidates = []
    seen_texts = set()
    for candidate in candidates:
        normalized = re.sub(r'\s+', ' ', candidate.text.lower().strip())
        if normalized not in seen_texts:
            seen_texts.add(normalized)
            unique_candidates.append(candidate)
    
    # Score candidates
    scored_candidates = []
    for candidate in unique_candidates:
        score = calculate_confidence(candidate, avg_font_size)
        if score >= 0.1:  # Only keep candidates with decent confidence
            candidate.confidence = score
            scored_candidates.append(candidate)
    
    return scored_candidates

def classify_headings_improved(headings: List[HeadingCandidate], title_text: str) -> List[HeadingCandidate]:
    """
    Improved heading classification that considers font sizes, patterns, and context.
    Excludes the title from heading classification.
    """
    if not headings:
        return []
    
    # Filter out title text from headings
    filtered_headings = []
    for heading in headings:
        # Normalize both texts for comparison
        normalized_heading = re.sub(r'\s+', ' ', heading.text.lower().strip())
        normalized_title = re.sub(r'\s+', ' ', title_text.lower().strip())
        
        if normalized_heading != normalized_title:
            filtered_headings.append(heading)
    
    if not filtered_headings:
        return []
    
    # Sort by font size (descending), then by page and position
    sorted_headings = sorted(filtered_headings, key=lambda x: (-x.font_size, x.page_num, x.position[1]))
    
    # Get unique font sizes
    font_sizes = [h.font_size for h in sorted_headings]
    unique_sizes = sorted(set(font_sizes), reverse=True)
    
    # Improved classification logic
    for heading in sorted_headings:
        # Check for numbered patterns first
        if re.match(r'^[0-9]+\.\s+', heading.text):  # 1. Pattern
            heading.level = "H1"
        elif re.match(r'^[0-9]+\.[0-9]+\s+', heading.text):  # 1.1 Pattern
            heading.level = "H2"
        elif re.match(r'^[0-9]+\.[0-9]+\.[0-9]+\s+', heading.text):  # 1.1.1 Pattern
            heading.level = "H3"
        else:
            # Use font size based classification
            if len(unique_sizes) == 1:
                # If all headings have same font size, use content patterns
                if heading.text.isupper() or re.match(r'^(Chapter|Section|Part)', heading.text, re.IGNORECASE):
                    heading.level = "H1"
                else:
                    heading.level = "H2"
            elif heading.font_size >= unique_sizes[0]:
                heading.level = "H1"
            elif len(unique_sizes) > 1 and heading.font_size >= unique_sizes[1]:
                heading.level = "H2"
            else:
                heading.level = "H3"
    
    # Sort by page number and position for final output
    final_headings = sorted(sorted_headings, key=lambda x: (x.page_num, x.position[1]))
    return final_headings

def process_pdf(pdf_path: str, output_dir: str) -> bool:
    """Process a single PDF file and generate JSON output"""
    try:
        print(f"Processing: {pdf_path}")
        
        # Open PDF
        doc = pymupdf.open(pdf_path)
        
        # Extract candidates
        candidates = extract_candidates_from_pdf(doc)
        
        # Filter and score candidates
        scored_candidates = filter_and_score_candidates(candidates)
        
        # Extract title
        title = extract_title(scored_candidates, pdf_path)
        
        # Classify headings (excluding title)
        final_headings = classify_headings_improved(scored_candidates, title)
        
        # Create output structure
        outline = []
        for heading in final_headings:
            outline.append({
                "level": heading.level,
                "text": heading.text,
                "page": heading.page_num
            })
        
        output = {
            "title": title,
            "outline": outline
        }
        
        # Generate output filename
        pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(output_dir, f"{pdf_basename}.json")
        
        # Write JSON output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"Generated: {output_path}")
        print(f"Title: {title}")
        print(f"Found {len(outline)} headings")
        
        doc.close()
        return True
        
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return False

def main():
    """Main function to process all PDFs in input directory"""
    input_dir = "/app/input"
    output_dir = "/app/output"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        print(f"Input directory {input_dir} does not exist!")
        return
    
    # Find all PDF files
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in input directory!")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF
    successful = 0
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        if process_pdf(pdf_path, output_dir):
            successful += 1
    
    print(f"\nProcessing complete! {successful}/{len(pdf_files)} files processed successfully.")

if __name__ == "__main__":
    main()