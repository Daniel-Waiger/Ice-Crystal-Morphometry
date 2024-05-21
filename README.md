# Ice Crystal Morphometry in Fiji/ImageJ


This Fiji (ImageJ) macro script is designed for automated detection and morphometry analysis of ice crystals in merged TIF images. The script performs the following tasks:
1. Prompts the user to select directories for input images and output results.
2. Processes each image in the selected directory.
3. Applies image processing techniques to enhance and detect ice crystals.
4. Uses Cellpose Advanced for crystal detection and MorphoLibJ for morphometry analysis.
5. Saves results and processed images in the specified output directory.

## Short Workfllow Example - From Left to Right: Raw → Cellpose Label Image Without Border Labels → Ellipsoid Image.

<div style="display: flex; justify-content: center;">
  <img src="https://github.com/Daniel-Waiger/Ice-Crystal-Morphometry/assets/55537771/1dfc3437-417f-42eb-afd4-df74fad58d8e" alt="raw-image" style="width: 25%; vertical-align: top;" />
  <img src="https://github.com/Daniel-Waiger/Ice-Crystal-Morphometry/assets/55537771/5507fdbf-0a55-4bae-8a78-56f7dc1f7ef5" alt="cellpose-label-image" style="width: 25%; vertical-align: top;" />
  <img src="https://github.com/Daniel-Waiger/Ice-Crystal-Morphometry/assets/55537771/a9b0506d-1f33-47fb-a576-43b477b42e42" alt="ellipsoid-image" style="width: 25%; vertical-align: top;" />
</div>

## Pre-requisites
- [Fiji (ImageJ) Installation](https://fiji.sc)
- [Cellpose Installation](https://cellpose.readthedocs.io/en/latest/installation.html)
### Plugins and how to install them:
   - [BIOP Cellpose Wrapper Manual](https://github.com/BIOP/ijl-utilities-wrappers?tab=readme-ov-file#cellpose) - to use Cellpose Advanced in Fiji.
   - [MorphoLibJ Plugin] (https://imagej.net/plugins/morpholibj) - Wiki.
      - [How to install plugins in Fiji](https://www.youtube.com/watch?v=DFz9xmWi63I&t=47s&ab_channel=Lost-in-the-Shell)
      - [Fiji FAQ - Quick How-to Manual](https://imagej.net/learn/faq)

## Step-by-Step Instructions

### 1. Start the Macro
1. Open Fiji (ImageJ).
2. Open the script editor (Plugins > New > Macro).
3. Copy and paste the provided macro code into the editor.
   - Or, you can drag-and-drop the macro file onto Fiji's main toolbar, [ice-crystal-morphometry-analysis.ijm](https://github.com/Daniel-Waiger/Ice-Crystal-Morphometry/blob/main/ice-crystal-morphometry-analysis.ijm).

<p align="center">
  <img src="https://github.com/Daniel-Waiger/Ice-Crystal-Morphometry/assets/55537771/8abb6d99-0120-431d-898a-4f6cf91000a6" alt="Fiji Toolbar" style="width: 75%;" />
</p>
  
5. Run the macro (Run button in the script editor).

<p align="center">
  <img src="https://github.com/Daniel-Waiger/Ice-Crystal-Morphometry/assets/55537771/1882307d-c1f7-4871-a5eb-b3c939fc69a9" alt="script-editor-gui" style="width: 75%;">
</p>




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

| Parameter                | Description                                                                                                  | Significance                                                                                                 |
|--------------------------|--------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| **Pixel Count**          | The total number of pixels that make up the object.                                                          | Provides a basic measure of the object's size.                                                               |
| **Area**                 | The total area covered by the object in square microns.                                                      | Indicates the size of the object.                                                                            |
| **Perimeter**            | The length of the boundary around the object.                                                                | Helps in understanding the object's boundary characteristics and complexity.                                 |
| **Circularity**          | A measure of how close the shape of the object is to a perfect circle.                                       | A circularity value of 1 indicates a perfect circle, while values closer to 0 indicate more elongated or irregular shapes. |
|                          | **Formula**: Circularity = (4 × π × Area) / (Perimeter^2)                                                    |                                                                                                              |
| **Bounding Box**         | The smallest rectangle (aligned with the axes) that completely encloses the object.                          | Useful for calculating the extent and positioning of the object.                                             |
| **Centroid**             | The center of mass of the object.                                                                            | Provides the coordinates of the object's geometric center.                                                   |
| **Equivalent Ellipse**   | An ellipse that has the same normalized second central moments as the object.                                | Used to describe the shape and orientation of the object.                                                    |
| **Ellipse Elongation**   | The ratio of the major axis to the minor axis of the equivalent ellipse.                                     | Indicates how elongated the object is.                                                                       |
| **Convexity**            | The ratio of the object's area to the area of its convex hull (the smallest convex shape that encloses the object). | Values close to 1 indicate the object is more convex (less concave indentations).                            |
| **Maximum Feret Diameter** | The longest distance between any two points along the boundary of the object.                                | Provides a measure of the object's maximum dimension.                                                        |
| **Geodesic Tortuosity**  | A measure of the complexity of the object's shape, considering its internal path lengths.                    | Higher values indicate more complex and winding shapes.                                                      |
| **Maximum Inscribed Disc** | The diameter of the largest circle that can fit inside the object without crossing its boundary.              | Provides insight into the object's internal size and constraints.                                            |
| **Average Thickness**    | The average distance across the object, considering all internal points.                                     | Useful for understanding the overall "thickness" of the object.                                              |
| **Geodesic Elongation**  | The ratio of the maximum geodesic distance (shortest path within the object) to the diameter of the maximum inscribed disc. | Indicates the elongation of the object based on its internal path lengths.                                   |

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


