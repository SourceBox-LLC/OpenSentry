import cv2
import numpy as np
import time
import os
from dotenv import load_dotenv, find_dotenv

class ObjectDetector:
    def __init__(self):
        # Path to YOLO weights and configuration
        self.config_path = 'yolov3.cfg'
        self.weights_path = 'yolov3.weights'
        self.classes_path = 'coco.names'
        
        # Check if model files exist
        if not all(os.path.exists(f) for f in [self.config_path, self.weights_path, self.classes_path]):
            print("ERROR: YOLO model files not found. Please download them using download_models.py")
            print("Run: python download_models.py")
            exit()
        
        # Load YOLOv3 network
        self.net = cv2.dnn.readNetFromDarknet(self.config_path, self.weights_path)
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        
        # Load class names
        with open(self.classes_path, 'r') as f:
            self.classes = [line.strip() for line in f.readlines()]
        
        # Get output layer names
        self.layer_names = self.net.getLayerNames()
        self.output_layers = [self.layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
        
        # Load detection labels from .env if available
        load_dotenv(find_dotenv(filename='.env', usecwd=True))
        env_labels = os.environ.get('DETECTION_LABELS', 'person')
        self.target_classes = env_labels.split(',')
        
        print(f"Detecting objects: {', '.join(self.target_classes)}")
        
        # Colors for visualization (BGR format)
        # Generate colors dynamically based on class index
        self.colors = {}
        for class_name in self.target_classes:
            # Use a color based on the hash of the class name for consistency
            # This ensures the same class always gets the same color
            hash_val = hash(class_name) % 255
            self.colors[class_name] = (
                (hash_val * 71) % 256,  # B
                (hash_val * 173) % 256, # G
                (hash_val * 47) % 256   # R
            )
        
    def detect_objects(self, frame):
        height, width, _ = frame.shape
        
        # Create blob from input image
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
        
        # Set input to the network
        self.net.setInput(blob)
        
        # Run forward pass
        start_time = time.time()
        outs = self.net.forward(self.output_layers)
        end_time = time.time()
        
        # Show processing time
        processing_time = end_time - start_time
        fps = 1.0 / processing_time
        cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Initialize lists for detected objects
        class_ids = []
        confidences = []
        boxes = []
        
        # Process detections
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                # Filter detections by confidence and target classes
                if confidence > 0.5 and self.classes[class_id] in self.target_classes:
                    # Object detected
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    # Save details
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # Apply non-maximum suppression to remove overlapping boxes
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        
        # Draw bounding boxes and labels
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                class_name = self.classes[class_ids[i]]
                confidence = confidences[i]
                color = self.colors.get(class_name, (255, 0, 0))  # Default to blue if class not in colors dict
                
                # Draw bounding box
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                
                # Draw label background
                label = f"{class_name}: {confidence:.2f}"
                size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                cv2.rectangle(frame, (x, y - 25), (x + size[0], y), color, -1)
                
                # Draw label text
                cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return frame

def main():
    # Check if .env file exists with detection labels
    if not os.path.exists('.env'):
        print("WARNING: No .env file found with detection labels.")
        print("Run 'python setup.py' first to configure which objects to detect.")
        print("Proceeding with default configuration (detecting 'person' only)...")
    
    # Initialize detector
    detector = ObjectDetector()
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    while True:
        # Read frame
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to grab frame")
            break
        
        # Detect objects in the frame
        processed_frame = detector.detect_objects(frame)
        
        # Display result
        cv2.imshow("Object Detection", processed_frame)
        
        # Break loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
