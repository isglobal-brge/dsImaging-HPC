#' Source Python Functions from `dsImaging` Package
#'
#' This function sources the `functions.py` script from the `dsImaging` package using `reticulate`.
#'
#' @return None. This function only sources Python functions for use in the current R session.
#' @export
#' @examples
#' source_dsImaging_python_functions()
source_dsImaging_python_functions <- function() {
  # Specify the conda environment to use
  message("a")
  a <- reticulate::conda_list("/root/.local/share/r-miniconda")
  a
  message(a)

  # reticulate::use_condaenv(condaenv = "rock-python")

  # Locate the Python script within the dsImaging package
  script_path <- system.file("python", "functions.py", package = "dsImaging")
  script_path

  # Source the Python script
  reticulate::source_python(script_path, envir = parent.frame(), convert = TRUE)
}
