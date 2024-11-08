import math


class MyLine:
    line_id = 0

    def __init__(self, starting_point):
        self._id = self.line_id + 1
        self._starting_point = starting_point
        self._ending_point = None
        self._line_dist = 0
        self._color = None
        self._type = None
        self._angle =None


    def set_starting_point(self, new_starting_point):
        self._starting_point = new_starting_point

    def get_starting_point(self):
        return self._starting_point

    def set_ending_point(self, new_ending_point):
        self._ending_point = new_ending_point

    def get_ending_point(self):
        return self._ending_point

    def set_line_dist(self):
        self._line_dist = math.dist(self._starting_point, self._ending_point)

    def get_line_dist(self):
        return self._line_dist

    def set_color(self, new_color):
        self._color = new_color

    def get_color(self):
        return self._color

    def set_type(self, new_type):
        self._type = new_type

    def get_type(self):
        return self._type

    def set_angle(self, new_angle):
        self._angle = new_angle

    def get_angle(self):
        return self._angle

    def get_id(self):
        return self._id

