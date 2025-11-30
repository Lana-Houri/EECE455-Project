import os
import tempfile
import numpy as np
from PIL import Image


def encode_image_in_image(cover_path: str, secret_path: str, password: str = "", bits_per_channel: int = 1):
    """
    Encode a secret image into a cover image using LSB steganography.
    
    Args:
        cover_path: Path to cover image
        secret_path: Path to secret image to hide
        password: Optional password (for future encryption support)
        bits_per_channel: Number of LSBs to use (1-4, default 1 for best invisibility)
    
    Returns:
        dict: {
            'success': bool,
            'output_path': str (if success),
            'error': str (if failed),
            'message': str (info message)
        }
    """
    try:
        # Load images
        cover_img = Image.open(cover_path)
        secret_img = Image.open(secret_path)
        
        # Convert cover to RGB if needed
        if cover_img.mode in ('RGBA', 'LA', 'P'):
            cover_img = cover_img.convert('RGB')
        elif cover_img.mode not in ('RGB',):
            cover_img = cover_img.convert('RGB')
        
        # Convert secret to RGB if needed
        if secret_img.mode in ('RGBA', 'LA', 'P'):
            secret_img = secret_img.convert('RGB')
        elif secret_img.mode not in ('RGB',):
            secret_img = secret_img.convert('RGB')
        
        # Resize secret image if needed
        cover_width, cover_height = cover_img.size
        secret_width, secret_height = secret_img.size
        
        # Calculate maximum secret image size based on LSB capacity
        # Each pixel can hide bits_per_channel bits per color channel (3 channels)
        max_secret_pixels = (cover_width * cover_height * 3 * bits_per_channel) // 24  # 24 bits per pixel for RGB
        
        if secret_width * secret_height > max_secret_pixels:
            # Resize secret image to fit
            scale = np.sqrt(max_secret_pixels / (secret_width * secret_height))
            new_width = int(secret_width * scale)
            new_height = int(secret_height * scale)
            secret_img = secret_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            secret_width, secret_height = secret_img.size
        
        # Convert to numpy arrays
        cover_array = np.array(cover_img, dtype=np.uint8)
        secret_array = np.array(secret_img, dtype=np.uint8)
        
        # Reshape secret image to 1D array for easier embedding
        secret_flat = secret_array.flatten()
        
        # Calculate how many bits we need to hide
        secret_bits = []
        for pixel in secret_flat:
            # Convert each pixel value to binary (8 bits)
            secret_bits.extend([int(bit) for bit in format(pixel, '08b')])
        
        # Add metadata: width (32 bits), height (32 bits), total bits
        width_bits = [int(bit) for bit in format(secret_width, '032b')]
        height_bits = [int(bit) for bit in format(secret_height, '032b')]
        
        # Combine metadata + secret data
        all_secret_bits = width_bits + height_bits + secret_bits
        
        # Create stego image array (copy of cover)
        stego_array = cover_array.copy()
        stego_flat = stego_array.flatten()
        
        # Check if secret fits
        required_bits = len(all_secret_bits)
        available_bits = len(stego_flat) * bits_per_channel
        
        if required_bits > available_bits:
            return {
                'success': False,
                'error': f'Secret image too large. Required: {required_bits} bits, Available: {available_bits} bits. Try reducing secret image size or using fewer LSBs.'
            }
        
        # Embed secret bits into LSBs
        bit_idx = 0
        for pixel_idx in range(len(stego_flat)):
            if bit_idx >= len(all_secret_bits):
                break
            
            # Get current pixel value
            pixel_value = stego_flat[pixel_idx]
            
            # Clear LSBs (bits_per_channel bits)
            mask = (0xFF << bits_per_channel) & 0xFF
            cleared_pixel = pixel_value & mask
            
            # Embed secret bits
            for bit_pos in range(bits_per_channel):
                if bit_idx < len(all_secret_bits):
                    secret_bit = all_secret_bits[bit_idx]
                    cleared_pixel |= (secret_bit << bit_pos)
                    bit_idx += 1
            
            stego_flat[pixel_idx] = cleared_pixel
        
        # Reshape back to image dimensions
        stego_array = stego_flat.reshape(stego_array.shape)
        
        # Create output image
        stego_img = Image.fromarray(stego_array, 'RGB')
        
        # Generate output path
        base_name = os.path.splitext(os.path.basename(cover_path))[0]
        output_path = os.path.join(tempfile.gettempdir(), f"{base_name}_image_stego.png")
        
        # Save as PNG (lossless)
        stego_img.save(output_path, 'PNG')
        
        return {
            'success': True,
            'output_path': output_path,
            'message': f'Successfully embedded {secret_width}x{secret_height} image into cover using {bits_per_channel} LSB(s) per channel'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Encoding error: {str(e)}'
        }


