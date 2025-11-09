#!/usr/bin/env python3
"""
Lungmask segmentation method.

This script applies lung segmentation to CT images using the lungmask library.
It reads an input image file, applies the segmentation model, and returns the mask.

Usage:
    python3 main.py <input_file> <metadata_file> <params_file>
"""

import sys
import os
import json
import traceback
import tempfile
import shutil
from pathlib import Path

import SimpleITK as sitk
import numpy as np
from lungmask import mask as lungmask_mask


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
    """Apply lungmask segmentation to an image."""
    try:
        # Validate model name
        valid_models = ["R231", "LTRCLobes", "R231CovidWeb"]
        if model_name not in valid_models:
            return None, f"Invalid model name '{model_name}'. Valid options: {', '.join(valid_models)}"
        
        # Apply lungmask
        try:
            if force_cpu:
                # Force CPU by setting CUDA_VISIBLE_DEVICES
                import os as os_module
                original_cuda = os_module.environ.get('CUDA_VISIBLE_DEVICES')
                os_module.environ['CUDA_VISIBLE_DEVICES'] = ''
                try:
                    mask = lungmask_mask.apply(image, model=model_name)
                finally:
                    if original_cuda is not None:
                        os_module.environ['CUDA_VISIBLE_DEVICES'] = original_cuda
                    else:
                        os_module.environ.pop('CUDA_VISIBLE_DEVICES', None)
            else:
                mask = lungmask_mask.apply(image, model=model_name)
        except RuntimeError as e:
            if "CUDA" in str(e) or "GPU" in str(e):
                return None, f"GPU error: {str(e)}. Try setting force_cpu=true parameter."
            return None, f"Runtime error during lungmask application: {str(e)}"
        except Exception as e:
            return None, f"Error applying lungmask: {str(e)}"
        
        # Validate mask was created
        if mask is None:
            return None, "Lungmask returned None (no mask generated)"
        
        # Validate mask dimensions match image
        if mask.GetSize() != image.GetSize():
            return None, f"Mask size {mask.GetSize()} does not match image size {image.GetSize()}"
        
        return mask, None
        
    except Exception as e:
        return None, f"Unexpected error applying lungmask: {str(e)}"


def save_mask(mask, output_dir, original_image_path):
    """Save the mask to a file."""
    try:
        # Create output filename based on input filename
        input_basename = Path(original_image_path).stem
        # Remove .nii if present (for .nii.gz files)
        if input_basename.endswith('.nii'):
            input_basename = input_basename[:-4]
        
        output_path = os.path.join(output_dir, f"{input_basename}_lungmask.nii.gz")
        
        # Write the mask
        try:
            sitk.WriteImage(mask, output_path)
        except Exception as e:
            return None, f"Failed to write mask to file: {str(e)}"
        
        # Validate file was created
        if not os.path.exists(output_path):
            return None, "Mask file was not created successfully"
        
        return output_path, None
        
    except Exception as e:
        return None, f"Unexpected error saving mask: {str(e)}"


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
        
        # Apply lungmask
        mask, error = apply_lungmask(image, model_name=model_name, force_cpu=force_cpu)
        if error:
            result = {
                "status": "error",
                "message": error
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        # Create temporary directory for output
        output_dir = tempfile.mkdtemp(prefix="lungmask_")
        try:
            # Save mask
            mask_path, error = save_mask(mask, output_dir, input_file)
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
            
            # Create success result
            result = {
                "status": "success",
                "message": f"Successfully generated lung mask using model '{model_name}'",
                "data": {
                    "mask_file": mask_path,
                    "mask_size_bytes": os.path.getsize(mask_path),
                    "statistics": stats
                },
                "metadata": {
                    "method": "lungmask",
                    "model": model_name,
                    "force_cpu": force_cpu,
                    "input_file": input_file,
                    "input_image_size": list(image.GetSize()),
                    "input_image_spacing": list(image.GetSpacing()),
                    "original_metadata": metadata
                },
                "parameters_applied": params
            }
            
            # Output as JSON
            print(json.dumps(result, indent=None, separators=(',', ':')), flush=True)
            
            return True
            
        finally:
            pass
        
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

