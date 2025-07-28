import os
import sys
import json
import logging
from src.utils import ensure_dir, save_json, get_pdf_files, get_output_path
from src.extractor import DocumentExtractor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
        
def extract_document_structure(pdf_path):
    """
    Extract title and headings from a PDF document using the DocumentExtractor.
    """
    extractor = DocumentExtractor()
    return extractor.extract_document_structure(pdf_path)

def process_pdf(pdf_path, output_dir):
    """
    Process a single PDF file and extract its structure.
    """
    try:
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract document structure
        output = extract_document_structure(pdf_path)
        
        # Save to JSON
        output_path = get_output_path(pdf_path, output_dir)
        save_json(output, output_path)
        
        logger.info(f"Successfully processed {pdf_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing {pdf_path}: {e}")
        return False

def process_directory(input_dir, output_dir):
    """
    Process all PDF files in the input directory.
    """
    # Get all PDF files
    pdf_files = get_pdf_files(input_dir)
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return 0
    
    # Process each PDF
    success_count = 0
    for pdf_path in pdf_files:
        if process_pdf(pdf_path, output_dir):
            success_count += 1
    
    logger.info(f"Processed {success_count}/{len(pdf_files)} PDF files successfully")
    return success_count

def main():
    # Define input and output directories
    input_dir = os.environ.get('INPUT_DIR', '/app/input')
    output_dir = os.environ.get('OUTPUT_DIR', '/app/output')
    
    # Ensure output directory exists
    ensure_dir(output_dir)
    
    logger.info(f"Starting PDF processing")
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    # Process all PDFs
    count = process_directory(input_dir, output_dir)
    
    logger.info(f"Completed processing {count} PDF files")
    return 0 if count > 0 else 1

if __name__ == "__main__":
    sys.exit(main())