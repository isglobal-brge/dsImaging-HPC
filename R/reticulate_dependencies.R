#' Install Reticulate Dependencies
#'
#' This function automates the setup of a conda environment specific for reticulate use, installing a predefined set of Python packages necessary for a project. It creates a new conda environment or uses an existing one, installs Miniconda if necessary, and then installs several packages using both conda and pip.
#'
#' @param path The base path where Miniconda should be installed or is already installed. Default is `"/var/lib/rock/python"`.
#' @param condaenv The name of the conda environment to either create or use. Default is `"rock-python"`.
#' 
#' @details The function begins by ensuring that Miniconda is installed at the specified `path`. Then, it creates a new conda environment named `condaenv` (or uses the existing one) and installs a series of Python packages essential for various data processing tasks. The packages include numpy, lungmask, SimpleITK, pynrrd, matplotlib, opencv-python, dicom2nifti, pandas, and pyradiomics. These packages are installed using pip within the conda environment to ensure compatibility and ease of installation.
#'
#' @examples
#' install_reticulate_dependencies()
#' install_reticulate_dependencies("/custom/path/to/miniconda", "my-conda-env")
#'
#' @return Invisible NULL. The function is called for its side effects (setting up a conda environment and installing packages) and does not return a value.
#'
#' @export

install_reticulate_dependencies <- function(path = "/var/lib/rock/python", condaenv = "rock-python") {
  path_conda <- paste0(path, "/bin/conda")
  reticulate::install_miniconda(path = path)
  reticulate::conda_create(
    envname = condaenv,
    packages = c("python=3.8.13", "numpy"), conda = path_conda
  )
  reticulate::conda_install(
    envname = condaenv,
    packages = "lungmask", pip = TRUE, conda = path_conda
  )
  reticulate::conda_install(
    envname = condaenv,
      packages = "SimpleITK", pip = TRUE, conda = path_conda
  )
  reticulate::conda_install(
    envname = condaenv,
    packages = "pynrrd", pip = TRUE, conda = path_conda
  )
  reticulate::conda_install(
    envname = condaenv,
    packages = "matplotlib", pip = TRUE, conda = path_conda
  )
  reticulate::conda_install(
    envname = condaenv,
    packages = "opencv-python", pip = TRUE, conda = path_conda
  )
  reticulate::conda_install(
    envname = condaenv,
    packages = "dicom2nifti", pip = TRUE, conda = path_conda
  )
  reticulate::conda_install(
    envname = condaenv,
    packages = "pandas", pip = TRUE, conda = path_conda
  )
  reticulate::conda_install(
    envname = condaenv,
    packages = "pyradiomics", pip = TRUE, conda = path_conda
  )
}