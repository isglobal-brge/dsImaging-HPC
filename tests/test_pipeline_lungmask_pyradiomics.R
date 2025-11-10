#!/usr/bin/env Rscript
# Test script for lungmask + pyradiomics pipeline
# Uses a pipeline to:
# 1. Apply lungmask to generate mask (node 1)
# 2. Apply pyradiomics using original image + mask from node 1 (node 2)
#
# Pipeline structure:
# - Node 1: lungmask meta-job with original image (input_file_hash)
# - Node 2: pyradiomics meta-job with:
#   * image = original file_hash (direct)
#   * mask = $ref:node1/data/mask_base64 (reference to node1 output, system extracts and creates file)
# 
# The $ref system works in file_inputs, not in parameters. The system will:
# 1. Extract the value at path "data/mask_base64" from node1's output JSON
# 2. Decode the base64 string
# 3. Create a temporary file with the decoded content
# 4. Use that file path as the "mask" input for pyradiomics
#
# NOTE: There appears to be a backend bug when processing input_file_hash in pipeline nodes
# (error: 'NoneType' object has no attribute 'get'). The script structure is correct according
# to the documentation, but the backend needs to be fixed. As an alternative, you can use
# test_pyradiomics.R which uses a meta-job approach and works correctly.

library(dsHPC)

# Create API config
config <- create_api_config(
  "http://localhost", 
  8001, 
  "YOUR_API_KEY",
  "X-API-Key",
  ""
)

cat("=== Testing Lungmask + PyRadiomics Pipeline ===\n\n")

# Step 1: Upload original image
cat("Step 1: Uploading original CT image...\n")
test_image_path <- "study_0001.nii.gz"

if (!file.exists(test_image_path)) {
  cat(sprintf("✗ File '%s' does not exist in current directory\n", test_image_path))
  stop("Original CT image file not found")
}

file_hash <- upload_file(config, test_image_path, "study_0002.nii.gz")
cat(sprintf("✓ File uploaded successfully. Hash: %s...\n", substr(file_hash, 1, 16)))
cat("\n")

# Step 2: Create pipeline nodes
cat("Step 2: Creating pipeline nodes...\n")

# Node 1: Apply lungmask to generate mask
# Uses the original image as input
# Note: Even though lungmask uses single-file input, we can pass it via file_inputs in the chain
# The system will handle it correctly for methods that support single_file
node1 <- create_pipeline_node(
  chain = list(
    list(
      method_name = "lungmask",
      parameters = list(
        model = "R231",
        force_cpu = TRUE
      ),
      file_inputs = NULL  # lungmask uses single file, but we'll use input_file_hash
    )
  ),
  dependencies = character(0),  # Root node (no dependencies)
  input_file_hash = file_hash  # Original image for lungmask
)

cat("✓ Node 1 (lungmask) created\n")

# Node 2: Apply pyradiomics using original image + mask from node 1
# This node needs:
# - Original image (as file_inputs)
# - Mask from node 1 (as file_inputs using $ref - system will extract base64 and create file)
node2 <- create_pipeline_node(
  chain = list(
    list(
      method_name = "pyradiomics",
      parameters = list(
        feature_classes = "firstorder,shape,glcm,glrlm,glszm,gldm,ngtdm",
        bin_width = 25,
        normalize = FALSE
      ),
      file_inputs = list(
        image = file_hash,  # Original image
        mask = "$ref:node1/data/mask_base64"  # Mask from node 1 - system extracts base64 and creates file
      )
    )
  ),
  dependencies = c("node1")  # Depends on node1 completing first
)

cat("✓ Node 2 (pyradiomics) created\n")
cat("\n")

# Step 3: Create and submit pipeline
cat("Step 3: Creating and submitting pipeline...\n")
pipeline <- list(
  nodes = list(
    node1 = node1,
    node2 = node2
  )
)

cat("Pipeline structure:\n")
cat("  Node 1 (lungmask): Processes original image → generates mask\n")
cat("  Node 2 (pyradiomics): Uses original image + mask from node 1 → extracts features\n")
cat("\n")

# Submit and wait for pipeline
cat("Submitting pipeline and waiting for results...\n")
cat("(This may take several minutes)\n\n")

result <- execute_pipeline(
  config,
  pipeline_definition = pipeline,
  timeout = 600,  # 10 minutes timeout
  verbose = TRUE
)

cat("\n=== Pipeline Results ===\n")

if (!is.null(result$final_output) && result$final_output$status == "success") {
  cat("✓ Pipeline completed successfully!\n\n")
  
  # Extract results from final node (pyradiomics)
  radiomics_result <- result$final_output
  
  cat("=== PyRadiomics Feature Summary ===\n")
  if (!is.null(radiomics_result$data)) {
    if (!is.null(radiomics_result$data$feature_count)) {
      cat(sprintf("Total features extracted: %d\n", radiomics_result$data$feature_count))
    }
    if (!is.null(radiomics_result$data$feature_classes)) {
      cat(sprintf("Feature classes: %s\n", paste(radiomics_result$data$feature_classes, collapse=", ")))
    }
    
    cat("\n=== Feature Classes ===\n")
    if (!is.null(radiomics_result$data$features)) {
      features <- radiomics_result$data$features
      for (class_name in names(features)) {
        class_features <- features[[class_name]]
        cat(sprintf("\n%s (%d features):\n", class_name, length(class_features)))
        # Show first 3 features as sample
        sample_features <- head(class_features, 3)
        for (feature_name in names(sample_features)) {
          cat(sprintf("  %s: %.6f\n", feature_name, as.numeric(sample_features[[feature_name]])))
        }
        if (length(class_features) > 3) {
          cat(sprintf("  ... and %d more features\n", length(class_features) - 3))
        }
      }
    }
  }
  
  # Also show intermediate results (lungmask output)
  if (!is.null(result$node_outputs) && !is.null(result$node_outputs$node1)) {
    cat("\n=== Intermediate Results (Lungmask) ===\n")
    lungmask_result <- result$node_outputs$node1
    if (lungmask_result$status == "success") {
      cat("✓ Lungmask completed successfully\n")
      if (!is.null(lungmask_result$data$mask_size_bytes)) {
        cat(sprintf("Mask size: %d bytes\n", lungmask_result$data$mask_size_bytes))
      }
      if (!is.null(lungmask_result$data$mask_format)) {
        cat(sprintf("Mask format: %s\n", lungmask_result$data$mask_format))
      }
    }
  }
  
  cat("\n=== Pipeline Summary ===\n")
  cat("✓ Node 1 (lungmask): Generated lung mask\n")
  cat("✓ Node 2 (pyradiomics): Extracted radiomic features\n")
  cat("✓ Pipeline completed successfully!\n")
  
} else {
  cat("✗ Pipeline failed!\n")
  cat("Error details:\n")
  print(result)
  
  # Try to show node statuses
  if (!is.null(result$node_outputs)) {
    cat("\n=== Node Statuses ===\n")
    for (node_name in names(result$node_outputs)) {
      node_output <- result$node_outputs[[node_name]]
      cat(sprintf("Node %s: %s\n", node_name, node_output$status))
      if (node_output$status != "success") {
        cat(sprintf("  Error: %s\n", node_output$message))
      }
    }
  }
}

cat("\n=== Test Complete ===\n")

