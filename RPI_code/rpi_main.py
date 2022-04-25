import RPi.GPIO as GPIO
import json_post
import time
import picamera

# Change this for each device
SERIAL_ID = "123456"
SECRET = "secretkey"
URL = 'https://b6foodtracker.com'


def my_callback(channel):
    tmp_img_path = "BIN/cur_img.jpeg"
    #take photo


    with picamera.PiCamera() as camera:
        camera.start_preview()
        time.sleep(3)
        camera.capture(f"{tmp_img_path}.jpeg")
        camera.stop_preview()

    #post data
    json_post.post_data(tmp_img_path, SERIAL_ID, SECRET, URL)


if __name__ == "__main__":
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(11, GPIO.FALLING, callback=my_callback, bouncetime=300)

    while True:
        time.sleep(30)
        json_post.post_keepalive(SERIAL_ID, SECRET, URL)


