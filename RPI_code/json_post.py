from sqlite3 import Timestamp
import requests
import webbrowser
import base64

TIMESTAMP_INT = 0

def post_data(img_path, serialId, secret, url):
    url = url + "/update_inventory"
    with open(img_path, "rb") as f:
        im_bytes = f.read()
    im_serialized_b64 = base64.b64encode(im_bytes).decode("utf8")
    headers = {'Content-Type': 'application/json'}
    global TIMESTAMP_INT
    TIMESTAMP_INT = TIMESTAMP_INT + 1
    resp = requests.post(url, headers= headers, json={"image": im_serialized_b64, "serial_number": serialId, "secret": secret, "timestamp": TIMESTAMP_INT})
    with open("resp_data.html", "w") as f:
        f.write(resp.text)

    if "success" in resp.json():
        print("success: {}".format(resp.json()['success']))
    elif "error" in resp.json():
        print("error: {}".format(resp.json()['error']))
    else:
        print("failed!")

def post_keepalive(img_path, serialId, secret, url):
    url = url + "/keep_alive"
    headers = {'Content-Type': 'application/json'}

    resp = requests.post(url, headers= headers, json={ "serial_number": serialId, "secret": secret})
    with open("resp_keepalive.html", "w") as f:
        f.write(resp.text)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-I', '--image', help='path to image', default="BIN/c1.jpeg")
    args = parser.parse_args()
    post_data(args.image, "123456", "secretkey", 'http://localhost:8000')

