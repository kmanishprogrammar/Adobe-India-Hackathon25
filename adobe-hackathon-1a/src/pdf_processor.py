import os
import logging
from .extractor import DocumentExtractor
from .utils import save_json, get_output_path

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.document_extractor = DocumentExtractor()
    
    def process_pdf(self, pdf_path, output_dir):
        """
        Process a single PDF file and extract its structure.
        """
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            
            # Extract document structure (title and headings)
            output = self.document_extractor.extract_document_structure(pdf_path)
            
            # Save to JSON
            output_path = get_output_path(pdf_path, output_dir)
            save_json(output, output_path)
            
            logger.info(f"Successfully processed {pdf_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            return False
    
    def process_directory(self, input_dir, output_dir):
        """
        Process all PDF files in the input directory.
        """
        # Get all PDF files
        pdf_files = []
        for file in os.listdir(input_dir):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(input_dir, file))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {input_dir}")
            return 0
        
        # Process each PDF
        success_count = 0
        for pdf_path in pdf_files:
            if self.process_pdf(pdf_path, output_dir):
                success_count += 1
        
        logger.info(f"Processed {success_count}/{len(pdf_files)} PDF files successfully")
        return success_count