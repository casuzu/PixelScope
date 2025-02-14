# Contact_Angle_by_Hand: An Image Analysis Tool 
**Analyze fluid interfaces with precision and simplicity.**
 
## Overview: This software helps in analyzing images of fluid interfaces in low-gravity conditions.

## Key Features
-Perform image analysis using a simple UI.

-Generate canny-edged image for deeper image analysis, which highlight significant edges in the image to facilitate precise fluid interface detection.

-Click to draw Lines and points.

-Scroll to zoom-in on image for precise point notations.

-Simple slider to overlay and transition between original image and canny-edged image.

-Line calibration to derive unit line pixel-mm relationship allowing users to convert measurements from pixel units to physical dimensions. 
This is crucial for ensuring accurate quantitative analysis of fluid interfaces.

-Drag and drop precise lines.

-Automatic save and export images.

-Automatic save and Export line data to Excel sheets.

## System Requirement
### Required:
- **Operating System**: Windows 10 or later  
- **Python Version**: Python 3.11 or later  
- **Dependencies**: Listed in 'requirements.txt' 

### Additional Notes:
- `tkinter` is built into standard Windows Python installations.
- This software has not been tested on non-Windows platforms. 

## Installation
1. Clone the repository from GitHub using bash: 
git clone https://github.com/casuzu/Contact-Angle-by-Hand.git

2. Navigate to the project directory:
cd Contact-Angle-by-Hand

3. Install the required dependencies:
py -m pip install -r requirements.txt

4. Run the application:
python main.py

