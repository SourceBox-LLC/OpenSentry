#!/usr/bin/env python
import os
import sys
import re
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
    
        # Ask if user wants to configure email notifications
    print("\n===== Email Notification Setup =====")
    print("Would you like to configure email notifications for detected objects?")
    setup_email = input("Configure email notifications? (y/n): ").strip().lower() == 'y'
    
    # Load existing .env content if available
    existing_env = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    existing_env[key] = value
    
    # Set the detection labels
    existing_env['DETECTION_LABELS'] = ','.join(selected_classes)
    
    if setup_email:
        # Email notification config
        print("\nEmail notification setup:")
        print("This will allow OpenSentry to send you email alerts when objects are detected.")
        print("Note: For Gmail, you need to create an 'App Password' in your Google Account settings.")
        
        # Enable/disable email notifications
        existing_env['EMAIL_NOTIFICATIONS'] = 'true'
        
        # Email credentials
        sender_email = input("\nSender email address: ").strip()
        while not re.match(r"[^@]+@[^@]+\.[^@]+", sender_email):
            print("Invalid email format. Please enter a valid email address.")
            sender_email = input("Sender email address: ").strip()
        existing_env['SENDER_EMAIL'] = sender_email
        
        sender_password = input("Email password or app password: ").strip()
        existing_env['SENDER_PASSWORD'] = sender_password
        
        recipient_email = input("\nRecipient email address (where to send alerts): ").strip()
        while not re.match(r"[^@]+@[^@]+\.[^@]+", recipient_email):
            print("Invalid email format. Please enter a valid email address.")
            recipient_email = input("Recipient email address: ").strip()
        existing_env['RECIPIENT_EMAIL'] = recipient_email
        
        # SMTP server settings (with defaults for common providers)
        print("\nSMTP Server Settings:")
        print("Common settings:")
        print("1. Gmail: smtp.gmail.com:587")
        print("2. Outlook/Hotmail: smtp-mail.outlook.com:587")
        print("3. Yahoo: smtp.mail.yahoo.com:587")
        print("4. Custom")
        
        smtp_choice = input("Choose SMTP provider (1-4): ").strip()
        if smtp_choice == '1':
            existing_env['SMTP_SERVER'] = 'smtp.gmail.com'
            existing_env['SMTP_PORT'] = '587'
        elif smtp_choice == '2':
            existing_env['SMTP_SERVER'] = 'smtp-mail.outlook.com'
            existing_env['SMTP_PORT'] = '587'
        elif smtp_choice == '3':
            existing_env['SMTP_SERVER'] = 'smtp.mail.yahoo.com'
            existing_env['SMTP_PORT'] = '587'
        else:
            smtp_server = input("SMTP server address: ").strip()
            smtp_port = input("SMTP port: ").strip()
            existing_env['SMTP_SERVER'] = smtp_server
            existing_env['SMTP_PORT'] = smtp_port
        
        # Notification timeout
        print("\nNotification Timeout:")
        print("This is the minimum time between notifications for the same object.")
        print("Default is 300 seconds (5 minutes).")
        
        try:
            timeout = int(input("Notification timeout in seconds: ").strip() or "300")
            if timeout < 10:
                print("Timeout too short. Setting to minimum of 10 seconds.")
                timeout = 10
            existing_env['NOTIFICATION_TIMEOUT'] = str(timeout)
        except ValueError:
            print("Invalid input. Using default of 300 seconds.")
            existing_env['NOTIFICATION_TIMEOUT'] = '300'
    else:
        # Disable email notifications if user chooses not to set them up
        existing_env['EMAIL_NOTIFICATIONS'] = 'false'
        
    # Create or update .env file content
    env_content = '\n'.join([f"{key}={value}" for key, value in existing_env.items()])
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\nConfiguration saved to {env_path}")
    print("Your object detection preferences have been saved.")
    print("Run 'python app.py' to start detection with these settings.")
    
    return True

