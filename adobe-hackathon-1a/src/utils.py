import os
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def ensure_dir(directory):
    """
    Ensure that a directory exists, creating it if necessary.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def save_json(data, output_path):
    """
    Save data as JSON to the specified path.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved JSON to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {output_path}: {e}")
        return False

def get_pdf_files(input_dir):
    """
    Get all PDF files from the input directory.
    """
    pdf_files = []
    for file in os.listdir(input_dir):
        if file.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(input_dir, file))
    return pdf_files

def get_output_path(input_path, output_dir):
    """
    Generate the output JSON path based on the input PDF path.
    """
    filename = os.path.basename(input_path)
    name_without_ext = os.path.splitext(filename)[0]
    return os.path.join(output_dir, f"{name_without_ext}.json")