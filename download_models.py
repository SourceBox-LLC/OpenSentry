import urllib.request
import os
import sys

def download_file(url, filename):
    """Download a file from a URL to a local path"""
    print(f"Downloading {filename}...")
    try:
        urllib.request.urlretrieve(url, filename, report_progress)
        print(f"\nDownloaded {filename} successfully!")
        return True
    except Exception as e:
        print(f"\nFailed to download {filename}: {e}")
        return False

def report_progress(block_num, block_size, total_size):
    """Report download progress"""
    downloaded = block_num * block_size
    percent = min(int(downloaded * 100 / total_size), 100)
    sys.stdout.write(f"\rProgress: {percent}% ({downloaded} / {total_size} bytes)")
    sys.stdout.flush()

def main():
    # Create directory for models if it doesn't exist
    if not os.path.exists('models'):
        os.makedirs('models')
    
    # URLs for YOLOv3 model files
    urls = {
        'yolov3.weights': 'https://github.com/patrick013/Object-Detection---Yolov3/raw/master/model/yolov3.weights',
        'yolov3.cfg': 'https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov3.cfg',
        'coco.names': 'https://raw.githubusercontent.com/AlexeyAB/darknet/master/data/coco.names'
    }
    
    # Download each file
    success = True
    for filename, url in urls.items():
        if not os.path.exists(filename):
            success = download_file(url, filename) and success
        else:
            print(f"{filename} already exists, skipping download.")
    
    if success:
        print("\nAll model files downloaded successfully!")
        print("You can now run the object detection script: python object_detection.py")
    else:
        print("\nSome files failed to download. Please check your internet connection and try again.")

if __name__ == "__main__":
    main()
