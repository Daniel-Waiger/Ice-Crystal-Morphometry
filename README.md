# Ice Crystal Morphometry in FIji/ImageJ


This Fiji (ImageJ) macro script is designed for automated detection and morphometry analysis of ice crystals in merged TIF images. The script performs the following tasks:
1. Prompts the user to select directories for input images and output results.
2. Processes each image in the selected directory.
3. Applies image processing techniques to enhance and detect ice crystals.
4. Uses Cellpose Advanced for crystal detection and MorphoLibJ for morphometry analysis.
5. Saves results and processed images in the specified output directory.

## Pre-requisites
- **Fiji (ImageJ)**
- **Cellpose**
- **BIOP Plugin** - to use Cellpose Advanced
- **MorphoLibJ Plugin**

## Step-by-Step Instructions

### 1. Start the Macro
1. Open Fiji (ImageJ).
2. Open the script editor (Plugins > New > Macro).
3. Copy and paste the provided macro code into the editor.
4. Run the macro (Macros > Run).

### 2. Select Input and Output Folders
- The macro will prompt you to choose a directory containing the image files (input folder) and a directory to save the results (output folder).

### 3. Measurement Settings
- The macro sets measurement parameters such as area, mean, and standard deviation which will be applied in the ROI manager.

### 4. Process Each Image
* The macro iterates through each file in the directory and processes valid '.tif' images using the processImage function.

## Image Processing Steps
### a. Image Opening and Properties
* The image file is opened, and its properties are set based on the microscope calibration.

```javascript
open(dir + fileName);
run("Properties...", "channels=1 slices=1 frames=1 unit=um pixel_width=1.118 pixel_height=1.118 voxel_depth=1");
```

### b. Contrast Enhancement and Crystal Detection
* The script enhances the contrast of the image and uses the Cellpose Advanced plugin for crystal detection.

```javascript
run("Enhance Contrast...", "saturated=0.35 normalize equalize");
run("Cellpose Advanced", "diameter=12 cellproba_threshold=0.0 flow_threshold=0.4 anisotropy=1.0 diam_threshold=12.0 model=cyto2 nuclei_channel=0 cyto_channel=1 dimensionmode=2D stitch_threshold=-1.0 omni=false cluster=false additional_flags=");
``` 

### c. Label Image Conversion and Border Removal
* Converts the detected labels to ROIs and removes any labels at the borders.

```javascript
run("Remove Border Labels", "left right top bottom");
run("Label image to ROIs", "rm=[RoiManager[size=13, visible=true]]");
``` 

### d. Morphometry Analysis
* Uses the MorphoLibJ plugin to analyze regions and save the results.
* 
```javascript
run("Analyze Regions", "pixel_count area perimeter circularity bounding_box centroid equivalent_ellipse ellipse_elong. convexity max._feret geodesic tortuosity max._inscribed_disc average_thickness geodesic_elong.");
``` 

# Morphometry Parameters Explained

When performing morphometry analysis, various parameters are used to quantify the geometric and structural properties of the detected objects. Below are the explanations for the key parameters used in the Ice Crystal Morphometry Macro:

## Morphometry Parameters

### 1. Pixel Count
- **Description**: The total number of pixels that make up the object.
- **Significance**: Provides a basic measure of the object's size.

### 2. Area
- **Description**: The total area covered by the object in square microns.
- **Significance**: Indicates the size of the object.

### 3. Perimeter
- **Description**: The length of the boundary around the object.
- **Significance**: Helps in understanding the object's boundary characteristics and complexity.

### 4. Circularity
- **Description**: A measure of how close the shape of the object is to a perfect circle.
- **Formula**: Circularity = (4 × π × Area) / (Perimeter^2)
- **Significance**: A circularity value of 1 indicates a perfect circle, while values closer to 0 indicate more elongated or irregular shapes.

### 5. Bounding Box
- **Description**: The smallest rectangle (aligned with the axes) that completely encloses the object.
- **Significance**: Useful for calculating the extent and positioning of the object.

### 6. Centroid
- **Description**: The center of mass of the object.
- **Significance**: Provides the coordinates of the object's geometric center.

### 7. Equivalent Ellipse
- **Description**: An ellipse that has the same normalized second central moments as the object.
- **Significance**: Used to describe the shape and orientation of the object.

### 8. Ellipse Elongation
- **Description**: The ratio of the major axis to the minor axis of the equivalent ellipse.
- **Significance**: Indicates how elongated the object is.

### 9. Convexity
- **Description**: The ratio of the object's area to the area of its convex hull (the smallest convex shape that encloses the object).
- **Significance**: Values close to 1 indicate the object is more convex (less concave indentations).

### 10. Maximum Feret Diameter
- **Description**: The longest distance between any two points along the boundary of the object.
- **Significance**: Provides a measure of the object's maximum dimension.

### 11. Geodesic Tortuosity
- **Description**: A measure of the complexity of the object's shape, considering its internal path lengths.
- **Significance**: Higher values indicate more complex and winding shapes.

### 12. Maximum Inscribed Disc
- **Description**: The diameter of the largest circle that can fit inside the object without crossing its boundary.
- **Significance**: Provides insight into the object's internal size and constraints.

### 13. Average Thickness
- **Description**: The average distance across the object, considering all internal points.
- **Significance**: Useful for understanding the overall "thickness" of the object.

### 14. Geodesic Elongation
- **Description**: The ratio of the maximum geodesic distance (shortest path within the object) to the diameter of the maximum inscribed disc.
- **Significance**: Indicates the elongation of the object based on its internal path lengths.

These parameters collectively provide a comprehensive understanding of the geometric and structural properties of the detected objects, allowing for detailed analysis and comparison.


## Results and Visualization
### Save Results
* The results of the morphometry analysis are saved in a CSV file in the output directory.

```javascript
saveAs("Results", resultsPath); // Save results to a CSV file
``` 

## Save Processed Images
* The equivalent ellipse image and detection label image are flattened and saved.

```javascript
run("Flatten");
saveAs("Tiff", saveDir + saveName); // Save the equivalent ellipse image
``` 

## Visualization
* The macro includes visualization tools such as generating and saving equivalent ellipse images for better interpretation of the results.

## Example Output
* '.csv' File: Contains detailed morphometry analysis results.
* '.tif' Files: Include processed images with detected crystals and equivalent ellipses.


