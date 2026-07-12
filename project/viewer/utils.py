# viewer/utils.py
import os
import SimpleITK as sitk
import numpy as np
import logging
from PIL import Image

logger = logging.getLogger(__name__)

def convert_dicom_to_png(dicom_files, output_dir):
    """
    Convert DICOM files to PNG images using SimpleITK only
    """
    try:
        # Check if we have DICOM files
        if not dicom_files:
            raise ValueError("No DICOM files provided")
        
        # Try to read as series first
        try:
            series_reader = sitk.ImageSeriesReader()
            series_reader.SetFileNames(dicom_files)
            image = series_reader.Execute()
            
        except Exception as series_error:
            logger.warning(f"Series reading failed: {series_error}. Trying single file approach.")
            
            # Fallback: try reading individual files
            images = []
            for file_path in dicom_files:
                try:
                    img = sitk.ReadImage(file_path)
                    images.append(img)
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
            
            if not images:
                raise RuntimeError("Could not read any DICOM files")
            
            if len(images) == 1:
                # Single slice
                image = images[0]
            else:
                # Try to create 3D volume from individual slices
                try:
                    image = sitk.JoinSeries(images)
                except:
                    # If joining fails, just use the first image
                    image = images[0]
                    logger.warning("Could not join series, using first slice only")

        # Convert to numpy array
        array = sitk.GetArrayFromImage(image)
        
        # Handle different array shapes
        if array.ndim == 3:  # Volume (slices, height, width)
            num_slices = array.shape[0]
        elif array.ndim == 2:  # Single slice
            num_slices = 1
            array = array[np.newaxis, :, :]
        else:
            raise ValueError(f"Unexpected array shape: {array.shape}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        png_paths = []
        
        # Normalize and save each slice
        for i in range(num_slices):
            slice_data = array[i]
            
            # Normalize to 0-255
            slice_data = slice_data.astype(np.float32)
            slice_min = np.min(slice_data)
            slice_max = np.max(slice_data)
            
            slice_data = slice_data - slice_min
            if slice_max > slice_min:
                slice_data = slice_data / (slice_max - slice_min) * 255
            
            slice_data = slice_data.astype(np.uint8)
            
            # Create PIL image and save
            img = Image.fromarray(slice_data)
            png_path = os.path.join(output_dir, f"slice_{i:04d}.png")
            img.save(png_path)
            png_paths.append(png_path)
        
        return png_paths
        
    except Exception as e:
        logger.error(f"DICOM conversion error: {e}")
        raise RuntimeError(f"Erreur de conversion DICOM: {str(e)}")

def is_dicom_file(file_path):
    """
    Check if a file is a valid DICOM file using SimpleITK only
    """
    # Check file extension first
    if not file_path.lower().endswith(('.dcm', '.dicom')):
        return False
    
    # Try to read with SimpleITK
    try:
        sitk.ReadImage(file_path)
        return True
    except:
        return False

def validate_dicom_files(file_paths):
    """
    Validate that all files are proper DICOM files
    """
    valid_files = []
    invalid_files = []
    
    for file_path in file_paths:
        if is_dicom_file(file_path):
            valid_files.append(file_path)
        else:
            invalid_files.append(os.path.basename(file_path))
    
    return valid_files, invalid_files