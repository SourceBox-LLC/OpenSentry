import cv2
import numpy as np
import time
import os
import threading
import io
import glob
import json
from pathlib import Path
from fastapi import FastAPI, Response, Request, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Iterator, Dict, Any, List
from dotenv import load_dotenv, find_dotenv
import uvicorn

# Import notification manager
from notification import notification_manager

# Create snapshots directory if it doesn't exist
os.makedirs('snapshots', exist_ok=True)

# Class for object detection from the original app
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
        
        # List to track detected objects for notifications
        detected_objects = []
        
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
                    
                    # Add to detected objects for notification
                    detected_objects.append({
                        'name': self.classes[class_id],
                        'confidence': confidence,
                        'box': [x, y, w, h]
                    })
        
        # Apply non-maximum suppression to remove overlapping boxes
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        
        # Final list of detected objects after NMS
        final_detections = []
        
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
                
                # Add to final detections for notification
                final_detections.append({
                    'name': class_name,
                    'confidence': confidence,
                    'box': [x, y, w, h]
                })
        
        # Send notifications for detected objects
        if final_detections:
            notification_manager.send_notification(final_detections, frame)
        
        return frame

# Define the lifespan context manager for events
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create background task for camera management
    def check_camera_usage():
        while True:
            release_camera()
            time.sleep(10)  # Check every 10 seconds
    
    # Start the thread
    camera_thread = threading.Thread(target=check_camera_usage, daemon=True)
    camera_thread.start()
    
    # Yield control back to FastAPI
    yield
    
    # Shutdown logic (if needed)
    global camera
    if camera is not None:
        with camera_lock:
            camera.release()
            camera = None
            print("Camera released during shutdown")

# Create FastAPI app with lifespan
app = FastAPI(
    title="OpenSentry API", 
    description="Security Camera API with object detection",
    lifespan=lifespan
)

# Allow cross-origin requests to access the API from any domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Mount the snapshots directory as a static files directory
app.mount("/static/snapshots", StaticFiles(directory="snapshots"), name="snapshots")

# Global variables for camera handling
camera = None
camera_lock = threading.Lock()
last_access = time.time()

def get_camera():
    """
    Get camera with thread-safe access
    """
    global camera
    with camera_lock:
        if camera is None:
            camera = cv2.VideoCapture(0)
    return camera

def release_camera():
    """
    Release camera resources if not used for a while
    """
    global camera, last_access
    if camera is not None and time.time() - last_access > 60:  # Release after 60 seconds of inactivity
        with camera_lock:
            if camera is not None:
                camera.release()
                camera = None
                print("Camera released due to inactivity")

def generate_frames() -> Iterator[bytes]:
    """
    Generate frames from the camera feed with object detection
    """
    global last_access
    detector = ObjectDetector()
    
    while True:
        # Update the last access time
        last_access = time.time()
        
        # Get camera
        cap = get_camera()
        
        # Read frame
        success, frame = cap.read()
        if not success:
            print("Failed to grab frame")
            break
            
        # Process frame with object detection
        processed_frame = detector.detect_objects(frame)
        
        # Encode as JPEG
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        if not ret:
            continue
            
        # Convert to bytes
        frame_bytes = buffer.tobytes()
        
        # Yield frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Small delay to control frame rate
        time.sleep(0.03)  # ~30fps

# API endpoints
@app.get("/")
async def root():
    """
    Root endpoint with API info
    """
    return {
        "name": "OpenSentry API",
        "version": "1.0.0",
        "description": "Security Camera API with object detection",
        "endpoints": [
            {
                "path": "/stream",
                "description": "Stream the camera feed with object detection"
            },
            {
                "path": "/status",
                "description": "Get API status"
            }
        ]
    }

