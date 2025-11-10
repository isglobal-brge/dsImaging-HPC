#!/usr/bin/env python3
"""
PyRadiomics Feature Extraction Method

This script extracts radiomic features from medical images using PyRadiomics.
It requires both the original image and a binary mask defining the region of interest (ROI).

INPUT REQUIREMENTS:
- Input image: Medical imaging file (NIfTI, DICOM, NRRD, MHA, MHD, etc.)
- Mask: Binary mask file defining the ROI, OR mask_base64 parameter containing base64-encoded mask
- Both image and mask must have matching dimensions and spacing

OUTPUT:
- Returns a JSON response containing:
  - status: "success" or "error"
  - data.features: Dictionary of extracted radiomic features organized by feature class
  - data.feature_classes: List of feature classes extracted
  - data.feature_count: Total number of features extracted
  - metadata: Processing metadata including image info, mask info, and extraction settings
"""

import sys
import os
import json
import traceback
import base64
import tempfile
from pathlib import Path

import SimpleITK as sitk
from radiomics import featureextractor


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
    """Read an image file using SimpleITK."""
    try:
        exists, error = validate_file_exists(image_path, "Image file")
        if not exists:
            return None, error
        
        try:
            image = sitk.ReadImage(image_path)
        except Exception as e:
            return None, f"Failed to read image file '{image_path}': {str(e)}"
        
        if image.GetSize()[0] == 0 or image.GetSize()[1] == 0:
            return None, f"Image appears to be empty (size: {image.GetSize()})"
        
        return image, None
        
    except Exception as e:
        return None, f"Unexpected error reading image: {str(e)}"


def decode_mask_from_base64(mask_base64):
    """Decode mask from base64 string and save to temporary file."""
    try:
        # Decode base64
        mask_bytes = base64.b64decode(mask_base64)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(mask_bytes)
        
        return tmp_path, None
    except Exception as e:
        return None, f"Failed to decode mask from base64: {str(e)}"


