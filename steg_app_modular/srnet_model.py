"""
SRNet (Spatial Rich Model Network) for Image Steganalysis
=========================================================
A CNN-based steganalysis model for detecting JPEG steganography.

Detects: J-UNIWARD, nsF5, UERD, Steghide, OutGuess

Reference: 
"Deep Residual Network for Steganalysis of Digital Images" (2019)
https://github.com/brijeshiitg/Pytorch-implementation-of-SRNet

Usage:
    from srnet_model import SRNet, load_srnet
    
    # Load pre-trained model
    model = load_srnet("path/to/srnet.pth")
    
    # Or use directly
    model = SRNet()
    model.load_state_dict(torch.load("path/to/srnet.pth"))
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class SRMFilter(nn.Module):
    """
    SRM (Spatial Rich Model) preprocessing layer.
    Applies high-pass filters to extract noise residuals.
    """
    def __init__(self):
        super(SRMFilter, self).__init__()
        
        # Define SRM filters (30 filters from spatial domain features)
        # These are fixed filters, not learned
        self.srm_filters = nn.Conv2d(1, 30, kernel_size=5, padding=2, bias=False)
        
        # Initialize with SRM filter kernels
        srm_weights = self._get_srm_kernels()
        self.srm_filters.weight.data = srm_weights
        self.srm_filters.weight.requires_grad = False  # Fixed filters
    
    def _get_srm_kernels(self):
        """Get standard SRM filter kernels."""
        # Simplified SRM kernels (3 main types)
        kernels = []
        
        # 1st order edge filters
        edge1 = torch.tensor([
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 1, -1, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0]
        ], dtype=torch.float32)
        kernels.append(edge1)
        
        edge2 = torch.tensor([
            [0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, -1, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0]
        ], dtype=torch.float32)
        kernels.append(edge2)
        
        # 2nd order filters
        edge3 = torch.tensor([
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 1, -2, 1, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0]
        ], dtype=torch.float32)
        kernels.append(edge3)
        
        # 3rd order SPAM filters
        spam = torch.tensor([
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [-1, 3, -3, 1, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0]
        ], dtype=torch.float32)
        kernels.append(spam)
        
        # Square 3x3 edge
        square3 = torch.tensor([
            [0, 0, 0, 0, 0],
            [0, -1, 2, -1, 0],
            [0, 2, -4, 2, 0],
            [0, -1, 2, -1, 0],
            [0, 0, 0, 0, 0]
        ], dtype=torch.float32)
        kernels.append(square3)
        
        # Square 5x5 edge
        square5 = torch.tensor([
            [-1, 2, -2, 2, -1],
            [2, -6, 8, -6, 2],
            [-2, 8, -12, 8, -2],
            [2, -6, 8, -6, 2],
            [-1, 2, -2, 2, -1]
        ], dtype=torch.float32) / 12
        kernels.append(square5)
        
        # Duplicate and rotate kernels to get 30 filters
        all_kernels = []
        for k in kernels:
            all_kernels.append(k)
            all_kernels.append(torch.rot90(k, 1, [0, 1]))
            all_kernels.append(torch.rot90(k, 2, [0, 1]))
            all_kernels.append(torch.rot90(k, 3, [0, 1]))
            all_kernels.append(torch.flip(k, [0]))
        
        # Stack and reshape for conv2d: (out_channels, in_channels, H, W)
        weights = torch.stack(all_kernels[:30])
        weights = weights.unsqueeze(1)  # Add input channel dimension
        
        return weights
    
    def forward(self, x):
        return self.srm_filters(x)


class ResidualBlock(nn.Module):
    """Residual block with batch normalization."""
    def __init__(self, in_channels, out_channels, stride=1):
        super(ResidualBlock, self).__init__()
        
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, 
                               stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3,
                               stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        
        # Skip connection
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1,
                         stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )
    
    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        out = F.relu(out)
        return out


class SRNet(nn.Module):
    """
    SRNet: Spatial Rich Model Network for Steganalysis
    
    Architecture:
    1. SRM preprocessing (optional, can be disabled)
    2. Initial convolution layers
    3. Residual blocks (12 blocks)
    4. Global average pooling
    5. Fully connected classifier
    
    Input: Grayscale image (1, H, W) - will be converted if RGB
    Output: [P(cover), P(stego)] probabilities
    """
    
    def __init__(self, use_srm=False, num_classes=2):
        super(SRNet, self).__init__()
        
        self.use_srm = use_srm
        
        if use_srm:
            self.srm = SRMFilter()
            in_channels = 30
        else:
            in_channels = 1
        
        # Type 1: Initial convolution
        self.conv1 = nn.Conv2d(in_channels, 64, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        
        # Type 2: Residual layers
        self.layer1 = self._make_layer(64, 64, 2)      # 2 blocks
        self.layer2 = self._make_layer(64, 128, 2)     # 2 blocks  
        self.layer3 = self._make_layer(128, 256, 2)    # 2 blocks
        self.layer4 = self._make_layer(256, 512, 2)    # 2 blocks
        
        # Type 3: More residual layers
        self.layer5 = self._make_layer(512, 512, 2)    # 2 blocks
        self.layer6 = self._make_layer(512, 512, 2)    # 2 blocks
        
        # Global average pooling
        self.avgpool = nn.AdaptiveAvgPool2d(1)
        
        # Fully connected classifier
        self.fc = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes)
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _make_layer(self, in_channels, out_channels, num_blocks, stride=1):
        """Create a layer with multiple residual blocks."""
        layers = []
        layers.append(ResidualBlock(in_channels, out_channels, stride))
        for _ in range(1, num_blocks):
            layers.append(ResidualBlock(out_channels, out_channels))
        return nn.Sequential(*layers)
    
    def _initialize_weights(self):
        """Initialize model weights."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        # SRM preprocessing (optional)
        if self.use_srm:
            x = self.srm(x)
        
        # Initial convolution
        x = F.relu(self.bn1(self.conv1(x)))
        
        # Residual layers with progressive downsampling
        x = self.layer1(x)
        x = F.avg_pool2d(x, 2)  # Downsample
        
        x = self.layer2(x)
        x = F.avg_pool2d(x, 2)
        
        x = self.layer3(x)
        x = F.avg_pool2d(x, 2)
        
        x = self.layer4(x)
        x = F.avg_pool2d(x, 2)
        
        x = self.layer5(x)
        x = self.layer6(x)
        
        # Global average pooling
        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        
        # Classifier
        x = self.fc(x)
        
        return x