@app.get("/stream")
async def stream():
    """
    Stream video feed as MJPEG
    """
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/status")
async def status() -> Dict[str, Any]:
    """
    Get API status
    """
    email_enabled = os.environ.get('EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
    recipient = os.environ.get('RECIPIENT_EMAIL', 'Not configured')
    timeout = os.environ.get('NOTIFICATION_TIMEOUT', '300')
    
    # Count snapshots
    snapshot_count = 0
    if os.path.exists('snapshots'):
        snapshot_count = len(glob.glob('snapshots/*.jpg'))
    
    return {
        "status": "online",
        "timestamp": time.time(),
        "detecting": os.environ.get('DETECTION_LABELS', 'person').split(','),
        "notifications": {
            "email_enabled": email_enabled,
            "recipient": recipient if email_enabled else None,
            "timeout": timeout if email_enabled else None,
            "snapshot_count": snapshot_count
        }
    }

@app.get("/snapshots")
async def list_snapshots() -> Dict[str, Any]:
    """
    List all snapshot images
    """
    snapshots_dir = 'snapshots'
    if not os.path.exists(snapshots_dir):
        return {"snapshots": [], "count": 0}
    
    # Get all JPG files in the snapshots directory
    snapshot_files = glob.glob(f"{snapshots_dir}/*.jpg")
    
    # Sort by modification time (newest first)
    snapshot_files.sort(key=os.path.getmtime, reverse=True)
    
    snapshots = []
    for file_path in snapshot_files:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        mod_time = os.path.getmtime(file_path)
        
        # Parse detection info from filename (format: object_timestamp.jpg)
        parts = os.path.splitext(file_name)[0].split('_')
        detected_object = parts[0] if len(parts) > 0 else "unknown"
        
        snapshots.append({
            "filename": file_name,
            "path": file_path,
            "size": file_size,
            "timestamp": mod_time,
            "detected_object": detected_object,
            "url": f"/static/snapshots/{file_name}"
        })
    
    return {"snapshots": snapshots, "count": len(snapshots)}

@app.get("/snapshots/{filename}")
async def get_snapshot(filename: str):
    """
    Download a snapshot image
    """
    # Validate filename to prevent directory traversal attacks
    if '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = os.path.join('snapshots', filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    return FileResponse(file_path, filename=filename)

@app.delete("/snapshots/{filename}")
async def delete_snapshot(filename: str, background_tasks: BackgroundTasks):
    """
    Delete a snapshot image
    """
    # Validate filename to prevent directory traversal attacks
    if '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = os.path.join('snapshots', filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    # Delete file in background to avoid blocking
    def remove_file(path: str):
        try:
            os.remove(path)
        except Exception as e:
            print(f"Error deleting file {path}: {str(e)}")
    
    background_tasks.add_task(remove_file, file_path)
    
    return {"success": True, "message": f"Deleted {filename}"}

@app.delete("/snapshots")
async def delete_all_snapshots(background_tasks: BackgroundTasks):
    """
    Delete all snapshot images
    """
    snapshots_dir = 'snapshots'
    if not os.path.exists(snapshots_dir):
        return {"success": True, "message": "No snapshots to delete"}
    
    # Get all JPG files in the snapshots directory
    snapshot_files = glob.glob(f"{snapshots_dir}/*.jpg")
    
    # Delete files in background
    def remove_files(paths: List[str]):
        for path in paths:
            try:
                os.remove(path)
            except Exception as e:
                print(f"Error deleting file {path}: {str(e)}")
    
    background_tasks.add_task(remove_files, snapshot_files)
    
    return {"success": True, "message": f"Deleting {len(snapshot_files)} snapshots"}

# Lifespan handler is defined at the top of the file

if __name__ == "__main__":
    # Check if .env file exists with detection labels
    if not os.path.exists('.env'):
        print("WARNING: No .env file found with detection labels.")
        print("Run 'python setup.py' first to configure which objects to detect.")
        print("Proceeding with default configuration (detecting 'person' only)...")
    
    # Run the FastAPI app with uvicorn
    print("Starting OpenSentry API server...")
    print("To access from other devices on your network or internet, use your IP address/domain")
    print("Stream URL: http://your-ip:8000/stream")
    
    uvicorn.run(
        "server:app", 
        host="0.0.0.0",  # Make server available on network
        port=8000, 
        reload=False
    )
