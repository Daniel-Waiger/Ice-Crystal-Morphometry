// Fiji Macro for Combined Automated Spheroid Detection and Live/Dead Analysis
// This macro integrates spheroid detection with live/dead analysis in merged tif images.

macro "Ice Crystal Morphometry" {
    // Initialize the console for logging progress and outputs
    run("Close Fiji Console");
    run("Console");
    close("Log");
    IJ.log("Starting ice crystal detection and morphometry.");
    
    // Prompt user to select a directory containing the image files to be processed
   	waitForUser("Input and Output Folders", "Before this macro starts processing your files you \n"
    + "will need to choose the input folder (image folder),\n"
     + "and the output folder (Results folder).");
    
    dir = getDirectory("Choose a directory containing the image files");
    print("Image folder path: " + dir);
    saveDir = getDirectory("Choose a directory to save your results");
    print("Results folder path: " + saveDir);
	list = getFileList(dir);
    filter = "tif";
    
    // Set up measurement parameters such as area and mean which will be applied in ROI manager
    run("Set Measurements...", "area mean standard modal min display redirect=None decimal=3");
    print("Measurement settings applied.");

    // Iterate through each file in the directory
    for (i = 0; i < list.length; i++) {
        if (endsWith(list[i], filter)) {
            processImage(dir, list[i]); // Process each valid image
        }
    }
    IJ.log("Process completed for all files.");
    close("ROI Manager"); // Close ROI Manager after processing all files
    showMessage("Measurement completed for all files.");
}

function processImage(dir, fileName) {
    print("--------------------------------------------------------------------------------");
    open(dir + fileName); // Open image file
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
    print("Running Cellpose Advanced with parameters:\n" +
      "  diameter=12[pix]\n" +
      "  cellproba_threshold=0.0\n" +
      "  flow_threshold=0.4\n" +
      "  anisotropy=1.0\n" +
      "  diam_threshold=12.0\n" +
      "  model=cyto2\n" +
      "  nuclei_channel=0\n" +
      "  cyto_channel=1\n" +
      "  dimensionmode=2D\n" +
      "  stitch_threshold=-1.0\n" +
      "  omni=false\n" +
      "  cluster=false\n" + 
      "  additional_flags=\n\n");
      
      
    run("Cellpose Advanced", "diameter=12 cellproba_threshold=0.0 flow_threshold=0.4 anisotropy=1.0 diam_threshold=12.0 model=cyto2 nuclei_channel=0 cyto_channel=1 dimensionmode=2D stitch_threshold=-1.0 omni=false cluster=false additional_flags=");
    
    // Remove any labels at the borders
    run("Remove Border Labels", "left right top bottom"); 
    run("glasbey on dark");
    rename("labels-no-borders.tif");
    labelImage = getTitle();
	// Convert labels to ROIs
	run("Label image to ROIs", "rm=[RoiManager[size=13, visible=true]]"); 
    roiManager("Save", saveDir + orgName + ".zip"); // Save ROIs for future reference
    
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
    resultsPath = saveDir + shortName + "_morphometry_results.csv";
    saveAs("Results", resultsPath); // Save results to a CSV file
    print("Results saved to: " + resultsPath);
    close(shortName + "_morphometry_results.csv");
    
    run("Equivalent Ellipse", "label=" + labelImage + " overlay overlay_0 image=[" + orgName + "]");
    close("labels-no-borders-Ellipses");
    selectWindow(orgName);
    run("Flatten");
    rename(shortName + "-eq-ellipse-img.tif");
    saveName = getTitle();
    saveAs("Tiff", saveDir + saveName); // Save the equivalent ellipse image
    selectWindow(labelImage);
    run("Flatten");
    saveAs("Tiff", saveDir + shortName + "-detection-label-img.tif"); // Save the equivalent ellipse image
    close("*");
}
