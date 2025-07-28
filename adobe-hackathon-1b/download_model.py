import os
import sys
from sentence_transformers import SentenceTransformer

def download_model():
    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)
    
    # Download and save the model
    print("Downloading sentence-transformer model...")
    model_name = 'all-MiniLM-L6-v2'
    model = SentenceTransformer(model_name)
    
    # Save the model to the models directory
    model_path = os.path.join('models', model_name)
    model.save(model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    download_model()