def extract_radiomics_features(image_path, mask_path, settings=None):
    """Extract radiomic features from image using mask."""
    try:
        # Create feature extractor with settings
        extractor = featureextractor.RadiomicsFeatureExtractor()
        
        # Apply custom settings if provided
        if settings:
            extractor.settings.update(settings)
        
        # Extract features
        features = extractor.execute(image_path, mask_path)
        
        # Organize features by class
        feature_classes = {}
        feature_count = 0
        
        for feature_name, feature_value in features.items():
            # Skip diagnostic features (start with 'diagnostics')
            if feature_name.startswith('diagnostics'):
                continue
            
            # Extract feature class from name (e.g., 'original_firstorder_Mean' -> 'firstorder')
            parts = feature_name.split('_')
            if len(parts) >= 2:
                # Handle cases like 'original_firstorder_Mean' or 'wavelet-LHH_firstorder_Mean'
                if parts[0] == 'original':
                    class_name = parts[1]
                elif 'wavelet' in parts[0]:
                    class_name = 'wavelet_' + parts[1]
                else:
                    class_name = parts[0]
            else:
                class_name = 'other'
            
            if class_name not in feature_classes:
                feature_classes[class_name] = {}
            
            feature_classes[class_name][feature_name] = float(feature_value) if isinstance(feature_value, (int, float)) else str(feature_value)
            feature_count += 1
        
        return {
            'features': feature_classes,
            'feature_classes': list(feature_classes.keys()),
            'feature_count': feature_count,
            'all_features': {k: (float(v) if isinstance(v, (int, float)) else str(v)) for k, v in features.items() if not k.startswith('diagnostics')}
        }, None
        
    except Exception as e:
        return None, f"Error extracting radiomic features: {str(e)}"


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
        
        # Load metadata
        metadata, error = load_json_file(metadata_file, "metadata file")
        if error:
            result = {
                "status": "error",
                "message": error
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        # Extract parameters with defaults
        mask_base64 = params.get("mask_base64")
        feature_classes_str = params.get("feature_classes", "firstorder,shape,glcm,glrlm,glszm,gldm,ngtdm")
        bin_width = params.get("bin_width", 25)
        normalize = params.get("normalize", False)
        normalize_scale = params.get("normalize_scale", 100)
        
        # Parse feature classes
        feature_classes_list = [fc.strip() for fc in feature_classes_str.split(',')]
        
        # Determine mask path
        mask_path = None
        mask_temp_file = None
        
        # Check if mask is provided as base64
        if mask_base64 and mask_base64 != "null" and mask_base64 != "":
            # Decode mask from base64
            mask_path, error = decode_mask_from_base64(mask_base64)
            if error:
                result = {
                    "status": "error",
                    "message": error
                }
                print(json.dumps(result), flush=True)
                sys.exit(1)
            mask_temp_file = mask_path  # Mark for cleanup
        else:
            # Try to get mask from file_inputs (metadata)
            if metadata and 'files' in metadata:
                files = metadata['files']
                # Check for 'mask' input
                if 'mask' in files:
                    mask_path = files['mask']
                # Check for 'mask' in array format
                elif 'mask' in files and isinstance(files['mask'], list) and len(files['mask']) > 0:
                    mask_path = files['mask'][0]
            
            if not mask_path or not os.path.exists(mask_path):
                result = {
                    "status": "error",
                    "message": "Mask not provided. Provide either 'mask_base64' parameter or 'mask' file input."
                }
                print(json.dumps(result), flush=True)
                sys.exit(1)
            
            # Check if the mask file contains base64-encoded content (from $ref extraction)
            # When $ref extracts a base64 string from JSON, it's saved as a text file
            try:
                with open(mask_path, 'rb') as f:
                    first_bytes = f.read(100)
                    # Check if file starts with base64-like content (text, not binary NIfTI)
                    # NIfTI files start with specific magic numbers, base64 strings don't
                    if len(first_bytes) > 0 and first_bytes[0] not in [0x00, 0x1E, 0x5C]:  # Common NIfTI magic numbers
                        # Try to read as text and decode base64
                        with open(mask_path, 'r', encoding='utf-8') as text_file:
                            content = text_file.read().strip()
                            # Check if it looks like base64 (alphanumeric, +, /, =)
                            if all(c.isalnum() or c in '+/=' for c in content) and len(content) > 100:
                                # Likely base64, decode it
                                try:
                                    mask_bytes = base64.b64decode(content)
                                    # Create temporary file with decoded content
                                    with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as tmp_file:
                                        tmp_path = tmp_file.name
                                        tmp_file.write(mask_bytes)
                                    mask_path = tmp_path
                                    mask_temp_file = tmp_path
                                except Exception as e:
                                    # Not valid base64, continue with original file
                                    pass
            except Exception:
                # If reading fails, continue with original file path
                pass
        
        # Validate mask file exists
        exists, error = validate_file_exists(mask_path, "Mask file")
        if not exists:
            result = {
                "status": "error",
                "message": error
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        # Read images to validate
        image, error = read_image_file(input_file)
        if error:
            result = {
                "status": "error",
                "message": error
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        mask_image, error = read_image_file(mask_path)
        if error:
            result = {
                "status": "error",
                "message": error
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        # Validate dimensions match
        if image.GetSize() != mask_image.GetSize():
            result = {
                "status": "error",
                "message": f"Image size {image.GetSize()} does not match mask size {mask_image.GetSize()}"
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        # Configure PyRadiomics settings
        settings = {
            'binWidth': bin_width,
            'normalize': normalize,
            'normalizeScale': normalize_scale if normalize else None,
        }
        
        # Configure feature classes to extract
        # PyRadiomics uses 'enable' flags for each feature class
        settings['enable'] = {}
        for fc in feature_classes_list:
            fc_lower = fc.lower()
            if fc_lower in ['firstorder', 'shape', 'glcm', 'glrlm', 'glszm', 'gldm', 'ngtdm']:
                settings['enable'][fc_lower] = True
            elif fc_lower.startswith('wavelet'):
                settings['enable']['wavelet'] = True
        
        # Extract radiomic features
        features_result, error = extract_radiomics_features(input_file, mask_path, settings)
        if error:
            result = {
                "status": "error",
                "message": error
            }
            print(json.dumps(result), flush=True)
            sys.exit(1)
        
        # Clean up temporary mask file if created from base64
        if mask_temp_file and os.path.exists(mask_temp_file):
            try:
                os.unlink(mask_temp_file)
            except:
                pass
        
        # Create success result
        result = {
            "status": "success",
            "message": f"Successfully extracted {features_result['feature_count']} radiomic features",
            "data": {
                "features": features_result['features'],
                "feature_classes": features_result['feature_classes'],
                "feature_count": features_result['feature_count'],
                "all_features": features_result['all_features']
            },
            "metadata": {
                "method": "pyradiomics",
                "image_size": list(image.GetSize()),
                "image_spacing": list(image.GetSpacing()),
                "mask_size": list(mask_image.GetSize()),
                "mask_spacing": list(mask_image.GetSpacing()),
                "settings": {
                    "bin_width": bin_width,
                    "normalize": normalize,
                    "normalize_scale": normalize_scale if normalize else None,
                    "feature_classes": feature_classes_list
                },
                "original_metadata": metadata
            },
            "parameters_applied": params
        }
        
        # Output as JSON
        sys.stdout.flush()
        sys.stderr.flush()
        
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

