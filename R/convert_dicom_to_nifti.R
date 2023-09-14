#' Convert DICOM to NIFTI
#'
#' This function converts a DICOM image and its mask to the NIFTI format.
#'
#' @param paths Output of `process_single_scan_R`.
#'
#' @export
convert_dicom_to_nifti_R <- function(path) {
  # Extract the paths for the image and mask

  # Check if the paths are valid (not NULL)
  if (is.null(path)) {
    stop("Error in processing the scan or mask.")
  }

  # Call the Python function to convert the DICOMs to NIFTI
  res <- reticulate::py$convert_dicom_to_nifti(path)
  return(res[[1]])
}
