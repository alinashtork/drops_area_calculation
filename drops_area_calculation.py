# -*- coding: utf-8 -*-
"""Капли_final.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/11DQyuKFRJAUg3wLbNzwQ1_myWllO9UbN
"""

import cv2
import argparse
import seaborn as sns
from matplotlib import pyplot as plt
import numpy as np
import math

from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from scipy import ndimage
import imutils
from keras.preprocessing import image
from PIL import Image as im
from google.colab import files
import csv
import pandas as pd
from google.colab import files

def show_image(img, title):

  plt.figure(figsize=(12, 8))
  plt.title(title)
  plt.imshow(img)
  plt.show()


def contrast_and_blurr(img, blurr_block):
  """
  INPUT:
  img - unprocessed RGB image
  OUTPUT: gray_cs - gray normalized and blurred image
  """
  # turn to gray
  gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# blur
  gray = cv2.GaussianBlur(gray, blurr_block, 0)
# normalization
  gray_cs = cv2.normalize(gray, None, 0, 255.0, cv2.NORM_MINMAX, dtype=cv2.CV_32F)
  gray_cs = cv2.GaussianBlur(gray_cs, blurr_block, 0)

  return gray_cs


def calculate_drops_area(img, photo_number, blockSize, C):
  '''
  INPUT:
  img - preprocessed image
  blockSize - int, odd numbers only, e.x.: 3, 5, 7, ... - pixel neighborhood size for binary segmentation
  C - int, constant to be substracted before binary segmentation

  OUTPUT:
  drop_areas - np.array of shape(k) with calculated areas for each drop
  circularity - np.array of shape(k) with circularity parameters calculated for each drop
  '''

  img = img.astype(np.uint8)
  thresh = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize, C)
  thresh = thresh.astype(np.uint8)
  show_image(thresh, 'binary_image')
  cv2.imwrite('/content/processed_photos/' + str(photo_number + 1) + 'bw' + '.jpg', thresh)

 # detect contours in the mask
  cnts, hier = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
          cv2.CHAIN_APPROX_NONE)

  drop_areas = []
  circularity = []

  for k in range(len(cnts)):
    area = cv2.contourArea(cnts[k]) # contourArea считает площадь области, заключенной в контур
    length = cv2.arcLength(cnts[k], True)

    if area > 6.0:
      circ = 4*math.pi*area/(length**2.0)

      if circ > 0.4:
        drop_areas.append(area)
        circularity.append(circ)

  return drop_areas, circularity

def calculate_for_all_photos(photo_number, blockSize, C, blurr_block):
  '''
  INPUT:
  photo_number - int, number of photos
  blockSize - int, odd numbers only, e.x.: 3, 5, 7, ... - pixel neighborhood size for binary segmentation
  C - int, constant to be substracted before binary segmentation

  OUTPUT:
  photo_numbers - np.array of size (k), photo numbers of each processed drop
  area_all - np.array of size (k), area values for all photos
  circularity_all - np.array of size (k), circularity values of all drops
  '''
  area_all = []
  circularity_all = []
  photo_numbers = []
  for i in range(photo_number):
    name = '/content/' + str(i + 1) + '.jpg'
    img = cv2.imread(name)

    gray_cs = contrast_and_blurr(img, blurr_block)
    show_image(gray_cs, 'enhanced contrast')
    cv2.imwrite('/content/processed_photos/' + str(i + 1) + 'contr' + '.jpg', gray_cs)

    areas, circularity = calculate_drops_area(gray_cs, i, blockSize, C)
    photo_numbers = np.concatenate((photo_numbers, i * np.ones(len(areas))))
    circularity_all = np.concatenate((circularity_all, circularity))
    area_all = np.concatenate((area_all, areas))

    print('Площади капель в пикселях:', areas)
    print('circularity:', circularity)

  return photo_numbers, area_all, circularity_all

# change only these four parameters
photos_number = 10 # total number of photos to be processed
blockSize = 3 # should be an odd number: 3, 5, 7,...
C = -3 # a value to be substracted
blurr_block = (5, 5)

!mkdir processed_photos

photo_numbers, area, circularity = calculate_for_all_photos(photos_number, blockSize, C, blurr_block)

df = pd.DataFrame({'ind': photo_numbers, 'area': area, 'circularity': circularity}, index = None)
df1 = df.groupby('ind').mean()

!zip -r '/content/processed_photos.zip' '/content/processed_photos'
files.download('processed_photos.zip')

df.to_csv('/content/капли_площадь.csv', index=False)
df1