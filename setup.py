#!/usr/bin/env python
import os
import sys
import cv2
import numpy as np
from dotenv import load_dotenv, find_dotenv

def setup_detection_labels():
    """
    Interactive setup to choose object detection labels.
    Creates or updates .env file with user preferences.
    """
    print("\n===== Object Detection Setup =====")
    print("This setup will help you choose which objects to detect in your video stream.")
    
    # Try to load existing classes
    classes_path = 'coco.names'
    if not os.path.exists(classes_path):
        print(f"ERROR: {classes_path} not found. Please run download_models.py first.")
        print("Run: python download_models.py")
        return False
    
    # Load available classes
    with open(classes_path, 'r') as f:
        available_classes = [line.strip() for line in f.readlines()]
    
    # Load existing configuration if available
    env_path = '.env'
    load_dotenv(find_dotenv(filename=env_path, usecwd=True))
    
    existing_labels = os.environ.get('DETECTION_LABELS', '')
    if existing_labels:
        existing_labels = existing_labels.split(',')
        print(f"\nCurrent detection labels: {', '.join(existing_labels)}")
    
    # Show available classes
    print("\nAvailable object classes:")
    for i, class_name in enumerate(available_classes):
        print(f"{i+1}. {class_name}")
    
    # Get user selection
    print("\nChoose which objects to detect (min 1, max 10):")
    print("Enter the numbers corresponding to the objects, separated by commas")
    print("Example: 1,2,5,9")
    
    valid_selection = False
    while not valid_selection:
        try:
            selection_input = input("\nYour selection: ").strip()
            
            # Check if user wants to see a description of what's available
            if selection_input.lower() in ['help', '?', 'list']:
                print("\nAvailable object classes:")
                for i, class_name in enumerate(available_classes):
                    print(f"{i+1}. {class_name}")
                continue
                
            selections = [int(x.strip()) for x in selection_input.split(',')]
            
            # Validate input
            if not selections:
                print("Error: You must select at least one object.")
                continue
                
            if len(selections) > 10:
                print("Error: You can select a maximum of 10 objects for performance reasons.")
                continue
                
            # Check if all selections are valid
            invalid_selections = [s for s in selections if s < 1 or s > len(available_classes)]
            if invalid_selections:
                print(f"Error: Invalid selection(s): {invalid_selections}")
                print(f"Please enter numbers between 1 and {len(available_classes)}.")
                continue
                
            valid_selection = True
            
        except ValueError:
            print("Error: Please enter valid numbers separated by commas.")
    
    # Get the selected class names
    selected_classes = [available_classes[i-1] for i in selections]
    print(f"\nYou selected: {', '.join(selected_classes)}")
    
    # Confirm selection
    confirm = input("\nConfirm these selections? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Setup cancelled. No changes were made.")
        return False
    
    # Create or update .env file
    env_content = f"DETECTION_LABELS={','.join(selected_classes)}"
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\nConfiguration saved to {env_path}")
    print("Your object detection preferences have been saved.")
    print("Run 'python app.py' to start detection with these settings.")
    
    return True

if __name__ == "__main__":
    setup_detection_labels()
