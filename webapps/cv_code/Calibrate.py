
#ripped from a blog example: https://medium.com/@kennethjiang/calibrate-fisheye-lens-using-opencv-333b05afa0b0

import imp
import cv2
import numpy as np
import os
import glob
import shutil

CHECKERBOARD = (9,9)
DEFAULT_K = np.array([[743.8653770695429, 0.0, 1251.1764985790337], [0.0, 746.261717085507, 738.7610006363456], [0.0, 0.0, 1.0]])
DEFAULT_D = np.array([[0.05549035102033457], [0.004777838787067957], [-0.07080456884384306], [0.04316058244944371]])

# This works (?)
# DEFAULT_K =np.array([[742.6913952508773, 0.0, 1249.548022362481], [0.0, 744.6297639469036, 740.7807175578188], [0.0, 0.0, 1.0]])
# DEFAULT_D =np.array([[0.06632647629335793], [-0.05491477933127508], [0.027617545943178893], [-0.007521151402999929]])

#this is new 1
# DEFAULT_K=np.array([[743.9841536598568, 0.0, 1255.1819694061348], [0.0, 745.7531930733501, 746.6257774805962], [0.0, 0.0, 1.0]])
# DEFAULT_D=np.array([[0.0541884417527263], [-0.016897523441291227], [-0.016183500977269633], [0.007281230890118444]])

#This is new 2
# DEFAULT_K=np.array([[745.4902362620558, 0.0, 1250.9057081475266], [0.0, 748.2672546064653, 751.6694651847206], [0.0, 0.0, 1.0]])
# DEFAULT_D=np.array([[0.05638557181140707], [-0.013063034851805202], [-0.025757067190665884], [0.011481165227825604]])


#This is manually changed
# DEFAULT_K =np.array([[742.6913952508773, 0.0, 1249.548022362481], [0.0, 744.6297639469036, 740.7807175578188], [0.0, 0.0, 1.0]])
# DEFAULT_D =np.array([[0.06632647629335793], [-0.05491477933127508], [0.027617545943178893], [0.007521151402999929]])

#This is new 3
# DEFAULT_K=np.array([[743.9841536598568, 0.0, 1255.1819694061348], [0.0, 745.7531930733501, 746.6257774805962], [0.0, 0.0, 1.0]])
# DEFAULT_D=np.array([[0.0541884417527263], [-0.016897523441291227], [-0.016183500977269633], [0.007281230890118444]])

#This is new 4
DEFAULT_K=np.array([[746.2606029864031, 0.0, 1253.3039943785554], [0.0, 747.8303962022748, 746.8804295390603], [0.0, 0.0, 1.0]])
DEFAULT_D=np.array([[0.054508147613983864], [-0.018423201337080013], [-0.0158574863044052], [0.007230470980964623]])

#This is new 5
# DEFAULT_K=np.array([[746.6611669643795, 0.0, 1258.0834963310779], [0.0, 746.7693228265135, 748.2604564297882], [0.0, 0.0, 1.0]])
# DEFAULT_D=np.array([[0.04818181468970269], [-0.012787709242349402], [-0.016624091910845094], [0.006814930852439065]])

#This is the final version, I havn't really been able to fix the full distortion of the image, but it'll have to do for now
# DEFAULT_K=np.array([[746.205011008588, 0.0, 1259.599390114775], [0.0, 746.3719965670107, 751.7773066350132], [0.0, 0.0, 1.0]])
# DEFAULT_D=np.array([[0.0557504888972436], [-0.025822106030366027], [-0.007766810011750379], [0.004721292292724637]])

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
    new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(K, D, DIM, np.eye(3), balance=.3)
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
    # (K, D) = calibrate()
    (K, D) = (DEFAULT_K, DEFAULT_D)
    imgs = [cv2.imread("bg.jpeg")]
    names = ["bg.jpeg"]
    targetDir = "Bin2"
    for fname in os.listdir(targetDir):
        img = cv2.imread(os.path.join(targetDir, fname))
        imgs.append(img)
        names.append(fname)
    undistorted_imgs = undistort_imgs(imgs, K, D)
    write_to_output(undistorted_imgs, names)
