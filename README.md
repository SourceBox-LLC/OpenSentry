# Real-Time Object Detection with OpenCV and YOLOv3

A computer vision application that performs real-time object detection using OpenCV and the YOLOv3 model. The system can detect multiple objects simultaneously from a webcam feed, highlighting them with bounding boxes and displaying confidence scores. Users can customize which objects to detect through a simple setup process.

## Features

- Live webcam-based object detection
- Customizable object detection (choose up to 10 classes)
- Interactive setup wizard for selecting detection targets
- Real-time bounding box visualization
- Confidence score display
- FPS counter to monitor performance
- Dynamic color assignment for different object types

## Requirements

- Python 3.6+
- OpenCV
- NumPy
- python-dotenv
- Webcam or camera device

## Installation

1. Clone or download this repository

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Download the YOLOv3 model files:
   ```
   python download_models.py
   ```
   This will download:
   - YOLOv3 weights
   - YOLOv3 configuration
   - COCO class names



## Usage

1. Make sure your camera is connected

2. (Optional) Run the setup wizard to customize which objects to detect:
   ```
   python setup.py
   ```
   - Follow the prompts to select up to 10 object classes
   - Your selections will be saved to a `.env` file

3. Run the detection script:
   ```
   python app.py
   ```

4. A window will open showing the live camera feed with object detection

5. Press 'q' to quit the application



## How It Works

The application uses YOLOv3 (You Only Look Once), a state-of-the-art object detection model that can identify multiple objects in a single frame. The process works as follows:

1. The webcam captures frames in real-time
2. Each frame is processed through the YOLOv3 neural network
3. The network identifies objects and their locations in the frame
4. Bounding boxes are drawn around detected objects
5. Confidence scores are displayed to indicate detection certainty
6. The processed frame is shown to the user

## Customization

### Selecting Objects to Detect

The application can detect any of the 80 object classes in the COCO dataset. There are two ways to customize detection:

#### Option 1: Using the Setup Wizard (Recommended)

Run the interactive setup wizard:
```
python setup.py
```

This will:
1. Display all available object classes
2. Let you select up to 10 classes to detect (for performance reasons)
3. Save your preferences to a `.env` file

#### Option 2: Manual Configuration

Create or edit the `.env` file in the project root:
```
DETECTION_LABELS=person,car,dog,chair
```

The labels must match exactly the class names in the `coco.names` file.

Available classes include:
- Common objects: person, bicycle, car, motorbike, airplane, bus, train, etc.
- Animals: dog, cat, horse, sheep, cow, elephant, bear, zebra, giraffe, etc.
- Everyday items: backpack, umbrella, handbag, tie, suitcase, etc.
- Furniture: chair, sofa, bed, dining table, etc.
- Electronics: tv, laptop, mouse, keyboard, cell phone, etc.
- And many more!

### Adjusting Detection Parameters

To modify the detection sensitivity:
1. In `app.py`, find the `detect_objects` method
2. Adjust the confidence threshold (default is 0.5) in the line: `if confidence > 0.5 and self.classes[class_id] in self.target_classes:`
3. Lower values will detect more objects but may include more false positives
4. Higher values will be more selective but might miss some objects

## License

This project is provided for educational purposes.

## Acknowledgments

- YOLOv3 by Joseph Redmon and Ali Farhadi
- OpenCV community
