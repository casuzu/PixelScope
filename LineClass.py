import math


class MyLine:
    line_id = 0

    def __init__(self, starting_point, ending_point, angle, line_type, line_color):
        MyLine.line_id += 1
        self._id = MyLine.line_id
        self.starting_point = starting_point
        self.ending_point = ending_point
        self._line_dist = None
        self._color = line_color
        self._type = line_type
        self._angle = angle

        self.calculate_line_dist()

    def calculate_line_dist(self):
        self._line_dist = math.dist(self.starting_point, self.ending_point)

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

