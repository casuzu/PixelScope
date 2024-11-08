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

 #b = np.linspace(1, 10, 10)
# b = [1,2,3,4,5]
# a = [2, 4, 6, 8, 10]
# my_reg = MyCalibRegression(b, a)
# #
# print(my_reg.show_result())
# print("constant = ", my_reg.get_intercept())
# print("slope = ", my_reg.get_slope())
