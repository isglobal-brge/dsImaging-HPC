#' Source Python Functions from `dsImaging` Package
#'
#' This function sources the `functions.py` script from the `dsImaging` package using `reticulate`.
#'
#' @return None. This function only sources Python functions for use in the current R session.
#' @export
#' @examples
#' source_dsImaging_python_functions()
source_dsImaging_python_functions <- function(path = "/var/lib/rock/python/bin/conda", condaenv = "rock-python") {
  reticulate::use_condaenv(conda = path, condaenv = condaenv)
  script_path <- system.file("python", "functions.py", package = "dsImaging")
  reticulate::source_python(script_path, envir = parent.frame(), convert = TRUE)
}
