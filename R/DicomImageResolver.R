DicomImageResolver <- R6::R6Class(
  "DicomImageResolver",
  inherit = ResourceResolver,
  public = list(
    isFor = function(x) {
      if (super$isFor(x)) {
        !is.null(findFileResourceGetter(x)) && tolower(x$format) %in% c("dicomimage")
      } else {
        FALSE
      }
    },
    newClient = function(x) {
      if (self$isFor(x)) {
        DicomImageClient$new(x)
      } else {
        stop("Resource is not an Dicom Image data file")
      }
    }
  )
)
