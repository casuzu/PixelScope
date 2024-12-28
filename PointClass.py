class MyPoint:
    point_id = 0

    def __init__(self, point_coord):
        self._id = self.point_id + 1
        self.point_coord = point_coord
        self._color = None
