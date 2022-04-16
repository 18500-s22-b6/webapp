from asyncio import open_unix_connection
from email.mime import image
import imp
import os
import numpy as np
import pandas as pd
import cv2 as cv
from scipy import stats
import matplotlib.pyplot as plt
import math
from skimage.metrics import structural_similarity as compare_ssim
import time
import copy
import diff
import Calibrate
import base64

N_DESC = 1000

#These will need to be redone individually, should be fine for basic tesing rn
BB_dict = {
    "Apple": ((261, 542), (470,770)),
    "Bannana": ((185, 470), (570,850)),
    "Cereal": ((0, 0), (768,1024)), #this one especially
    "Cheese brick": ((200, 450), (490, 770)),
    "Cheese Log": ((230, 520), (500,850)),
    "Cheese wedge": ((90, 460), (550,880)),
    "Eggs": ((0, 0), (768,1024)), #this one especially
    "Milk": ((0, 0), (768,1024)), #this one especially
    "Oranges": ((280, 600), (500,810)),
    "Yogurt": ((160, 445), (500,835)),
}

#reads all the images (non-grayscale)
def read_images():
    image_dir = os.path.join(os.getcwd(), "Images")
    image_class_folders = os.listdir(image_dir)
    out_dict = dict()
    for image_class in image_class_folders:
        if image_class == ".DS_Store":
            continue
        real_list = []
        iconic_list = []
        #read real images
        real_path = os.path.join(image_dir, image_class, "Real")
        for image in os.listdir(real_path):
            image_path = os.path.join(real_path, image)
            real_list.append(cv.imread(image_path, 1))
        #read iconic images
        iconic_path = os.path.join(image_dir, image_class, "Iconic")
        for image in os.listdir(iconic_path):
            image_path = os.path.join(iconic_path, image)
            iconic_list.append(cv.imread(image_path, 1))

        out_dict[image_class] = (iconic_list, real_list)

    return out_dict


def test_alg(alg, matcher):
    images_dict = read_images()

    #get kp/desc for each image
    desc_dict = {}
    for image_class, images in images_dict.items():
        real_list = []
        iconic_list = []
        iconic_images, real_images = images
        for iconic_image in iconic_images:
            key_points = alg.detect(iconic_image, None)
            key_points, descriptors = alg.compute(iconic_image, key_points)
            iconic_list.append(descriptors)
        for real_image in real_images:
            key_points = alg.detect(real_image, None)
            key_points, descriptors = alg.compute(real_image, key_points)

            real_list.append((key_points, descriptors))
        desc_dict[image_class] = (iconic_list, real_list)

    #compile combined descriptors list
    matches_dict = {}
    for image_class, descriptors in desc_dict.items():
        if image_class not in BB_dict:
            import pdb; pdb.set_trace()
        bounds = BB_dict[image_class]
        lbound = bounds[0][0]
        rbound = bounds[1][0]
        topbound = bounds[0][1]
        botbound = bounds[1][1]
        iconic_descriptors, real_descriptors = descriptors

        #sanity check
        if len(iconic_descriptors) == 0:
            print("Image class " + image_class + " has no iconic images")
            assert False
        elif len(real_descriptors) == 0:
            print("Image class " + image_class + " has no real images")
            assert False

        all_iconic_descriptors = np.concatenate(iconic_descriptors, axis=0)

        match_percentage = []
        #check each of the images against the contatenation of all the descriptors
        for (cur_image_real_keypoints, cur_image_real_descriptors) in real_descriptors:
            assert len(cur_image_real_keypoints) == len(cur_image_real_descriptors)
            matches = matcher.match(all_iconic_descriptors, cur_image_real_descriptors)
            cor_matches = 0
            for match in matches:
                match_kp = cur_image_real_keypoints[match.trainIdx]
                if lbound <= match_kp.pt[0] <= rbound and topbound <= match_kp.pt[1] <= botbound:
                    cor_matches = cor_matches + 1
                else:
                    pass
                    # print(match_kp.pt)
            print(image_class + str(cor_matches/len(matches)))
            match_percentage.append(cor_matches/len(matches))

        matches_dict[image_class] = match_percentage
    return matches_dict

#pretty prints the stuff so I can throw it in a google sheet
def to_info(matches_dict):
    # return
    for image_class, match_percentages in matches_dict.items():
        print(image_class, stats.describe(np.array(match_percentages)))


