import numpy as np
class ImageEnhancement():

    def __init__(self,method):
        self.method = method


    def _hist_equalization(self):




    def _imagej_BC(self):




    def _min_max_normalization(img):
        array_img = np.array(img)
        maxValue = max(array_img)
        minValue = min(array_img)
        enhanced_image = (array_img - minValue)/(maxValue - minValue + 0.0001)
        return enhanced_image


    def _log_enhancement(self):

