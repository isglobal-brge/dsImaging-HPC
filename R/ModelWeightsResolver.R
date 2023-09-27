ModelWeightsResolver <- R6::R6Class(
  "ModelWeightsResolver",
  inherit = ResourceResolver,
  public = list(
    isFor = function(x) {
      if (super$isFor(x)) {
        !is.null(findFileResourceGetter(x)) && tolower(x$format) %in% c("modelweights")
      } else {
        FALSE
      }
    },
    newClient = function(x) {
      if (self$isFor(x)) {
        ModelWeightsClient$new(x)
      } else {
        stop("Resource is not an Model Weights data file")
      }
    }
  )
)
