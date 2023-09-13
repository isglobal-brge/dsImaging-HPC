.onAttach <- function(libname, pkgname) {
  resourcer::registerResourceResolver(DicomImageResolver$new())
  #reticulate::use_condaenv(condaenv = "rock-python")
  #script_path <- system.file("python", "functions.py", package = "dsImaging")
  #reticulate::source_python(script_path, envir = parent.frame(), convert = TRUE)
}

.onDetach <- function(libpath) {
  resourcer::unregisterResourceResolver("DicomImageResolver")
}
