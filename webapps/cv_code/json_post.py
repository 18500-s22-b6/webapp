import requests
import webbrowser
import base64


def post_data(img_path, serialId, secret):
    url = 'http://localhost:8000/update_inventory'
    with open(img_path, "rb") as f:
        im_bytes = f.read()
    im_serialized_b64 = base64.b64encode(im_bytes).decode("utf8")
    headers = {'Content-Type': 'application/json'}
    #TODO: how to do some sort of back exponential backoff here?
    resp = requests.post(url, headers= headers, json={"image": im_serialized_b64, "serial_number": serialId, "secret": secret})
    with open("resp.html", "w") as f:
        f.write(resp.text)

    if "success" in resp.json():
        print("success: {}".format(resp.json()['success']))
    elif "error" in resp.json():
        print("error: {}".format(resp.json()['error']))
    else:
        print("failed!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-I', '--image', help='path to image', default="BIN/c1.jpeg")
    args = parser.parse_args()
    post_data(args.image, "123456", "secretkey")

