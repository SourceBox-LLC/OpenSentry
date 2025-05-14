import os
import time
import smtplib
import threading
import cv2
import imghdr
from email.message import EmailMessage
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

class NotificationManager:
    def __init__(self):
        # Load environment variables
        load_dotenv(find_dotenv(filename='.env', usecwd=True))
        
        # Email configuration
        self.email_enabled = os.environ.get('EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
        self.sender_email = os.environ.get('SENDER_EMAIL', '')
        self.sender_password = os.environ.get('SENDER_PASSWORD', '')
        self.recipient_email = os.environ.get('RECIPIENT_EMAIL', '')
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        
        # Notification configuration
        self.notification_timeout = int(os.environ.get('NOTIFICATION_TIMEOUT', '300'))  # 5 minutes default
        self.last_notification_time = {}
        self.notification_lock = threading.Lock()
        
        # Create directory for snapshot images if it doesn't exist
        self.snapshots_dir = 'snapshots'
        os.makedirs(self.snapshots_dir, exist_ok=True)
        
        # Log initialization
        if self.email_enabled:
            print(f"Email notifications enabled. Sending to {self.recipient_email}")
            print(f"Notification timeout set to {self.notification_timeout} seconds")
        else:
            print("Email notifications disabled. Configure in .env file to enable.")
    
    def is_notification_allowed(self, object_name):
        """Check if notification is allowed based on timeout period"""
        with self.notification_lock:
            current_time = time.time()
            last_time = self.last_notification_time.get(object_name, 0)
            
            # Check if enough time has passed since last notification
            if current_time - last_time >= self.notification_timeout:
                # Update the last notification time
                self.last_notification_time[object_name] = current_time
                return True
            return False
    
    def send_notification(self, detected_objects, frame):
        """Send email notification with detected objects and image"""
        if not self.email_enabled or not detected_objects:
            return
        
        # Process each detected object
        for obj in detected_objects:
            object_name = obj['name']
            confidence = obj['confidence']
            
            # Check if notification is allowed for this object
            if not self.is_notification_allowed(object_name):
                continue
            
            # Save snapshot image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"{self.snapshots_dir}/{object_name}_{timestamp}.jpg"
            cv2.imwrite(image_filename, frame)
            
            # Create email
            msg = EmailMessage()
            msg['Subject'] = f'OpenSentry Alert: {object_name} Detected'
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            # Email body
            body = f"OpenSentry Security Alert\n\n"
            body += f"Object Detected: {object_name}\n"
            body += f"Confidence: {confidence:.2f}\n"
            body += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            body += f"A snapshot image is attached.\n"
            msg.set_content(body)
            
            # Attach image
            with open(image_filename, 'rb') as img:
                img_data = img.read()
                msg.add_attachment(img_data, maintype='image',
                                  subtype=imghdr.what(None, img_data),
                                  filename=os.path.basename(image_filename))
            
            # Send email in a separate thread to avoid blocking
            threading.Thread(target=self._send_email_async, args=(msg,)).start()
            
            print(f"Notification queued: {object_name} detected")
    
    def _send_email_async(self, msg):
        """Send email asynchronously"""
        try:
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable secure connection
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            print(f"Email notification sent successfully to {self.recipient_email}")
        except Exception as e:
            print(f"Failed to send email notification: {str(e)}")

# Global notification manager instance
notification_manager = NotificationManager()