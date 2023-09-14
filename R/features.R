#' Calculate Radiomic Features
#'
#' This function calculates radiomic features based on a given original image,
#' its mask, and a set of parameters.
#'
#' @param paths
#' @param config A character string specifying the configuration to use. Available options: "default", "config2", ...
#'
#' @return A list of computed radiomic features.
#' @examples
#' \dontrun{
#' features <- calculate_radiomic_features_R("/path/to/original/image", "/path/to/mask", "/path/to/parameters")
#' print(features)
#' }
#' @export
calculate_radiomic_features_R <- function(image, mask, config = "default") {
  print(image)
  print(mask)
  results <- reticulate::py$calculate_radiomic_features(image, mask, config)
  return(results)
}
