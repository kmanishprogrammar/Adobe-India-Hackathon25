import os
import subprocess
import time
import json

def run_test_case(test_case):
    """Run a single test case"""
    print(f"\n{'='*50}")
    print(f"Running test case: {test_case}")
    print(f"{'='*50}\n")
    
    # Run the main.py script with the test case
    cmd = ["python", "src/main.py", "--test_case", test_case]
    start_time = time.time()
    
    try:
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(process.stdout)
        
        # Check if output file was created
        base_dir = os.path.dirname(os.path.abspath(__file__))
        test_case_dir = os.path.join(base_dir, 'Test cases', test_case)
        output_dir = os.path.join(test_case_dir, 'Output' if os.path.exists(os.path.join(test_case_dir, 'Output')) else 'output')
        output_path = os.path.join(output_dir, 'challenge1b_output.json')
        
        if os.path.exists(output_path):
            # Load and validate output
            with open(output_path, 'r', encoding='utf-8') as f:
                output = json.load(f)
            
            # Check if output has required fields
            if all(key in output for key in ['metadata', 'extracted_sections', 'subsection_analysis']):
                print(f"✅ Test case {test_case} completed successfully")
                print(f"Output file: {output_path}")
                print(f"Extracted {len(output['extracted_sections'])} sections")
                print(f"Analyzed {len(output['subsection_analysis'])} subsections")
            else:
                print(f"❌ Test case {test_case} output is missing required fields")
        else:
            print(f"❌ Test case {test_case} failed to create output file")
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Test case {test_case} failed with error:")
        print(e.stderr)
    
    end_time = time.time()
    print(f"Total time: {end_time - start_time:.2f} seconds")

def main():
    # Get all test case directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_cases_dir = os.path.join(base_dir, 'Test cases')
    
    test_cases = []
    for item in os.listdir(test_cases_dir):
        if os.path.isdir(os.path.join(test_cases_dir, item)):
            test_cases.append(item)
    
    if not test_cases:
        print("No test cases found")
        return
    
    print(f"Found {len(test_cases)} test cases: {', '.join(test_cases)}")
    
    # Run each test case
    for test_case in test_cases:
        run_test_case(test_case)
    
    print("\nAll test cases completed")

if __name__ == "__main__":
    main()