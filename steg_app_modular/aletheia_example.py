"""
Example: How to Use Aletheia for Steganography Detection

This script demonstrates how to use Aletheia in your steganography detection app.
"""

from statistical_tools import run_aletheia_detection
import os

def example_basic_usage():
    """Basic example of using Aletheia."""
    
    image_path = "test_image.jpg"
    
    # Method 1: Auto detection (recommended)
    print("=== Using Aletheia Auto Detection ===")
    result = run_aletheia_detection(image_path, method="auto")
    
    if result["success"]:
        print(f"Steganography detected: {result['is_stego']}")
        print(f"Confidence: {result['confidence']:.1f}%")
        print(f"Method: {result['method_type']}")
        print(f"Interpretation: {result['interpretation']}")
        print(f"\nRaw Output:\n{result['raw_output']}")
    else:
        print(f"Error: {result['error']}")


def example_specific_methods():
    """Example using specific detection methods."""
    
    image_path = "test_image.jpg"
    
    methods = ["spa", "chi", "rs", "dct"]
    
    for method in methods:
        print(f"\n=== Using Aletheia {method.upper()} Method ===")
        result = run_aletheia_detection(image_path, method=method)
        
        if result["success"]:
            print(f"Result: {'Stego detected' if result['is_stego'] else 'Clean'}")
            print(f"Confidence: {result['confidence']:.1f}%")
        else:
            print(f"Error: {result['error']}")


def example_integration_with_app():
    """Example of integrating Aletheia into your analysis workflow."""
    
    image_path = "test_image.jpg"
    
    # Run multiple detection methods
    results = {}
    
    # Your existing methods
    from statistical_tools import run_stegexpose, run_deep_steganalysis
    results['stegexpose'] = run_stegexpose(image_path)
    results['deep_learning'] = run_deep_steganalysis(image_path)
    
    # Add Aletheia
    results['aletheia'] = run_aletheia_detection(image_path, method="auto")
    
    # Combine results
    print("\n=== Combined Analysis Results ===")
    for method, result in results.items():
        if result.get("success"):
            print(f"{method}: {result.get('confidence', 0):.1f}% confidence")
            if result.get('is_stego'):
                print(f"  → Steganography detected!")
        else:
            print(f"{method}: {result.get('error', 'Failed')}")


def example_batch_analysis():
    """Example of analyzing multiple images."""
    
    image_dir = "test_images/"
    images = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    print(f"\n=== Analyzing {len(images)} images ===")
    
    for image_file in images:
        image_path = os.path.join(image_dir, image_file)
        result = run_aletheia_detection(image_path, method="auto")
        
        status = "🔴 STEGO" if result.get("is_stego") else "🟢 CLEAN"
        conf = result.get("confidence", 0)
        
        print(f"{image_file}: {status} ({conf:.1f}%)")


if __name__ == "__main__":
    print("Aletheia Usage Examples")
    print("=" * 50)
    
    # Uncomment the example you want to run:
    
    # example_basic_usage()
    # example_specific_methods()
    # example_integration_with_app()
    # example_batch_analysis()
    
    print("\nNote: Make sure Aletheia is installed before running these examples.")
    print("Installation: git clone https://github.com/daniellerch/aletheia.git")

