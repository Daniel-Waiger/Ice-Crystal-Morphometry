// Fiji Macro for Ice Crystal Morphometry

macro "Ice Crystal Morphometry" {
    // Initialize the console for logging progress and outputs
    run("Close Fiji Console");
	run("Console");
	close("Log");
    IJ.log("Starting ice crystal detection and morphometry.");

    // Create a dialog for user inputs
    Dialog.create("Ice Crystal Morphometry");

    Dialog.addDirectory("Choose a directory containing the image files", "");
    Dialog.addDirectory("Choose a directory to save your results", "");
    Dialog.addString("Enter the file suffix filter (e.g., tif):", "tif");
    Dialog.addChoice("Do you want to use GPU for processing?", newArray("Yes", "No"), "No");

    Dialog.show();

    // Retrieve user inputs
    inputDir = Dialog.getString();
    outputDir = Dialog.getString();
    fileFilter = Dialog.getString();
    useGPU = Dialog.getChoice();

    // Convert GPU choice to boolean
    useGPU = (useGPU == "Yes");

    list = getFileList(inputDir);

    // Set up measurement parameters such as area and mean which will be applied in ROI manager
    run("Set Measurements...", "area mean standard modal min display redirect=None decimal=3");
    print("Measurement settings applied.");

    // Iterate through each file in the directory
    for (i = 0; i < list.length; i++) {
        if (endsWith(list[i], fileFilter)) {
            processImage(inputDir, outputDir, list[i], useGPU); // Process each valid image
        }
    }
    IJ.log("Process completed for all files.");
    close("ROI Manager"); // Close ROI Manager after processing all files
    showMessage("Measurement completed for all files.");
}

function processImage(inputDir, outputDir, fileName, useGPU) {
    print("--------------------------------------------------------------------------------");
    open(inputDir + fileName); // Open image file
    orgName = getTitle(); // Get the title of the opened image
    shortName = File.getNameWithoutExtension(orgName); // Get the file name without the extension for later use
    print("Processing image file: " + orgName);

    // Set properties for the image based on the microscope calibration
    pixelWidth = 1.118; // Pixel width in microns, adjust as per your microscope's calibration
    pixelHeight = 1.118; // Pixel height in microns, consistent with pixel width
    run("Properties...", "channels=1 slices=1 frames=1 unit=um pixel_width=" + pixelWidth + " pixel_height=" + pixelHeight + " voxel_depth=1");

    // Image processing steps for detection
    run("8-bit");
    selectWindow(orgName);
    makeRectangle(0, 0, 1392, 1040);
    run("Duplicate...", "title=[copy.tif]");
    run("Pseudo flat field correction", "blurring=50 hide");
    print("Enhancing contrast with parameters: saturated=0.35, normalize, equalize");
    run("Enhance Contrast...", "saturated=0.35 normalize equalize");

    // Crystal detection using Cellpose Advanced (BIOP): adjust parameters according to your sample
    if (useGPU) {
        additional_flags = "--use_gpu";
        print("Using GPU for Cellpose segmentation [On Nvidia (CUDA) GPUs Only!]");
    } else {
        additional_flags = ""; // Fall back to use CPU
        print("Using CPU for Cellpose segmentation.");
    }

    run("Cellpose Advanced", "diameter=12 cellproba_threshold=0.0 flow_threshold=0.4 anisotropy=1.0 diam_threshold=12.0 model=cyto2 nuclei_channel=0 cyto_channel=1 dimensionmode=2D stitch_threshold=-1.0 omni=false cluster=false additional_flags=" + additional_flags);

    // Remove any labels at the borders
    run("Remove Border Labels", "left right top bottom");
    run("glasbey on dark");
    rename("labels-no-borders.tif");
    labelImage = getTitle();

    // Convert labels to ROIs
    run("Label image to ROIs", "rm=[RoiManager[size=13, visible=true]]");
    roiManager("Save", outputDir + File.separator + orgName + ".zip"); // Save ROIs for future reference

    // Morphometry with MorphoLibJ
    print("Running Analyze Regions (MorphoLibJ) with parameters:\n" +
      "  pixel_count\n" +
      "  area\n" +
      "  perimeter\n" +
      "  circularity\n" +
      "  bounding_box\n" +
      "  centroid\n" +
      "  equivalent_ellipse\n" +
      "  ellipse_elong.\n" +
      "  convexity\n" +
      "  max._feret\n" +
      "  geodesic tortuosity\n" +
      "  max._inscribed_disc\n" +
      "  average_thickness\n" +
      "  geodesic_elong.\n\n");

    run("Analyze Regions", "pixel_count area perimeter circularity bounding_box centroid equivalent_ellipse ellipse_elong. convexity max._feret geodesic tortuosity max._inscribed_disc average_thickness geodesic_elong.");

    // Clean up and save results
    roiManager("Deselect");
    roiManager("Delete");
    resultsPath = outputDir + File.separator + shortName + "_morphometry_results.csv";
    saveAs("Results", resultsPath); // Save results to a CSV file
    print("Results saved to: " + resultsPath);
    close(shortName + "_morphometry_results.csv");

    run("Equivalent Ellipse", "label=" + labelImage + " overlay overlay_0 image=[" + orgName + "]");
    close("labels-no-borders-Ellipses");
    selectWindow(orgName);
    run("Flatten");
    rename(shortName + "-eq-ellipse-img.tif");
    saveName = getTitle();
    saveAs("Tiff", outputDir + File.separator + saveName); // Save the equivalent ellipse image
    selectWindow(labelImage);
    run("Flatten");
    saveAs("Tiff", outputDir + File.separator + shortName + "-detection-label-img.tif"); // Save the equivalent ellipse image
    close("*");
}

