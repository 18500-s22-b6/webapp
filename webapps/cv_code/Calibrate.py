
#ripped from a blog example: https://medium.com/@kennethjiang/calibrate-fisheye-lens-using-opencv-333b05afa0b0

import imp
import cv2
import numpy as np
import os
import glob
import shutil

CHECKERBOARD = (9,9)
#DEFAULT_K = np.array([[743.8653770695429, 0.0, 1251.1764985790337], [0.0, 746.261717085507, 738.7610006363456], [0.0, 0.0, 1.0]])
#DEFAULT_D = np.array([[0.05549035102033457], [0.004777838787067957], [-0.07080456884384306], [0.04316058244944371]])

DEFAULT_K =np.array([[742.6913952508773, 0.0, 1249.548022362481], [0.0, 744.6297639469036, 740.7807175578188], [0.0, 0.0, 1.0]])
DEFAULT_D =np.array([[0.06632647629335793], [-0.05491477933127508], [0.027617545943178893], [-0.007521151402999929]])

DEFAULT_DIM = (2560,1440)

def calibrate(calib_imgs_folder_path = "Calib_imgs"):
    subpix_criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 0.1)
    calibration_flags = cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC+cv2.fisheye.CALIB_CHECK_COND+cv2.fisheye.CALIB_FIX_SKEW
    objp = np.zeros((1, CHECKERBOARD[0]* CHECKERBOARD[1], 3), np.float32)
    objp[0,:,:2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)


    _img_shape = None
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane
    for fname in os.listdir(calib_imgs_folder_path):
        img = cv2.imread(os.path.join(calib_imgs_folder_path, fname))
        if _img_shape == None:
            _img_shape = img.shape[:2]
        else:
            assert _img_shape == img.shape[:2], "All images must share the same size."
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, cv2.CALIB_CB_ADAPTIVE_THRESH+cv2.CALIB_CB_FAST_CHECK+cv2.CALIB_CB_NORMALIZE_IMAGE)
        # If found, add object points, image points (after refining them)
        if ret == True:
            objpoints.append(objp)
            cv2.cornerSubPix(gray,corners,(3,3),(-1,-1),subpix_criteria)
            imgpoints.append(corners)

    if _img_shape == None:
        print("No imgages in calibration folder")
        assert False

    N_OK = len(objpoints)
    K = np.zeros((3, 3))
    D = np.zeros((4, 1))
    rvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]
    tvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]
    if len(objpoints) == 0 or len(imgpoints) == 0 or len(objpoints) != len(imgpoints):
        print("ERROR! no valid files found!")
        assert False


    rms, _, _, _, _ = \
        cv2.fisheye.calibrate(
            objpoints,
            imgpoints,
            gray.shape[::-1],
            K,
            D,
            rvecs,
            tvecs,
            calibration_flags,
            (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6)
        )
    print("K=np.array(" + str(K.tolist()) + ")")
    print("D=np.array(" + str(D.tolist()) + ")")
    return (K, D)

def undistort_img(img, K = DEFAULT_K, D = DEFAULT_D, DIM=DEFAULT_DIM):
    new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(K, D, DIM, np.eye(3), balance=1)
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), new_K, DIM, cv2.CV_16SC2)
    undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
    return undistorted_img

def undistort_img_2(img, K = DEFAULT_K, D = DEFAULT_D, DIM=DEFAULT_DIM):
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), K, DIM, cv2.CV_16SC2)
    undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return undistorted_img

def undistort_imgs(imgs, K, D):
    #takes a list of images, outputs a list of images undistorted.
    #all images must have same deminsion
    outlist  = []
    for img in imgs:
        outlist.append(undistort_img(img, K, D))
    return outlist

def write_to_output(imgs, names, out_dir="Output/undistort_output"):
        #clear existing output directory, if it exists
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    assert len(imgs) == len(names)

    for i in range(len(imgs)):
        cv2.imwrite(os.path.join(out_dir, names[i]), imgs[i])


if __name__ == "__main__":
    (K, D) = calibrate()
    #(K, D) = (DEFAULT_K, DEFAULT_D)
    imgs = [cv2.imread("bg.jpeg")]
    names = ["bg.jpeg"]
    for fname in os.listdir("TopDown"):
        img = cv2.imread(os.path.join("TopDown", fname))
        imgs.append(img)
        names.append(fname)
    undistorted_imgs = undistort_imgs(imgs, K, D)
    write_to_output(undistorted_imgs, names)