def main():
    # Main setup function
    print("\n===== OpenSentry Configuration Wizard =====\n")
    print("This wizard will help you configure OpenSentry for your needs.")
    print("1. Configure object detection")
    print("2. Configure email notifications")
    print("3. Configure both")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        setup_detection_labels()
    elif choice == '2':
        setup_email_notifications()
    elif choice == '3':
        setup_detection_labels()
        setup_email_notifications()
    else:
        print("Setup canceled.")
        return

def setup_email_notifications():
    """Setup email notification configuration"""
    print("\n===== Email Notification Setup =====")
    
    # Load existing configuration if available
    env_path = '.env'
    load_dotenv(find_dotenv(filename=env_path, usecwd=True))
    
    # Load existing .env content if available
    existing_env = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    existing_env[key] = value
    
    # Show current email settings if any
    if 'EMAIL_NOTIFICATIONS' in existing_env and existing_env['EMAIL_NOTIFICATIONS'] == 'true':
        print("Current email notification settings:")
        print(f"Recipient: {existing_env.get('RECIPIENT_EMAIL', 'Not set')}")
        print(f"SMTP Server: {existing_env.get('SMTP_SERVER', 'Not set')}")
        print(f"Notification timeout: {existing_env.get('NOTIFICATION_TIMEOUT', '300')} seconds")
    
    # Enable/disable email notifications
    existing_env['EMAIL_NOTIFICATIONS'] = 'true'
    
    # Email credentials
    sender_email = input("\nSender email address: ").strip()
    while not re.match(r"[^@]+@[^@]+\.[^@]+", sender_email):
        print("Invalid email format. Please enter a valid email address.")
        sender_email = input("Sender email address: ").strip()
    existing_env['SENDER_EMAIL'] = sender_email
    
    sender_password = input("Email password or app password: ").strip()
    existing_env['SENDER_PASSWORD'] = sender_password
    
    recipient_email = input("\nRecipient email address (where to send alerts): ").strip()
    while not re.match(r"[^@]+@[^@]+\.[^@]+", recipient_email):
        print("Invalid email format. Please enter a valid email address.")
        recipient_email = input("Recipient email address: ").strip()
    existing_env['RECIPIENT_EMAIL'] = recipient_email
    
    # SMTP server settings (with defaults for common providers)
    print("\nSMTP Server Settings:")
    print("Common settings:")
    print("1. Gmail: smtp.gmail.com:587")
    print("2. Outlook/Hotmail: smtp-mail.outlook.com:587")
    print("3. Yahoo: smtp.mail.yahoo.com:587")
    print("4. Custom")
    
    smtp_choice = input("Choose SMTP provider (1-4): ").strip()
    if smtp_choice == '1':
        existing_env['SMTP_SERVER'] = 'smtp.gmail.com'
        existing_env['SMTP_PORT'] = '587'
    elif smtp_choice == '2':
        existing_env['SMTP_SERVER'] = 'smtp-mail.outlook.com'
        existing_env['SMTP_PORT'] = '587'
    elif smtp_choice == '3':
        existing_env['SMTP_SERVER'] = 'smtp.mail.yahoo.com'
        existing_env['SMTP_PORT'] = '587'
    else:
        smtp_server = input("SMTP server address: ").strip()
        smtp_port = input("SMTP port: ").strip()
        existing_env['SMTP_SERVER'] = smtp_server
        existing_env['SMTP_PORT'] = smtp_port
    
    # Notification timeout
    print("\nNotification Timeout:")
    print("This is the minimum time between notifications for the same object.")
    print("Default is 300 seconds (5 minutes).")
    
    try:
        timeout = int(input("Notification timeout in seconds: ").strip() or "300")
        if timeout < 10:
            print("Timeout too short. Setting to minimum of 10 seconds.")
            timeout = 10
        existing_env['NOTIFICATION_TIMEOUT'] = str(timeout)
    except ValueError:
        print("Invalid input. Using default of 300 seconds.")
        existing_env['NOTIFICATION_TIMEOUT'] = '300'
    
    # Create or update .env file content
    env_content = '\n'.join([f"{key}={value}" for key, value in existing_env.items()])
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\nEmail notification configuration saved to {env_path}")
    print("You will now receive email alerts when specified objects are detected.")
    return True

if __name__ == "__main__":
    main()
