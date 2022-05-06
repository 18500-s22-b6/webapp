
import imp
from skimage.metrics import structural_similarity
import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import shutil
import math

def do_blur_diff(bg_img, new_img):
    # grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    # grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)

    ksize = (10, 10)
    bg_img = cv2.blur(bg_img, ksize)
    new_img = cv2.blur(new_img, ksize)

    diff = cv2.subtract(new_img, bg_img)
    thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # cnts = imutils.grab_contours(cnts)
    plt.imshow(bg_img),plt.show()
    cv2.imshow("Original", bg_img)
    cv2.imshow("Diff", diff)
    plt.imshow(diff),plt.show()
    return diff

def find_largest_diff_bounds(before, after):
    # ripped from stack overflow:
    # https://stackoverflow.com/questions/56183201/detect-and-visualize-differences-between-two-images-with-opencv-python

    # returns the bounding rectangle around the largest difference found between the before and after images
    # in the form of (x,y,w,h)
    # Convert images to grayscale

    before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
    after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

    # Compute SSIM between two images
    (score, diff) = structural_similarity(before_gray, after_gray, full=True)
    # print("Image similarity", score)

    # The diff image contains the actual image differences between the two images
    # and is represented as a floating point data type in the range [0,1]
    # so we must convert the array to 8-bit unsigned integers in the range
    # [0,255] before we can use it with OpenCV
    diff = (diff * 255).astype("uint8")

    # Threshold the difference image, followed by finding contours to
    # obtain the regions of the two input images that differ
    thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    mask = np.zeros(before.shape, dtype='uint8')
    filled_after = after.copy()

    largest_contour = None
    largest_contour_size = 0
    for c in contours:
        area = cv2.contourArea(c)
        if area > 40:
            x,y,w,h = cv2.boundingRect(c)
            # cv2.rectangle(before, (x, y), (x + w, y + h), (36,255,12), 2)
            # cv2.rectangle(after, (x, y), (x + w, y + h), (36,255,12), 2)
            # cv2.drawContours(mask, [c], 0, (0,255,0), -1)
            # cv2.drawContours(filled_after, [c], 0, (0,255,0), -1)
            if area > largest_contour_size:
                largest_contour_size = area
                largest_contour = c

    # cv2.imshow('before', before)
    # cv2.imshow('after', after)
    # cv2.imshow('diff',diff)
    # cv2.imshow('mask',mask)
    # cv2.imshow('filled after',filled_after)
    # cv2.waitKey(0)
    (x,y,w,h) = cv2.boundingRect(largest_contour)

    cropped_before_avrg = np.average(before[y:y+h, x:x+w])
    cropped_after_avrg = np.average(after[y:y+h, x:x+w])

    blur_dim = 50
    kernel = np.ones((blur_dim,blur_dim),np.float32)/(blur_dim * blur_dim)
    if len(before[y:y+h, x:x+w]) == 0:
        return (x,y,w,h)
    croped_before_blured = cv2.filter2D(before[y:y+h, x:x+w],-1,kernel)
    cropped_after_blured = cv2.filter2D(after[y:y+h, x:x+w],-1,kernel)

    diff_averg = np.average(croped_before_blured - cropped_after_blured)

    #somewhere between 3 and 5 likely good based on initial testing
    #This completly screwed over in more rigorous tesing, so I'm setting it to 0
    total_avg_thresh = 0
    dif_averg_thresh = 0

    if abs(cropped_before_avrg - cropped_after_avrg) < total_avg_thresh or diff_averg < dif_averg_thresh:
        #return inconsequential cropped region
        return (2,2,1,1)

    return (x,y,w,h)


def get_largest_dif(before, after, return_bounds = False):
    """returns a tuple.
    The first element is the subsection of the before image that contains the largest diff,
    the second is the subsection of the after images"""
    (x,y,w,h) = find_largest_diff_bounds(before, after)
    croped_before_img = before[y:y+h, x:x+w]
    cropped_after_img = after[y:y+h, x:x+w]
    if return_bounds:
        return (croped_before_img, cropped_after_img, (x,y,w,h))
    else:
        return (croped_before_img, cropped_after_img)

def get_largest_dif_folder(before_file_path, after_folder_path, keep_before=False, out_dir = "Output/dif_output"):

    #clear existing output directory, if it exists
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)


    before = cv2.imread(before_file_path)
    for img_name in os.listdir(after_folder_path):
        after = cv2.imread(os.path.join(after_folder_path, img_name))
        (cropped_before_img, cropped_after_img) = get_largest_dif(before, after)
        if keep_before and not len(cropped_before_img) > 0:
            cv2.imwrite(os.path.join(out_dir, img_name), cropped_before_img)
        elif len(cropped_after_img) > 0:
            cv2.imwrite(os.path.join(out_dir, img_name), cropped_after_img)




if __name__ == "__main__":
    get_largest_dif_folder("/Users/keatondrebes/Desktop/webapp/webapps/cv_code/Bin2/cur_img67.jpeg", "Bin2")






# from PIL import Image, ImageChops
# import matplotlib.pyplot as plt
# import skimage.io
# import matplotlib.pyplot as plt
# import skimage.filters


# def img_diff(img1, img2):
#     sigma= 3.0
#     skimage.filters.gaussian(img1, sigma=(sigma, sigma), truncate=3.5, multichannel=True)
#     skimage.filters.gaussian(img2, sigma=(sigma, sigma), truncate=3.5, multichannel=True)
#     return ImageChops.difference(img2, img1)


# if __name__ == "__main__":
#     # img1 = Image.open("Test_Images/arm.jpeg")
#     # img2 = Image.open("Test_Images/empty.jpeg")
#     img1 = skimage.io.imread("Test_Images/arm.jpeg")
#     img2 = skimage.io.imread("Test_Images/arm.jpeg")
#     diff = img_diff(img1, img2)
#     plt.imshow(diff),plt.show()
#     print("done")
