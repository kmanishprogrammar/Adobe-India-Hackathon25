import os
import json
import argparse
import time
from pdf_processor import PDFProcessor

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Persona-Driven Document Intelligence')
    parser.add_argument('--test_case', type=str, required=True, help='Test case directory name')
    args = parser.parse_args()
    
    # Set up paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_case_dir = os.path.join(base_dir, 'Test cases', args.test_case)
    input_dir = os.path.join(test_case_dir, 'Input')
    output_dir = os.path.join(test_case_dir, 'Output' if os.path.exists(os.path.join(test_case_dir, 'Output')) else 'output')
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find input scenario file
    scenario_file = os.path.join(input_dir, 'input_scnerio.json')
    if not os.path.exists(scenario_file):
        # Try alternative spelling
        scenario_file = os.path.join(input_dir, 'input_scenario.json')
        if not os.path.exists(scenario_file):
            print(f"Error: Could not find input scenario file in {input_dir}")
            return
    
    # Load input scenario
    try:
        with open(scenario_file, 'r', encoding='utf-8') as f:
            input_scenario = json.load(f)
    except Exception as e:
        print(f"Error loading input scenario: {str(e)}")
        return
    
    # Set output path
    output_path = os.path.join(output_dir, 'challenge1b_output.json')
    
    # Initialize PDF processor with optimized settings
    model_path = os.path.join(base_dir, 'models', 'all-MiniLM-L6-v2')
    import multiprocessing
    processor = PDFProcessor(
        model_path=model_path,
        max_workers=min(multiprocessing.cpu_count() + 2, 12),  # Use more workers for better parallelism
        batch_size=16  # Smaller batch size for faster processing
    )
    
    # Process documents
    print(f"Processing documents for test case: {args.test_case}")
    start_time = time.time()
    
    try:
        output, processing_time = processor.process_documents(input_scenario, input_dir, output_path)
        print(f"Output saved to: {output_path}")
        print(f"Total processing time: {processing_time:.2f} seconds")
    except Exception as e:
        print(f"Error processing documents: {str(e)}")
        return

if __name__ == "__main__":
    main()