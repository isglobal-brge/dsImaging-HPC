#!/usr/bin/env Rscript
# Test script for meta-job chain: lungmask -> pyradiomics
# This uses a meta-job (chained jobs) approach instead of a pipeline

library(dsHPC)

# Create API config
config <- create_api_config(
  "http://localhost",
  8001,
  "lXCXTxsK6JK8aeGSAZkAI8FGLYug8H9u",
  "X-API-Key",
  ""
)

cat("=== Testing Lungmask -> PyRadiomics Meta-Job Chain ===\n\n")

# Step 1: Upload original image
cat("Step 1: Uploading original CT image...\n")
test_image_path <- "/Users/david/Documents/GitHub/dsMinIO-vault/data/collections/images/study_0001.nii.gz"

if (!file.exists(test_image_path)) {
  stop(sprintf("Original CT image file not found: %s", test_image_path))
}

file_hash <- upload_file(config, test_image_path, "study_0001.nii.gz")
cat(sprintf("File uploaded successfully. Hash: %s...\n", substr(file_hash, 1, 16)))
cat("\n")

# Step 2: Create meta-job with chained methods
cat("Step 2: Creating meta-job chain: lungmask -> pyradiomics...\n")

# The meta-job chain processes methods sequentially
# Each step can reference the previous step's output using $ref:prev
chain <- list(
  list(
    method_name = "lungmask",
    parameters = list(
      model = "R231",
      force_cpu = TRUE
    )
    # No file_inputs needed for first step - uses the meta-job's file_hash
  ),
  list(
    method_name = "pyradiomics",
    parameters = list(
      feature_classes = list("firstorder", "shape"),  # Let's see if this gets coerced
      bin_width = 25,
      normalize = FALSE
    ),
    file_inputs = list(
      image = file_hash,  # Original image (direct hash)
      mask = "$ref:prev/data/mask_base64"  # Extract mask from previous step's output
    )
  )
)

cat("Chain structure:\n")
cat("  Step 1 (lungmask): Processes original image -> generates mask\n")
cat("  Step 2 (pyradiomics): Uses original image + mask from step 1 -> extracts features\n")
cat("\n")

# Submit meta-job
cat("Step 3: Submitting meta-job...\n")

submission <- submit_meta_job_by_hash(
  config,
  file_hash = file_hash,
  method_chain = chain
)

cat(sprintf("Meta-job submitted. Hash: %s\n", submission$meta_job_hash))
cat("Waiting for results (this may take several minutes)...\n\n")

result <- wait_for_meta_job(
  config,
  meta_job_hash = submission$meta_job_hash,
  max_wait = 600,  # 10 minutes timeout
  interval = 5
)

cat("\n=== Meta-Job Results ===\n")

if (!is.null(result$status) && result$status == "CD") {
  cat("Meta-job completed successfully!\n\n")

  # Get the final output
  final_result <- get_job_output_by_hash(config, result$final_job_hash)
  print(final_result)
} else {
  cat(sprintf("Meta-job status: %s\n", result$status))
  print(result)
}

cat("\n=== Test Complete ===\n")
