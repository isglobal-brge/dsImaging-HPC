ModelWeightsClient <- R6::R6Class(
  "ModelWeightsClient",
  inherit = FileResourceClient,
  public = list(
    initialize = function(resource) {
      super$initialize(resource)
    },
    getValue = function(...) {
      path <- super$downloadFile()
      class(path) <- "ModelWeights"
      return(path)
    }
  ),
  private = list()
)
