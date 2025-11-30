import os
import tempfile
import subprocess


def encode_openstego(image_path: str, message: str, password: str = ""):
    """
    Encode message into image using OpenStego.
    
    Args:
        image_path: Path to cover image
        message: Secret message to hide
        password: Optional password for encryption
    
    Returns:
        dict: {
            'success': bool,
            'output_path': str (if success),
            'error': str (if failed)
        }
    """
    try:
        # Create temporary message file
        temp_msg = os.path.join(tempfile.gettempdir(), f"openstego_msg_{os.getpid()}.txt")
        with open(temp_msg, "w", encoding="utf-8") as f:
            f.write(message)
        
        # Generate output path
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(tempfile.gettempdir(), f"{base_name}_stego.png")
        
        # Build command - OpenStego requires -a (algorithm) flag
        # Try to find OpenStego JAR file first
        openstego_jar = None
        possible_paths = [
            os.path.expanduser("~/openstego/openstego.jar"),
            os.path.expanduser("~/.openstego/openstego.jar"),
            "/usr/local/bin/openstego.jar",
            "/usr/bin/openstego.jar",
            "/opt/openstego/openstego.jar",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                openstego_jar = path
                break
        
        # Build command - OpenStego requires -a flag for algorithm selection
        if openstego_jar:
            # Use Java to run the JAR file
            cmd = ["java", "-jar", openstego_jar, "embed", "-a", "lsb", "-mf", temp_msg, "-cf", image_path, "-sf", output_path]
        else:
            # Assume openstego is a wrapper script or in PATH
            cmd = ["openstego", "embed", "-a", "lsb", "-mf", temp_msg, "-cf", image_path, "-sf", output_path]
        
        if password:
            cmd.extend(["-p", password])
        
        # Run OpenStego
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=40,
        )
        
        # Clean up temp message file
        try:
            os.remove(temp_msg)
        except:
            pass
        
        # Check if output was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return {
                'success': True,
                'output_path': output_path,
                'message': 'Successfully encoded message into image'
            }
        else:
            error_msg = result.stderr or result.stdout or "Encoding failed"
            return {
                'success': False,
                'error': error_msg
            }
            
    except FileNotFoundError:
        return {
            'success': False,
            'error': "OpenStego not found. Install from: https://www.openstego.com/"
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': "OpenStego timed out (>40s)"
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Error: {str(e)}"
        }


def encode_steghide(image_path: str, message: str, password: str = ""):
    """
    Encode message into image using Steghide.
    
    Args:
        image_path: Path to cover image (JPG/BMP)
        message: Secret message to hide
        password: Optional password for encryption
    
    Returns:
        dict: {
            'success': bool,
            'output_path': str (if success),
            'error': str (if failed)
        }
    """
    try:
        # Create temporary message file
        temp_msg = os.path.join(tempfile.gettempdir(), f"steghide_msg_{os.getpid()}.txt")
        with open(temp_msg, "w", encoding="utf-8") as f:
            f.write(message)
        
        # Generate output path
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        ext = os.path.splitext(image_path)[1]
        output_path = os.path.join(tempfile.gettempdir(), f"{base_name}_stego{ext}")
        
        # Build command
        cmd = ["steghide", "embed", "-cf", image_path, "-ef", temp_msg, "-sf", output_path, "-f"]
        if password:
            cmd.extend(["-p", password])
        else:
            cmd.extend(["-p", ""])
        
        # Run Steghide
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=40,
        )
        
        # Clean up temp message file
        try:
            os.remove(temp_msg)
        except:
            pass
        
        # Check if output was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return {
                'success': True,
                'output_path': output_path,
                'message': 'Successfully encoded message into image'
            }
        else:
            error_msg = result.stderr or result.stdout or "Encoding failed"
            return {
                'success': False,
                'error': error_msg
            }
            
    except FileNotFoundError:
        return {
            'success': False,
            'error': "steghide not found. Install: sudo apt install steghide"
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': "steghide timed out (>40s)"
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Error: {str(e)}"
        }