def test_sanity(alg, matcher, image_class, kp_detector=None):

    #read arbitrary real/iconic images
    image_dir = os.path.join(os.getcwd(), "Images")
    real_path = os.path.join(image_dir, image_class, "Real")
    real_image_path = os.path.join(real_path, os.listdir(real_path)[2])
    img1 = cv.imread(real_image_path, 1)

    iconic_path = os.path.join(image_dir, image_class, "Iconic")
    iconic_image_path = os.path.join(iconic_path, os.listdir(iconic_path)[0])
    img2 = cv.imread(iconic_image_path, 1)

    # section = cv.imread("/Users/keatondrebes/Desktop/cv_code/Images/Scratch/Screen Shot 2022-02-20 at 12.40.04 PM.png", 1)
    # icon = cv.imread("/Users/keatondrebes/Desktop/cv_code/Images/Cereal/Iconic/Cereal_Iconic_1.jpg", 1)
    # img1 = section
    # img2 = icon

    if kp_detector == None:
        kp1, des1 = alg.detectAndCompute(img1,None)
        kp2, des2 = alg.detectAndCompute(img2,None)
    else:
        kp1 = kp_detector.detect(img1,None)
        kp2 = kp_detector.detect(img1,None)
        des1 = alg.compute(img1, kp1)
        des2 = alg.compute(img2, kp2)


    matches = matcher.match(des1,des2)
    # Draw first matches.
    img3 = cv.drawMatches(img1,kp1,img2,kp2,matches,None,flags=cv.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

    plt.imshow(img3),plt.show()

def compare_2_imgs(img1, img2, alg, matcher, kp_detector=None):
    #read arbitrary real/iconic images

    if kp_detector == None:
        kp1, des1 = alg.detectAndCompute(img1,None)
        kp2, des2 = alg.detectAndCompute(img2,None)
    else:
        kp1 = kp_detector.detect(img1,None)
        kp2 = kp_detector.detect(img1,None)
        des1 = alg.compute(img1, kp1)
        des2 = alg.compute(img2, kp2)

    # import pdb; pdb.set_trace()
    matches = matcher.match(des1,des2)
    # Draw first matches.
    img3 = cv.drawMatches(img1,kp1,img2,kp2,matches,None,flags=cv.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

    plt.imshow(img3),plt.show()

    # find_item(alg, matcher, img1, img2)



def read_testing_images():
    """ """
    outlist = []
    image_dir = os.path.join(os.getcwd(), "Test_Images")
    for image_name in os.listdir(image_dir):
        image_path = os.path.join(image_dir, image_name)
        outlist.append(cv.imread(image_path, 1))
    return outlist




expected_dict = {
    "1.jpeg": {
        "Apple": 1,
        "Bannana": 0,
        "Cereal": 1,
        "Cheese brick": 1,
        "Cheese Log": 1,
        "Cheese wedge": 1,
        "Eggs": 0,
        "Milk": 0,
        "Oranges": 1,
        "Yogurt": 1,
    },
    "2.jpeg": {
        "Apple": 1,
        "Bannana": 0,
        "Cereal": 0,
        "Cheese brick": 1,
        "Cheese Log": 1,
        "Cheese wedge": 0,
        "Eggs": 0,
        "Milk": 0,
        "Oranges": 1,
        "Yogurt": 1,
    },
    "3.jpeg": {
        "Apple": 0,
        "Bannana": 0,
        "Cereal": 1,
        "Cheese brick": 1,
        "Cheese Log": 0,
        "Cheese wedge": 1,
        "Eggs": 0,
        "Milk": 1,
        "Oranges": 0,
        "Yogurt": 0,
    },
    "4.jpeg": {
        "Apple": 0,
        "Bannana": 1,
        "Cereal": 1,
        "Cheese brick": 0,
        "Cheese Log": 1,
        "Cheese wedge": 1,
        "Eggs": 0,
        "Milk": 1,
        "Oranges": 0,
        "Yogurt": 1,
    },
    "5.jpeg": {
        "Apple": 1,
        "Bannana": 1,
        "Cereal": 1,
        "Cheese brick": 1,
        "Cheese Log": 1,
        "Cheese wedge": 1,
        "Eggs": 1,
        "Milk": 1,
        "Oranges": 1,
        "Yogurt": 1,
    },
    "6.jpeg": {
        "Apple": 1,
        "Bannana": 0,
        "Cereal": 1,
        "Cheese brick": 1,
        "Cheese Log": 1,
        "Cheese wedge": 0,
        "Eggs": 0,
        "Milk": 0,
        "Oranges": 1,
        "Yogurt": 1,
    }
}

def test_cluttered(alg, matcher):
    """runs a test to see which items are ID'd with a cluttered background containing multiple of the target objects"""

    img_dict = read_images()
    test_img_list = read_testing_images()

    class_to_descriptors_dict = {}

    for image_class, (iconic_imgs, _) in img_dict.items():
        cur_descriptors = []
        for iconic_img in iconic_imgs:
            kp1, des1 = alg.detectAndCompute(iconic_img,None)
            cur_descriptors.append(des1)

        class_to_descriptors_dict[image_class] = np.concatenate(cur_descriptors, axis=0)



    #for each image, check how many classes of each item can be located
    for i in range(len(test_img_list)):
        img = test_img_list[i]
        expected = expected_dict[f"{i+1}.jpeg"]
        found = img_to_num_each_item(alg, matcher, class_to_descriptors_dict, img)
        misses = 0
        for item_class, num_expected in expected.items():
            if 0 != abs(num_expected - found[item_class]):
                print(f"{i+1}.jpeg expected {num_expected} {item_class}. Found {found[item_class]}.")
                misses = misses + abs(num_expected - found[item_class])

        print(f"     {misses} total misses for {i+1}.jpeg")





def img_to_num_each_item(alg, matcher, class_to_desc_map, img):
    """takes an image, and a maping of image class -> descriptors. Returns a dict containing the number of items of each type found in the image"""

    out_dict = {}
    for image_class, descriptors in class_to_desc_map.items():
        out_dict[image_class] = find_item(alg, matcher, descriptors, img)
    return out_dict

def find_item(alg, matcher, target_desc, img):
    """take decriptors, and an item. returns true if the item can be found int he img"""
    real_kp, real_dp = alg.detectAndCompute(img,None)

    # FLANN_INDEX_KDTREE = 1
    # index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    # search_params = dict(checks = 50)
    # flann = cv.FlannBasedMatcher(index_params, search_params)
    # matches = flann.knnMatch(target_desc,real_dp,k=2)

    bf = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(target_desc, real_dp, k=2) # knnMatch is crucial

    # store all the good matches as per Lowe's ratio test.
    ratio = .7
    good = []
    good_kp = []
    for m,n in matches:
        if m.distance < ratio*n.distance:
            good.append(m)
            # import pdb; pdb.set_trace()
            good_kp.append(real_kp[m.queryIdx])

    cv.drawKeypoints(img, good_kp, img, color=(0,0,0), flags=cv.DRAW_MATCHES_FLAGS_DRAW_OVER_OUTIMG)
    plt.imshow(img),plt.show()
    return good




def read_keypoints_descriptors(alg, kp_detector):
    #get kp/desc for each image
    desc_dict = {}
    t = time.time()
    images_dict = read_images()
    t2 = time.time()
    for image_class, images in images_dict.items():
        real_list = []
        iconic_list = []
        iconic_images, real_images = images
        print(f"CLASS: {image_class}")
        for iconic_image in iconic_images:
            t_foo = time.time()
            if kp_detector is None:
                key_points = alg.detect(iconic_image, None)
            else:
                key_points = kp_detector.detect(iconic_image,None)

            #Try except for diagnosing problems
            try:
                key_points, descriptors = alg.compute(iconic_image, key_points)
            except:
                import pdb; pdb.set_trace()
            iconic_list.append((key_points,descriptors))
            print(f"PLX_BE_BAD: {t_foo - time.time()}")
        for real_image in real_images:
            t_foo = time.time()
            if kp_detector is None:
                key_points = alg.detect(real_image, None)
            else:
                key_points = kp_detector.detect(iconic_image,None)

            #Try except for diagnosing problems
            try:
                key_points, descriptors = alg.compute(real_image, key_points)
            except:
                import pdb; pdb.set_trace()
            real_list.append((key_points, descriptors))
            print(f"PLX_BE_BAD_real: {t_foo - time.time()}")
        desc_dict[image_class] = (iconic_list, real_list)
    t3 = time.time()
    print(f"read: {t2 - t}")
    print(f"kp/desc: {t3 - t2}")

    return desc_dict

class AlgInfo:
    #convenient class for packaging info
    def __init__(self, image_class, num_descriptors_in_iconic, good_matches_dict):
        self.image_class = image_class
        self.num_descriptors_in_iconic = num_descriptors_in_iconic
        self.good_matches_dict = good_matches_dict

    def get_self_matches(self):
        return self.good_matches_dict[self.image_class]


def perform_pairwise_comparisons_arbitrary(iconic_dict, target_dict):
    #perform pairwise comparison between every image in the iconic dict, and every image in the target dict
    #target dict must be formattd image_name -> kp/descriptors
    #output is a dict of image image_name -> {iconic_image class: (len(total_iconic_descriptors, num_matching_descriptors)}
    #used for actually generating best guesses of image classes
    output_dict = {}
    matcher = cv.BFMatcher(cv.NORM_L1,crossCheck=False)
    for target_image_name, target_image_kp_descriptors in target_dict.items():
        target_class_descriptors = target_image_kp_descriptors[1]

        good_matches_dict = {}
        #check each of the images against the contatenation of all the descriptors
        for iconic_image_class, iconic_class_kp_descriptors in iconic_dict.items():
            _, all_iconic_descriptors = iconic_class_kp_descriptors
            matches = matcher.knnMatch(target_class_descriptors, all_iconic_descriptors, k=2) # knnMatch is needed
            good = 0
            for (m1, m2) in matches: # for every descriptor, take closest two matches
                if m1.distance < 0.7 * m2.distance: # best match has to be this much closer than second best
                    good = good + 1
            good_matches_dict[iconic_image_class] = (len(all_iconic_descriptors), good)

        output_dict[target_image_name] = good_matches_dict
    return output_dict

def perform_pairwise_comparisons_labeled(iconic_dict, target_dict):
    #perform pairwise comparison between every image in the iconic dict, and every image in the target dict
    #target dict must be formatted image_class -> kp_descriptors
    #used for constructing the confusion matrix
    alg_info_dict = {}
    matcher = cv.BFMatcher(cv.NORM_L1,crossCheck=False)
    for iconic_image_class, iconic_class_kp_descriptors in iconic_dict.items():
        _, all_iconic_descriptors = iconic_class_kp_descriptors

        good_matches_dict = {}
        #check each of the images against the contatenation of all the descriptors
        for target_image_class, target_image_kp_descriptors in target_dict.items():
            target_class_descriptors = target_image_kp_descriptors[1]
            # import pdb; pdb.set_trace()
            # np.asarray(, np.float32())
            matches = matcher.knnMatch(target_class_descriptors, all_iconic_descriptors, k=2) # knnMatch is needed
            good = 0
            for (m1, m2) in matches: # for every descriptor, take closest two matches
                if m1.distance < 0.7 * m2.distance: # best match has to be this much closer than second best
                    good = good + 1
            good_matches_dict[target_image_class] = good

        alg_info_dict[iconic_image_class] = AlgInfo(iconic_image_class,len(all_iconic_descriptors),good_matches_dict)
    return alg_info_dict



def alg_info_dict_to_excel(alg_info_dict, alg_name = ""):
    #helper function, takes a dict of algInfo's, and produces a

    keys_list = list(alg_info_dict.keys())
    num_found_df = pd.DataFrame(columns=keys_list, index = [None])

    num_matched_df = pd.DataFrame(index = keys_list, columns=keys_list)

    for iconic_image_class, alg_info in alg_info_dict.items():
        num_found_df[iconic_image_class] = alg_info.num_descriptors_in_iconic
        for target_img_class, num_match in alg_info.good_matches_dict.items():
            num_matched_df[iconic_image_class][target_img_class] = num_match
    with pd.ExcelWriter("output.xlsx", engine="openpyxl", mode = "a", if_sheet_exists= "replace") as writer:
        num_found_df.to_excel(excel_writer = writer, sheet_name=f"{alg_name}_num_descriptors_found")
        num_matched_df.to_excel(excel_writer = writer, sheet_name=f"{alg_name}_num_matched")

        num_matched_df_2 = num_matched_df.copy()

        for iconic_image_class, alg_info in alg_info_dict.items():
            num_matched_df[iconic_image_class] = num_matched_df[iconic_image_class] / alg_info.num_descriptors_in_iconic

        num_matched_df.to_excel(excel_writer = writer, sheet_name=f"{alg_name}_ratio_matched")

        for iconic_image_class, alg_info in alg_info_dict.items():
            if num_matched_df_2[iconic_image_class].max() == 0:
                num_matched_df_2[iconic_image_class] = -1
                num_matched_df[iconic_image_class] = -1
            else:
                num_matched_df_2[iconic_image_class] = (num_matched_df_2[iconic_image_class].max() - num_matched_df_2[iconic_image_class]) / num_matched_df_2[iconic_image_class].max()
                num_matched_df[iconic_image_class] = (num_matched_df[iconic_image_class].max() - num_matched_df[iconic_image_class]) / num_matched_df[iconic_image_class].max()

        num_matched_df.to_excel(excel_writer = writer, sheet_name=f"{alg_name}_delta_ratio_matched")
        num_matched_df_2.to_excel(excel_writer = writer, sheet_name=f"{alg_name}_delta_num_matched")

def read_images_desc_subfolder(folder_name, alg=None, bg_img=None):
    """reads labeled images from a given subfolder, and creates a map for image type to a tuple of
    (keypoints, descriptors).
    Raises an error if not exactly 1 image is found in the given subfolder.
    if bg_img is not none, will do pixel diff using the bg_img, and take the largest found diff
    """
    if alg == None:
        #default to SIFT since that did the best
        alg = cv.xfeatures2d.SIFT_create(N_DESC)

    image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Images")
    image_class_folders = os.listdir(image_dir)
    out_dict = dict()
    for image_class in image_class_folders:
        if image_class == ".DS_Store":
            continue
        subfolder_path = os.path.join(image_dir, image_class, folder_name)
        if len(os.listdir(subfolder_path)) != 1:
            print(f"Didn't find exactly one image in subfolder {subfolder_path}")
            assert False
        for image_filename in os.listdir(subfolder_path):
            image_path = os.path.join(subfolder_path, image_filename)
            raw_img = cv.imread(image_path, 1)
            if not (bg_img is None):
                (_, raw_img) = diff.get_largest_dif(bg_img, raw_img)
                cv.imshow('after', raw_img)
            key_points = alg.detect(raw_img,None)
            kp, desc = alg.compute(raw_img, key_points)
            out_dict[image_class] = (kp, desc)

    return out_dict

def read_images_desc_folder(folder_name, alg=None, bg_img=None, needs_undistort = True):
    """reads images from a given subfolder, and creates a map of image name -> a tuple of
    (keypoints, descriptors).
    """
    if alg == None:
        #default to SIFT since that did the best
        alg = cv.xfeatures2d.SIFT_create(N_DESC)

    out_dict = dict()
    if bg_img is not None and needs_undistort:
        bg_img = Calibrate.undistort_img(bg_img)
    for img_name in os.listdir(folder_name):
        if img_name == ".DS_Store":
            continue
        image_path = os.path.join(folder_name, img_name)
        raw_img = cv.imread(image_path, 1)
        if needs_undistort:
            raw_img = Calibrate.undistort_img(raw_img)
        if not (bg_img is None):
            (_, raw_img) = diff.get_largest_dif(bg_img, raw_img)
            cv.imshow('after', raw_img)
        key_points = alg.detect(raw_img,None)
        kp, desc = alg.compute(raw_img, key_points)
        out_dict[img_name] = (kp, desc)

    return out_dict



def test_images_labeled(target_subfolder_name, iconic_subfolder_path="Iconic", bg_path = "bg.jpeg"):
    #tests a set of images that have been labeled against every iconic image, to build a confusion matrix
    iconic_dict = read_images_desc_subfolder(iconic_subfolder_path)
    real_cropped_dict = read_images_desc_subfolder(target_subfolder_name, alg = None, bg_img = cv.imread(bg_path))
    return perform_pairwise_comparisons_labeled(iconic_dict, real_cropped_dict)


def test_arbitrary_images(target_subfolder_name="TopDown", iconic_subfolder_path="Iconic", bg_path = "bg.jpeg"):
    #tests a set of arbitrary images
    iconic_dict = read_images_desc_subfolder(iconic_subfolder_path)
    target_dict = read_images_desc_folder(target_subfolder_name)
    matches_dict = perform_pairwise_comparisons_arbitrary(iconic_dict,target_dict)
    #get best guess for each img

    best_guess_dict = dict()
    for img_name, iconic_map in matches_dict.items():
        best_guess = ""
        best_guess_ratio = -1
        for iconic_img, (num_total_desc, num_matches) in iconic_map.items():
            if num_matches/num_total_desc > best_guess_ratio:
                best_guess = iconic_img
                best_guess_ratio = num_matches/num_total_desc

        best_guess_dict[img_name] = best_guess

    print("Best Guesses:")
    for img_name, best_guess in sorted(best_guess_dict.items()):
        print(f"{img_name}: {best_guess}")

def get_best_guess_or_none(bg_image_path, new_image_path, additional_iconic_classes, items_already_present_in_shelf = None):
    """
    This is the only function that should be called externally to this module.
    Takes a path to the bg image, the new image, and a optional
    dict mapping additionally registered item names --> iconic image path.

    Returns the best guess for the image, or None if it isn't known with enough
    certainty (IE, need to ask user for clarification).
    """

    alg = cv.xfeatures2d.SIFT_create(N_DESC)

    new_img = Calibrate.undistort_img(cv.imread(new_image_path, 1))
    bg_image = Calibrate.undistort_img(cv.imread(bg_image_path, 1))


    iconic_dict = read_images_desc_subfolder("Iconic")

    #add additionally supplied iconic classes
    for new_iconic_name, new_iconic_img_path in additional_iconic_classes.items():
        img = cv.imread(new_iconic_img_path, 1)
        key_points = alg.detect(img,None)
        kp, desc = alg.compute(img, key_points)
        iconic_dict[new_iconic_name] = (kp, desc)

    (pre_dif, post_diff) = diff.get_largest_dif(bg_image, new_img)
    target_dict = dict()

    #If we don't have a large enough diff, there probably wasn't a change
    if pre_dif.shape[0] * pre_dif.shape[1] < 100:
        return None

    for img, img_name in [(pre_dif, "pre_dif"), (post_diff, "post_diff")]:
        key_points = alg.detect(img,None)
        kp, desc = alg.compute(img, key_points)
        target_dict[img_name] = (kp, desc)


    matches_dict = perform_pairwise_comparisons_arbitrary(iconic_dict,target_dict)

    best_guess_dict = dict()
    for img_name, iconic_map in matches_dict.items():
        best_guess = ""
        best_guess_ratio = -1
        for iconic_img, (num_total_desc, num_matches) in iconic_map.items():
            if num_matches/num_total_desc > best_guess_ratio:
                best_guess = iconic_img
                best_guess_ratio = num_matches/num_total_desc

        best_guess_dict[img_name] = best_guess

    #TODO: have some heuristic check when somthing is removed rather than added
    if False:
        return best_guess_dict["post_diff"]
    else:
        #if we couldn't identify it, return the diff
        return post_diff





if __name__ == "__main__":
    out = test_arbitrary_images("TopDown", bg_path="bg2.jpeg")
    # alg_info_dict_to_excel(out, f"SIFT_{subfolder_name}_test")

    # orb = cv.ORB_create(nfeatures=10000)
    # fast = cv.FastFeatureDetector_create()
    # brief = cv.xfeatures2d.BriefDescriptorExtractor_create() #needs independent kp detector
    # alg = sift
    # alg_name = "SIFT"
    # star_detector = cv.xfeatures2d.StarDetector_create()
    # kp_detector = None

    # # matcher = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=True)
    # # cv.BFMatcher(cv2.NORM_L1,crossCheck=False)
    # # matcher = cv.BFMatcher()
    # #cv.knnmatcher(k=2)
    # t = time.time()
    # print(f"TOTAL: {time.time() - t}")
    # alg_info_dict_to_excel(alg_info, alg_name)

    # print(to_info(test_alg(alg, matcher)))

    # test_sanity(alg, matcher, "Milk")

    # orig = cv.imread("/Users/keatondrebes/Desktop/cv_code/Images/Scratch/9E0128E5-D98F-45D5-8107-A09CCC9D2786_1_105_c.jpeg", cv.IMREAD_GRAYSCALE)
    # bg = cv.imread("/Users/keatondrebes/Desktop/cv_code/Images/Scratch/72AB2A58-5CA5-4249-9CF6-390F17BE476B_1_105_c.jpeg", cv.IMREAD_GRAYSCALE)
    # section = cv.imread("/Users/keatondrebes/Desktop/cv_code/Images/Scratch/Screen Shot 2022-02-20 at 1.12.26 PM.png", cv.IMREAD_GRAYSCALE)
    # icon = cv.imread("/Users/keatondrebes/Desktop/cv_code/Images/Cereal/Iconic/Cereal_Iconic_1.jpg", cv.IMREAD_GRAYSCALE)

    # compare_2_imgs(icon, section, alg, matcher)

    # test_cluttered(alg, matcher)
    # import pdb; pdb.set_trace()


# matches = bf.knnMatch(desCam, desTrain, k=2) # knnMatch is crucial
# good = []
# for (m1, m2) in matches: # for every descriptor, take closest two matches
#     if m1.distance < 0.7 * m2.distance: # best match has to be this much closer than second best
#         good.append(m1)
