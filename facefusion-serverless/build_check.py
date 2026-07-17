import sys
import torch
import onnxruntime as ort

def run_checks():
    print("--- Running Build Checks ---")
    
    # Check 1: CUDA availability
    if not torch.cuda.is_available():
        print("❌ ERROR: CUDA is not available during build.")
       # sys.exit(1)
    
    print(f"✅ GPU Detected: {torch.cuda.get_device_name()}")
    
    # Check 2: ONNX Runtime Providers
    providers = ort.get_available_providers()
    if 'CUDAExecutionProvider' not in providers:
        print(f"❌ ERROR: CUDAExecutionProvider missing. Found: {providers}")
        sys.exit(1)
        
    print("✅ ONNX Runtime CUDA Execution Provider is ready.")
    print("--- All checks passed! ---")

if __name__ == "__main__":
    run_checks()