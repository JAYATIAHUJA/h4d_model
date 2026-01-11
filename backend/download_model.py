"""
Download model from GitHub if not present locally (for Render deployment).
"""
from pathlib import Path
import urllib.request
import sys

MODEL_URL = "https://github.com/JAYATIAHUJA/h4d_model/raw/main/backend/model/artifacts/flood_model_v1.pkl"
MODEL_PATH = Path(__file__).parent / "model" / "artifacts" / "flood_model_v1.pkl"

def download_model():
    """Download model file if it doesn't exist."""
    if MODEL_PATH.exists():
        print(f"✓ Model already exists at {MODEL_PATH}")
        return True
    
    print(f"Downloading model from {MODEL_URL}...")
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print(f"✓ Model downloaded successfully to {MODEL_PATH}")
        return True
    except Exception as e:
        print(f"✗ Failed to download model: {e}")
        return False

if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)