def decode_image_from_image(stego_path: str, password: str = "", bits_per_channel: int = 1):
    """
    Decode a secret image from a stego image using LSB steganography.
    
    Args:
        stego_path: Path to stego image
        password: Optional password (for future decryption support)
        bits_per_channel: Number of LSBs used (1-4, default 1)
    
    Returns:
        dict: {
            'success': bool,
            'output_path': str (if success),
            'error': str (if failed),
            'message': str (info message)
        }
    """
    try:
        # Load stego image
        stego_img = Image.open(stego_path)
        
        # Convert to RGB if needed
        if stego_img.mode in ('RGBA', 'LA', 'P'):
            stego_img = stego_img.convert('RGB')
        elif stego_img.mode not in ('RGB',):
            stego_img = stego_img.convert('RGB')
        
        # Convert to numpy array
        stego_array = np.array(stego_img, dtype=np.uint8)
        stego_flat = stego_array.flatten()
        
        # Extract bits from LSBs
        extracted_bits = []
        for pixel in stego_flat:
            # Extract bits_per_channel LSBs
            for bit_pos in range(bits_per_channel):
                bit = (pixel >> bit_pos) & 1
                extracted_bits.append(bit)
        
        # Extract metadata (width and height)
        if len(extracted_bits) < 64:  # Need at least 64 bits for metadata
            return {
                'success': False,
                'error': 'Image too small or no embedded data found'
            }
        
        # Extract width (first 32 bits)
        width_bits = extracted_bits[0:32]
        width = int(''.join(map(str, width_bits)), 2)
        
        # Extract height (next 32 bits)
        height_bits = extracted_bits[32:64]
        height = int(''.join(map(str, height_bits)), 2)
        
        # Validate dimensions
        if width <= 0 or height <= 0 or width > 10000 or height > 10000:
            return {
                'success': False,
                'error': 'Invalid embedded image dimensions. Image may not contain steganographic data or wrong LSB count.'
            }
        
        # Calculate total pixels and required bits
        total_pixels = width * height * 3  # RGB = 3 channels
        required_bits = 64 + (total_pixels * 8)  # 64 for metadata + 8 bits per pixel value
        
        if len(extracted_bits) < required_bits:
            return {
                'success': False,
                'error': f'Not enough data extracted. Expected {required_bits} bits, got {len(extracted_bits)}. Wrong LSB count?'
            }
        
        # Extract pixel data (skip first 64 bits which are metadata)
        pixel_bits = extracted_bits[64:64 + (total_pixels * 8)]
        
        # Convert bits to pixel values
        secret_pixels = []
        for i in range(0, len(pixel_bits), 8):
            if i + 8 > len(pixel_bits):
                break
            byte_bits = pixel_bits[i:i+8]
            pixel_value = int(''.join(map(str, byte_bits)), 2)
            secret_pixels.append(pixel_value)
        
        # Reshape to image dimensions
        if len(secret_pixels) < total_pixels:
            return {
                'success': False,
                'error': f'Incomplete pixel data. Expected {total_pixels} pixels, got {len(secret_pixels)}'
            }
        
        secret_array = np.array(secret_pixels[:total_pixels], dtype=np.uint8)
        secret_array = secret_array.reshape((height, width, 3))
        
        # Create output image
        secret_img = Image.fromarray(secret_array, 'RGB')
        
        # Generate output path
        base_name = os.path.splitext(os.path.basename(stego_path))[0]
        output_path = os.path.join(tempfile.gettempdir(), f"{base_name}_extracted.png")
        
        # Save extracted image
        secret_img.save(output_path, 'PNG')
        
        return {
            'success': True,
            'output_path': output_path,
            'message': f'Successfully extracted {width}x{height} image from stego image'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Decoding error: {str(e)}'
        }

