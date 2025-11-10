#!/usr/bin/env python3
"""
Lungmask Segmentation Method

This script performs automatic lung segmentation on chest CT images using deep learning
models from the lungmask library. It automatically identifies and segments lung regions
from medical imaging data.

INPUT REQUIREMENTS:
- Input must be a 3D CT image volume
- Supported formats: NIfTI (.nii, .nii.gz), DICOM (directory or single file), 
  NRRD (.nrrd), MetaImage (.mha, .mhd), Analyze, and other SimpleITK-supported formats
- Image must be readable by SimpleITK library
- Expected image dimension: 3D (width x height x depth)

OUTPUT:
- Returns a JSON response containing:
  - status: "success" or "error"
  - data.mask_file: Path to the generated lung mask file (NIfTI format)
  - data.mask_size_bytes: Size of the mask file in bytes
  - data.statistics: Detailed statistics including:
    * total_voxels: Total number of voxels in the mask
    * lung_voxels: Number of voxels identified as lung tissue
    * background_voxels: Number of background voxels
    * lung_volume_mm3: Total lung volume in cubic millimeters
    * lung_volume_cm3: Total lung volume in cubic centimeters
    * unique_labels: List of unique label values in the mask
    * mask_size: Dimensions of the mask [width, height, depth]
    * spacing_mm: Voxel spacing in millimeters [x, y, z]
  - metadata: Processing metadata including model used, input image info, etc.

PARAMETERS:
- model (string, optional): Segmentation model to use
  * "R231" (default): Standard lung segmentation model, good for general use
  * "LTRCLobes": Lung and lobe segmentation, provides more detailed anatomical regions
  * "R231CovidWeb": Optimized for COVID-19 analysis and lung pathology detection
- force_cpu (boolean, optional): Force CPU processing even if GPU is available
  * false (default): Use GPU if available for faster processing
  * true: Force CPU usage (useful for GPU memory issues or consistency)

ERROR HANDLING:
The script includes comprehensive error handling for:
- Missing or invalid input files
- Unsupported image formats
- Image dimension mismatches (expects 3D images)
- GPU/CPU processing errors
- Model loading failures
- File I/O errors
All errors are returned as JSON with detailed error messages.

DEPENDENCIES:
- SimpleITK: For medical image I/O and processing
- lungmask: Deep learning lung segmentation library
- numpy: For array operations
- torch: Required by lungmask for model inference

Usage:
    python3 main.py <input_file> <metadata_file> <params_file>

Where:
    input_file: Path to the input CT image file
    metadata_file: Path to JSON file containing metadata about the input
    params_file: Path to JSON file containing method parameters
"""

import sys
import os
import json
import traceback
from pathlib import Path
import logging

# Suppress lungmask logging to stdout (we only want JSON output)
logging.getLogger('lungmask').setLevel(logging.ERROR)

import SimpleITK as sitk
import numpy as np
from lungmask import mask as lungmask_mask
from lungmask.mask import LMInferer


def validate_file_exists(file_path, file_description):
    """Validate that a file exists and is readable."""
    if not file_path:
        return False, f"{file_description} path is empty"
    
    if not os.path.exists(file_path):
        return False, f"{file_description} does not exist: {file_path}"
    
    if not os.path.isfile(file_path):
        return False, f"{file_description} is not a file: {file_path}"
    
    if not os.access(file_path, os.R_OK):
        return False, f"{file_description} is not readable: {file_path}"
    
    return True, None


