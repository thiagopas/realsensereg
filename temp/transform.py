import numpy as np
from skimage import transform as tf
import matplotlib.pyplot as plt
import cv2

# estimate transformation parameters
#src = np.array([0, 0, 10, 10]).reshape((2, 2))
src = np.linalg.norm(cv2.imread('C:/2022_07_20_15_53_07+cam0.jpg'), axis=2)
dst = np.linalg.norm(cv2.imread('C:/2022_07_20_15_53_07+cam2.jpg'), axis=2)
dim = (dst.shape[1], dst.shape[0])
src = cv2.resize(src, dim, interpolation=cv2.INTER_AREA)
#dst = np.array([12, 14, 1, -20]).reshape((2, 2))
tform = tf.estimate_transform('similarity', src, dst)
np.allclose(tform.inverse(tform(src)), src)
# warp image using the estimated transformation
from skimage import data
image = data.camera()

plt.imshow(image)

imw = tf.warp(image, inverse_map=tform.inverse) # doctest: +SKIP

# create transformation with explicit parameters
tform2 = tf.SimilarityTransform(scale=1.1, rotation=1, translation=(10, 20))
# unite transformations, applied in order from left to right
tform3 = tform + tform2
np.allclose(tform3(src), tform2(tform(src)))

plt.imshow(imw)