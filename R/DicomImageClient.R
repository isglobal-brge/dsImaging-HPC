DicomImageClient <- R6::R6Class(
  "DicomImageClient",
  inherit = FileResourceClient,
  public = list(
    initialize = function(resource) {
      super$initialize(resource)
    },
    getValue = function(...) {
      path <- super$downloadFile()
      class(path) <- "DicomPATH"
      return(path)
    }
  ),
  private = list()
)
