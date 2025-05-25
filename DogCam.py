import cv2
import requests
import time
import RPi.GPIO as GPIO
from picamera2 import Picamera2
import firebase_admin
from firebase_admin import credentials, messaging
from datetime import datetime
import os


# Configuration
SERVER_IP = "192.168.86.237"  # Replace with your PC IP
UPLOAD_URL = f"http://{SERVER_IP}:3000/upload"
NOTIFY_URL = f"http://{SERVER_IP}:3000/set_notification"
CAMERA_STATUS_URL = f"http://{SERVER_IP}:3000/camera_status"
PIR_PIN = 17
FCM_TOKEN = "YOUR_DEVICE_FCM_TOKEN_HERE"


PHOTO_DIR = "/home/Flynnpi/DogPhotos"  
os.makedirs(PHOTO_DIR, exist_ok=True)

# Firebase setup
cred = credentials.Certificate("/home/pi/dogsurveillance-a57aa-557c23f41b8a.json")  
firebase_admin.initialize_app(cred)

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

# Camera setup
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))

def update_notification(msg):
    try:
        requests.get(NOTIFY_URL, params={"msg": msg})
    except Exception as e:
        print(f"Notification update failed: {e}")

def update_camera_status(active):
    try:
        requests.get(CAMERA_STATUS_URL, params={"active": str(active).lower()})
    except Exception as e:
        print(f"Camera status update failed: {e}")

def send_push_notification(title, body, token):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token
    )
    try:
        response = messaging.send(message)
        print("Push sent:", response)
    except Exception as e:
        print("Push failed:", e)

def stream_video():
    print("Motion detected — streaming started.")
    update_camera_status(True)
    picam2.start()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    photo_path = os.path.join(PHOTO_DIR, f"dog_{timestamp}.jpg")
    frame = picam2.capture_array()
    cv2.imwrite(photo_path, frame)

    update_notification("Motion detected. Check on your dog.")
    send_push_notification("Motion Detected", "Your dog is active on camera.", FCM_TOKEN)

    for _ in range(100):  # Approx 10 seconds
        frame = picam2.capture_array()
        _, buffer = cv2.imencode('.jpg', frame)
        try:
            requests.post(UPLOAD_URL, files={'frame': ('frame.jpg', buffer.tobytes(), 'image/jpeg')}, timeout=1)
        except Exception as e:
            print(f"Error sending frame: {e}")
        time.sleep(0.1)

    update_notification("No motion. Your dog is probably chilling.")
    send_push_notification("Dog is Calm", "No more motion detected. All is quiet.", FCM_TOKEN)

    picam2.stop()
    update_camera_status(False)

print("Waiting for motion...")
try:
    while True:
        if GPIO.input(PIR_PIN):
            stream_video()
            print("Waiting again...")
            time.sleep(2) 
except KeyboardInterrupt:
    print("Stopped by user.")
finally:
    GPIO.cleanup()
