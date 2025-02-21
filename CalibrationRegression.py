import numpy as np
import statsmodels.api as sm

class MyCalibRegression:
    def __init__(self, pixel_arr, calib_arr):
        self.__calib_arr = np.array(calib_arr, dtype='float32')
        self.__pixel_arr = np.array(pixel_arr, dtype='float32')
        self.__result = self.__do_regression()

    def __do_regression(self):
        x = sm.add_constant(self.__pixel_arr)
        y = self.__calib_arr
        return sm.OLS(y, x).fit()

    def show_result(self):
        print(self.__result.summary())

    def get_intercept(self):
        return self.__result.params[0]

    def get_slope(self):
        return self.__result.params[1]

    def get_R_squared(self):
        return self.__result.rsquared