def load_json_file(file_path, file_description):
    """Load and parse a JSON file with error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {file_description}: {str(e)}"
    except Exception as e:
        return None, f"Error reading {file_description}: {str(e)}"


def read_image_file(image_path):
    """Read an image file using SimpleITK with comprehensive error handling."""
    try:
        # Check if file exists
        exists, error = validate_file_exists(image_path, "Input image")
        if not exists:
            return None, error
        
        # Try to read the image
        try:
            image = sitk.ReadImage(image_path)
        except Exception as e:
            return None, f"Failed to read image file '{image_path}': {str(e)}. Supported formats: NIfTI (.nii, .nii.gz), DICOM, NRRD, MHA, MHD, and other SimpleITK-supported formats."
        
        # Validate image is not empty
        if image.GetSize()[0] == 0 or image.GetSize()[1] == 0:
            return None, f"Image appears to be empty (size: {image.GetSize()})"
        
        # Check image dimension (should be 3D for CT)
        if image.GetDimension() != 3:
            return None, f"Expected 3D image, but got {image.GetDimension()}D image. Size: {image.GetSize()}"
        
        return image, None
        
    except Exception as e:
        return None, f"Unexpected error reading image: {str(e)}"


def apply_lungmask(image, model_name="R231", force_cpu=False):
    """Apply lungmask segmentation to an image.
    
    Args:
        image: SimpleITK Image object (required)
        model_name: Model name to use
        force_cpu: Whether to force CPU usage
    """
    try:
        # Validate model name
        valid_models = ["R231", "LTRCLobes", "R231CovidWeb"]
        if model_name not in valid_models:
            return None, f"Invalid model name '{model_name}'. Valid options: {', '.join(valid_models)}"
        
        # Validate image is a SimpleITK Image
        if not isinstance(image, sitk.Image):
            return None, f"Image must be a SimpleITK Image object, got {type(image).__name__}"
        
        # Store image metadata for later
        image_spacing = image.GetSpacing()
        image_origin = image.GetOrigin()
        image_direction = image.GetDirection()
        
        # Use LMInferer directly (lungmask.apply() is deprecated and has bugs)
        # LMInferer accepts modelname in constructor, not as parameter to apply()
        # Redirect lungmask stdout messages to stderr to avoid interfering with JSON output
        from contextlib import redirect_stdout
        import io
        
        try:
            if force_cpu:
                # Force CPU by setting CUDA_VISIBLE_DEVICES
                import os as os_module
                original_cuda = os_module.environ.get('CUDA_VISIBLE_DEVICES')
                os_module.environ['CUDA_VISIBLE_DEVICES'] = ''
                try:
                    # Redirect stdout to stderr for lungmask output
                    f = io.StringIO()
                    with redirect_stdout(f):
                        inferer = LMInferer(modelname=model_name, force_cpu=True)
                        mask = inferer.apply(image)
                    # Print lungmask messages to stderr
                    lungmask_output = f.getvalue()
                    if lungmask_output:
                        print(lungmask_output, file=sys.stderr, flush=True)
                finally:
                    if original_cuda is not None:
                        os_module.environ['CUDA_VISIBLE_DEVICES'] = original_cuda
                    else:
                        os_module.environ.pop('CUDA_VISIBLE_DEVICES', None)
            else:
                # Redirect stdout to stderr for lungmask output
                f = io.StringIO()
                with redirect_stdout(f):
                    inferer = LMInferer(modelname=model_name, force_cpu=False)
                    mask = inferer.apply(image)
                # Print lungmask messages to stderr
                lungmask_output = f.getvalue()
                if lungmask_output:
                    print(lungmask_output, file=sys.stderr, flush=True)
        except RuntimeError as e:
            if "CUDA" in str(e) or "GPU" in str(e):
                return None, f"GPU error: {str(e)}. Try setting force_cpu=true parameter."
            return None, f"Runtime error during lungmask application: {str(e)}"
        except Exception as e:
            return None, f"Error applying lungmask: {str(e)}"
        
        # Validate mask was created
        if mask is None:
            return None, "Lungmask returned None (no mask generated)"
        
        # Convert mask to SimpleITK Image (it should be a numpy array)
        if isinstance(mask, np.ndarray):
            mask_sitk = sitk.GetImageFromArray(mask)
            # Restore image metadata
            mask_sitk.SetSpacing(image_spacing)
            mask_sitk.SetOrigin(image_origin)
            mask_sitk.SetDirection(image_direction)
            mask = mask_sitk
        elif isinstance(mask, sitk.Image):
            # Already a SimpleITK Image, ensure metadata matches
            mask.SetSpacing(image_spacing)
            mask.SetOrigin(image_origin)
            mask.SetDirection(image_direction)
        else:
            return None, f"Lungmask returned unexpected type: {type(mask).__name__}"
        
        # Validate mask dimensions match image
        if mask.GetSize() != image.GetSize():
            return None, f"Mask size {mask.GetSize()} does not match image size {image.GetSize()}"
        
        return mask, None
        
    except Exception as e:
        return None, f"Unexpected error applying lungmask: {str(e)}"


def get_mask_statistics(mask):
    """Calculate statistics about the mask."""
    try:
        mask_array = sitk.GetArrayFromImage(mask)
        
        # Count voxels
        total_voxels = mask_array.size
        lung_voxels = np.sum(mask_array > 0)
        background_voxels = total_voxels - lung_voxels
        
        # Calculate volumes (assuming spacing is in mm)
        spacing = mask.GetSpacing()
        voxel_volume_mm3 = spacing[0] * spacing[1] * spacing[2]
        lung_volume_mm3 = lung_voxels * voxel_volume_mm3
        lung_volume_cm3 = lung_volume_mm3 / 1000.0
        
        # Get unique labels
        unique_labels = np.unique(mask_array)
        
        return {
            "total_voxels": int(total_voxels),
            "lung_voxels": int(lung_voxels),
            "background_voxels": int(background_voxels),
            "lung_volume_mm3": float(lung_volume_mm3),
            "lung_volume_cm3": float(lung_volume_cm3),
            "unique_labels": [int(x) for x in unique_labels],
            "mask_size": list(mask.GetSize()),
            "spacing_mm": list(spacing)
        }, None
        
    except Exception as e:
        return None, f"Error calculating mask statistics: {str(e)}"


def main():
    """Main function."""
    try:
        # Parse command line arguments
        if len(sys.argv) < 4:
            result = {
                "status": "error",
                "message": "Usage: python3 main.py <input_file> <metadata_file> <params_file>"
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        input_file = sys.argv[1]
        metadata_file = sys.argv[2]
        params_file = sys.argv[3]
        
        # Validate input file exists
        exists, error = validate_file_exists(input_file, "Input file")
        if not exists:
            result = {
                "status": "error",
                "message": error
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        # Validate metadata file exists
        exists, error = validate_file_exists(metadata_file, "Metadata file")
        if not exists:
            result = {
                "status": "error",
                "message": error
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        # Validate params file exists
        exists, error = validate_file_exists(params_file, "Parameters file")
        if not exists:
            result = {
                "status": "error",
                "message": error
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        # Load parameters
        params, error = load_json_file(params_file, "parameters file")
        if error:
            result = {
                "status": "error",
                "message": error
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        # Extract parameters with defaults
        model_name = params.get("model", "R231")
        force_cpu = params.get("force_cpu", False)
        
        # Validate parameter types
        if not isinstance(model_name, str):
            result = {
                "status": "error",
                "message": f"Parameter 'model' must be a string, got {type(model_name).__name__}"
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        if not isinstance(force_cpu, bool):
            # Try to convert string "true"/"false" to boolean
            if isinstance(force_cpu, str):
                force_cpu = force_cpu.lower() in ("true", "1", "yes")
            else:
                result = {
                    "status": "error",
                    "message": f"Parameter 'force_cpu' must be a boolean, got {type(force_cpu).__name__}"
                }
                print(json.dumps(result), flush=True)
                sys.exit(1)
        
        # Read input image
        image, error = read_image_file(input_file)
        if error:
            result = {
                "status": "error",
                "message": error
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        # Store image info for later use
        image_size = image.GetSize()
        image_spacing = image.GetSpacing()
        
        # Apply lungmask - pass the SimpleITK Image object directly
        # lungmask.apply() accepts SimpleITK.Image or numpy.ndarray
        mask, error = apply_lungmask(image, model_name=model_name, force_cpu=force_cpu)
        if error:
            result = {
                "status": "error",
                "message": error
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        # Calculate statistics
        stats, error = get_mask_statistics(mask)
        if error:
            # Non-fatal error, continue without stats
            stats = {}
        
        # Load metadata
        metadata, error = load_json_file(metadata_file, "metadata file")
        if error:
            # Non-fatal error, use empty metadata
            metadata = {}
        
        # Convert mask directly to base64 using temporary file that's auto-deleted
        # SimpleITK requires a file path, so we use NamedTemporaryFile which auto-deletes
        mask_base64 = None
        mask_size_bytes = 0
        try:
            import base64
            import tempfile
            
            # Use NamedTemporaryFile which auto-deletes when closed
            # This avoids leaving files on disk
            with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=True) as tmp_file:
                tmp_path = tmp_file.name
                
                # Write mask to temporary file
                sitk.WriteImage(mask, tmp_path)
                
                # Read the file into memory
                with open(tmp_path, 'rb') as f:
                    mask_bytes = f.read()
                
                mask_size_bytes = len(mask_bytes)
                
                # Check size limit (50MB base64 ≈ 37MB raw)
                max_size_bytes = 50 * 1024 * 1024  # 50MB
                if mask_size_bytes * 1.4 < max_size_bytes:
                    mask_base64 = base64.b64encode(mask_bytes).decode('utf-8')
                else:
                    # File too large, skip base64 encoding
                    mask_base64 = None
                    print(f"Warning: Mask too large for base64 encoding ({mask_size_bytes / (1024*1024):.2f} MB)", 
                          file=sys.stderr)
                # File is automatically deleted when exiting the 'with' block
        except Exception as e:
            # Non-fatal error, continue without base64 encoding
            print(f"Warning: Could not encode mask as base64: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            mask_base64 = None
        
        # Get mask metadata for radiomics (spacing, origin, direction)
        mask_spacing = list(mask.GetSpacing())
        mask_origin = list(mask.GetOrigin())
        mask_direction = list(mask.GetDirection())
        mask_size = list(mask.GetSize())
        
        # Create success result with all necessary information for radiomics
        result = {
            "status": "success",
            "message": f"Successfully generated lung mask using model '{model_name}'",
            "data": {
                "mask_base64": mask_base64,  # Mask image encoded in base64 (NIfTI format)
                "mask_size_bytes": mask_size_bytes,  # Size of mask in bytes
                "mask_format": "nii.gz",  # Format of the mask
                "statistics": stats,  # Basic statistics
                # Mask metadata for radiomics
                "mask_metadata": {
                    "size": mask_size,  # [width, height, depth] in voxels
                    "spacing_mm": mask_spacing,  # [x, y, z] spacing in mm (critical for radiomics)
                    "origin_mm": mask_origin,  # [x, y, z] origin in mm
                    "direction": mask_direction  # Direction cosine matrix (9 elements)
                }
            },
            "metadata": {
                "method": "lungmask",
                "model": model_name,
                "force_cpu": force_cpu,
                "input_file": input_file,
                # Input image metadata (needed for radiomics to ensure alignment)
                "input_image_size": list(image_size),
                "input_image_spacing": list(image_spacing),
                "input_image_origin": list(image.GetOrigin()),
                "input_image_direction": list(image.GetDirection()),
                "original_metadata": metadata
            },
            "parameters_applied": params
        }
        
        # Output as JSON only (suppress any other output)
        # Clear any buffered stdout first
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Output JSON to stdout - this should be the only output
        json_output = json.dumps(result, indent=None, separators=(',', ':'))
        print(json_output, flush=True)
        
        return True
        
    except KeyboardInterrupt:
        result = {
            "status": "error",
            "message": "Process interrupted by user"
        }
        print(json.dumps(result), flush=True)
        sys.exit(1)
        
    except Exception as e:
        # Catch-all for any unexpected errors
        error_traceback = traceback.format_exc()
        result = {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__,
            "traceback": error_traceback
        }
        print(json.dumps(result), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