class YedroudjNet(nn.Module):
    """
    Yedroudj-Net: Efficient CNN for Spatial Steganalysis
    
    Simpler and faster alternative to SRNet.
    Good for spatial domain steganography (PNG images).
    """
    
    def __init__(self, num_classes=2):
        super(YedroudjNet, self).__init__()
        
        # Preprocessing with high-pass filter
        self.prep = nn.Conv2d(1, 30, kernel_size=5, padding=2, bias=False)
        
        # Feature extraction
        self.features = nn.Sequential(
            nn.Conv2d(30, 30, kernel_size=5, padding=2),
            nn.BatchNorm2d(30),
            nn.ReLU(inplace=True),
            nn.AvgPool2d(2),
            
            nn.Conv2d(30, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.AvgPool2d(2),
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.AvgPool2d(2),
            
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            
            nn.AdaptiveAvgPool2d(1)
        )
        
        # Classifier
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        x = self.prep(x)
        x = self.features(x)
        x = self.classifier(x)
        return x


class EfficientStegoNet(nn.Module):
    """
    Lightweight steganalysis network.
    Fastest option with reasonable accuracy.
    """
    
    def __init__(self, num_classes=2):
        super(EfficientStegoNet, self).__init__()
        
        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            
            # Block 2
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            
            # Block 3
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            
            # Block 4
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1)
        )
        
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


def load_srnet(model_path: str, use_srm: bool = False, device: str = None):
    """
    Load a pre-trained SRNet model.
    
    Args:
        model_path: Path to the .pth weights file
        use_srm: Whether to use SRM preprocessing
        device: Device to load model on ('cuda', 'cpu', or None for auto)
    
    Returns:
        Loaded SRNet model in eval mode
    """
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    model = SRNet(use_srm=use_srm)
    
    # Load weights
    state_dict = torch.load(model_path, map_location=device)
    
    # Handle different state dict formats
    if 'model_state_dict' in state_dict:
        state_dict = state_dict['model_state_dict']
    elif 'state_dict' in state_dict:
        state_dict = state_dict['state_dict']
    
    # Try to load (may fail if architecture doesn't match)
    try:
        model.load_state_dict(state_dict, strict=True)
    except RuntimeError:
        # Try loading with strict=False for partial matches
        model.load_state_dict(state_dict, strict=False)
        print("Warning: Loaded weights with strict=False (some layers may not match)")
    
    model = model.to(device)
    model.eval()
    
    return model


def predict_stego(model, image_path: str, device: str = None):
    """
    Predict steganography probability for an image.
    
    Args:
        model: Loaded SRNet model
        image_path: Path to image file
        device: Device to run inference on
    
    Returns:
        dict with cover_prob, stego_prob, and prediction
    """
    import torchvision.transforms as transforms
    from PIL import Image
    
    if device is None:
        device = next(model.parameters()).device
    
    # Load and preprocess image
    img = Image.open(image_path)
    
    # Convert to grayscale if needed
    if img.mode != 'L':
        img = img.convert('L')
    
    # Transform
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize([0.5], [0.5])
    ])
    
    img_tensor = transform(img).unsqueeze(0).to(device)
    
    # Inference
    with torch.no_grad():
        output = model(img_tensor)
        probs = F.softmax(output, dim=1).cpu().numpy()[0]
    
    return {
        'cover_prob': float(probs[0]),
        'stego_prob': float(probs[1]),
        'prediction': 'stego' if probs[1] > probs[0] else 'cover',
        'confidence': float(max(probs))
    }


# Command-line interface for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python srnet_model.py <model_path> <image_path>")
        print("Example: python srnet_model.py ~/steg_models/srnet.pth test.jpg")
        sys.exit(1)
    
    model_path = sys.argv[1]
    image_path = sys.argv[2]
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        sys.exit(1)
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        sys.exit(1)
    
    print(f"Loading model from: {model_path}")
    model = load_srnet(model_path)
    
    print(f"Analyzing: {image_path}")
    result = predict_stego(model, image_path)
    
    print(f"\nResults:")
    print(f"  Cover probability: {result['cover_prob']:.4f}")
    print(f"  Stego probability: {result['stego_prob']:.4f}")
    print(f"  Prediction: {result['prediction'].upper()}")
    print(f"  Confidence: {result['confidence']:.2%}")