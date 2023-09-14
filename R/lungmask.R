#' Process a Single Scan
#'
#' This function acts as a wrapper for a Python function that processes a single scan.
#' It decompresses the tarball, creates and saves masks, recompresses the mask, 
#' and cleans up intermediate files.
#'
#' @param scan_path Character string specifying the path to the .tar.gz scan file.
#'
#' @return NULL. The function performs processing on the provided scan file but doesn't return any R object.
#' @export
#'
#' @examples
#' \dontrun{
#' scan_path <- "/path/to/your/single/image.tar.gz"
#' process_single_scan_R(scan_path)
#' }
process_single_scan_R <- function(scan_path) {
  # Call the Python function
  reticulate::py$lugmask_nifti(scan_path)
}
