import cv2
import math
from CalibrationRegression import MyCalibRegression as LinearReg
from LineClass import MyLine
from PointClass import MyPoint


# This function orientates the line to either a horizontal or vertical orientation.
def line_orientation(point1, point2):
    # Resolve division by zero
    if point2[0] == point1[0]:
        point2[0] += 0.1

    # Get the angle
    angle = math.atan((point2[1] - point1[1]) / (point2[0] - point1[0]))

    # Convert to degrees
    angle_deg = angle * (180 / math.pi)

    # Convert to a vertical or horizontal line
    # Preference is arbitrarily set on "Vertical"
    if abs(math.sin(angle)) >= abs(math.cos(angle)):
        return angle_deg, "Vertical"

    return angle_deg, "Horizontal"


class MySpline:
    def __init__(self, edged_img, img):
        self.modeselect = None
        self.img_untouched = img.copy()
        self.original_image = self.img_untouched.copy()
        self.edged_image = edged_img.copy()
        self.clone = self.edged_image.copy()
        self.img_zoom_cache = self.edged_image.copy()  # A cache for a temp img before storing in clone

        self.line_complete = 0

        # Original line color
        # [0, 195, 225]
        self.orig_line_color = (225, 100, 25, 0.9)

        # vertical and horizontal lines color respectively
        self.vline_color = (0, 0, 225, 0.5)
        # alpha formally = 90
        self.hline_color = (0, 225, 0, 0.5)

        # List to store start/end points for line
        self.line_starting_point = None
        self.line_ending_point = None
        self.line_dist = None
        self.line_color = None
        self.line_orient = None
        self.line_orientation_angle = None

        self.lines = []

        # List to store points.
        self.points = []
        self.point_color = (0, 255, 255)
        # Used in line calibration calculation.
        # 8 is used as it is the minimum number of sample that statsmodel will allow before throwing a fit.
        self.calibration_lines = []
        self.total_calibration_num = 4  # maximum points set for the regression
        self.calibration_line_complete = False  # Flag for when calibration line has been completely drawn.
        self.CALIBRATION_COMPLETE = False  # Flag for when calibration of the measurements is complete.
        self.linelen_calib_measure = []
        self.linelen_pixel_measure = []

        # used in generating the linear relationship
        # between the pixels and mm(millimeters) in real life
        self.lreg = None
        self.__calib_slope = None
        self.__calib_intercept = None

        # Used in line zoom calculation
        self.zoom = 1
        self.MIN_ZOOM = 1
        self.MAX_ZOOM = 7
        self.full_zoomed_OUT_flag = True
        self.full_zoomed_IN_flag = False
        self.zoom_slopex = None
        self.zoom_constantx = None
        self.zoom_slopey = None
        self.zoom_constanty = None

        # Used in trackbar system
        self.trackbar_window_name = "Superimpose Trackbar"
        self.TRACKBR_WINDW_WIDTH = 400
        self.TRACKBR_WINDW_HEIGHT = 40
        self.trackbar_created = False
        self.trackbar_name = "Overlay"
        self.alpha_slider_max = 100
        self.trackbar_img = self.clone.copy()
        self.trackbar_value = 0

        # Used in mouse dragging
        self.start_drag = False
        self.mouse_dragging = False
        self.one_line_picked_for_drag = False
        self.closest_mouse_line_id = -1

        self.IMG_LENGTH, self.IMG_WIDTH = self.edged_image.shape[0], self.edged_image.shape[1]  # 732, 402

        self.count = 0

    def mode(self):
        self.show_image()
        cv2.setMouseCallback('Main Image', self.__mode_select)

    # Select mode
    def __mode_select(self, event, x, y, flags, parameters):

        self.__mouse_drag(event, x, y, flags, parameters)

        if self.modeselect == "Straight Line" and not self.mouse_dragging:
            self.__draw_line(event, x, y)

        elif self.modeselect == "Points":
            self.__draw_point(event, x, y)

        elif self.modeselect == "Calibration":
            self.calibration_mode(event, x, y)

        # Clear drawing boxes on right mouse button click
        if event == cv2.EVENT_RBUTTONDOWN:
            self.reset_all()

        self.zoom_img(event, x, y, flags)

    def __mouse_drag(self, event, x, y, flags, parameters):

        # Finds out if the mouse is close to a drawn line and what line it is.
        mouse_close_to_a_line, closest_line_ID = self.mouse_is_close_to_a_line(x, y)

        # print(f'mouse close to line: {mouse_close_to_a_line}, line_id:{closest_line_ID}')
        # print(f'line_id:{closest_line_ID}')

        # If the mouse left button is held down and the mouse is close to a line...
        if event == cv2.EVENT_LBUTTONDOWN and mouse_close_to_a_line:
            # Flag set for conditions to mouse drag.
            self.start_drag = True

        # if mouse is moved and the dragging conditions are met...
        elif event == cv2.EVENT_MOUSEMOVE and self.start_drag:
            self.mouse_dragging = True

            # If one line selected is being dragged,
            # dont allow another line to be able to be dragged.
            self.one_line_picked_for_drag = True

            # Allow the line to be moved to a new position.
            self.__line_drag(x, y, closest_line_ID)

        # If the mouse left button is released...
        elif event == cv2.EVENT_LBUTTONUP:

            self.one_line_picked_for_drag = False
            self.start_drag = False
            # Turn off mouse dragging.
            self.mouse_dragging = False

    # Function to determine if a mouse is close to a line
    # and what line it is.
    def mouse_is_close_to_a_line(self, mouseX, mouseY):

        # Hyperparameter to show the range around a line that
        # the mouse should be within to flag that the mouse is close emough
        # to said line.
        SHORTEST_MOUSE_TO_LINE_PROXIMITY_RANGE = 3

        # If there is at least 1 line drawn...
        if len(self.lines) >= 1:

            # If no line is currently being dragged...
            if not self.one_line_picked_for_drag:
                # Create a temp shortest distance between the mouse and the line.
                shortest_mouse_line_proximity = 10000

                # Find the line closest to the mouse
                for line in self.lines:
                    # Gets the x and y coordinates of the starting and endind points of the line.
                    x1, y1 = line.starting_point[0], line.starting_point[1]
                    x2, y2 = line.ending_point[0], line.ending_point[1]

                    # Calculate the distance between a point and a line by setting up a
                    # traingle between the line and the mouse point and calcualte the height at
                    # any given mouse coordinate.
                    numerator = math.fabs(mouseX * (y2 - y1) - mouseY * (x2 - x1) + x2 * y1 - y2 * x1)
                    denominator = math.sqrt(math.pow((y2 - y1), 2) + math.pow((x2 - x1), 2))
                    current_mouse_line_proximity = int(numerator / denominator)

                    # Get the line id of the line that is closest to the mouse and its distance away from the mouse
                    if shortest_mouse_line_proximity > current_mouse_line_proximity:
                        shortest_mouse_line_proximity = current_mouse_line_proximity
                        self.closest_mouse_line_id = line.get_id()

                # Return if the mouse is within the accepted line boundary,
                # and the line id of the line it is closest to.
                if shortest_mouse_line_proximity <= SHORTEST_MOUSE_TO_LINE_PROXIMITY_RANGE:
                    # print("shortest_mouse_line_proximity: ", shortest_mouse_line_proximity)
                    return True, self.closest_mouse_line_id
                else:
                    return False, self.closest_mouse_line_id
            else:
                return True, self.closest_mouse_line_id
        else:  # If no line is drawn, the mouse proximity as false and the line id as none.
            return False, None

    # This function drags the line across the screen to the current mouse position.
    # Mouse is held down and the line is dragged.
    def __line_drag(self, mouseX, mouseY, line_id):
        line_index = None
        selected_line = None

        # Find the position and the selected line to be dragged from the lines list using the line ID
        for index, line in enumerate(self.lines):
            if line.get_id() == line_id:
                # Break if the line is found based on ID.
                selected_line = line
                line_index = index
                break

        # If a line is found...
        if line_index is not None:
            # Get the centre of the line
            old_line_centre = [(selected_line.starting_point[0] + selected_line.ending_point[0]) / 2,
                               (selected_line.starting_point[1] + selected_line.ending_point[1]) / 2]
            # Calculate the x and y componets of how far the centre of the old line
            # is from the mouse new position.
            displacement = [mouseX - old_line_centre[0], mouseY - old_line_centre[1]]

            # Change the line starting and ending point based on the line type
            # and the displacement.
            if selected_line.get_type() == "Vertical":
                selected_line.starting_point[0] = mouseX
                selected_line.starting_point[1] = int(selected_line.starting_point[1] + displacement[1])
                selected_line.ending_point[0] = mouseX
                selected_line.ending_point[1] = int(selected_line.starting_point[1] + selected_line.get_line_dist())
            else:
                selected_line.starting_point[0] = int(selected_line.starting_point[0] + displacement[0])
                selected_line.starting_point[1] = mouseY
                selected_line.ending_point[0] = int(selected_line.starting_point[0] + selected_line.get_line_dist())
                selected_line.ending_point[1] = mouseY

            # Store the modified line in the line list.
            self.lines[line_index] = selected_line
            # Redraw all lines(old line and new updated line)
            self.__redraw_lines()
        else:  # If no line was found, make no changes.
            print("No Line present.")

    # Redraws all previous lines to the new canvas\

    def __redraw_lines(self):
        # Reset the canvas back to the original images.
        self.trackbar_img = self.edged_image.copy()
        self.original_image = self.img_untouched.copy()
        self.img_zoom_cache = self.edged_image.copy()

        # Get the trackbar value
        alpha = self.trackbar_value / self.alpha_slider_max
        beta = (1.0 - alpha)

        # Transition from the original no lines image to another image without lines
        # based on alpha and beta
        trackbar_transition_img2 = cv2.addWeighted(self.original_image,
                                                   alpha, self.edged_image,
                                                   beta,
                                                   0.0)

        # Reset clone to the transition image without the lines.
        self.clone = trackbar_transition_img2.copy()

        # Draw all previous lines plus the updated line to the images.
        for line in self.lines:
            # Redraw the lines created on the clone, trackbar and original image.
            cv2.line(self.clone, line.starting_point, line.ending_point, line.get_color(), 2)
            cv2.line(self.trackbar_img, line.starting_point, line.ending_point, line.get_color(), 2)
            cv2.line(self.original_image, line.starting_point, line.ending_point, line.get_color(), 2)

        self.show_image()

    def __draw_line(self, event, x, y, calibration_mode=False):
        # Record starting (x,y) coordinates on left mouse button double click
        if event == cv2.EVENT_LBUTTONDBLCLK:
            self.line_complete += 1
            if self.line_complete == 1:
                # Create the point to make a line
                self.line_starting_point = [x, y]

            # Draw the first point of the line
            cv2.circle(self.clone, (x, y), 1, [0, 195, 225], 2)
            cv2.circle(self.trackbar_img, (x, y), 1, [0, 195, 225], 2)
            cv2.circle(self.original_image, (x, y), 1, [0, 195, 225], 2)

            self.show_image()

        # Record ending (x,y) coordinates on left mouse bottom release

        if self.line_complete == 2:
            # Set the ending point of the line
            self.line_ending_point = [x, y]

            # Original line color
            self.line_color = self.orig_line_color

            # Draw the premodified line created on the clone, trackbar and original image.
            cv2.line(self.clone, self.line_starting_point, self.line_ending_point, self.line_color, 2)
            cv2.line(self.trackbar_img, self.line_starting_point, self.line_ending_point, self.line_color, 2)
            cv2.line(self.original_image, self.line_starting_point, self.line_ending_point, self.line_color, 2)

            # Get the line orientation
            self.line_orientation_angle, self.line_orient = line_orientation(self.line_starting_point,
                                                                             self.line_ending_point)

            # Calculate and Get the length of the line
            self.line_distance = math.dist(self.line_starting_point, self.line_ending_point)

            old_starting_point = self.line_starting_point.copy()
            old_ending_point = self.line_ending_point.copy()

            if self.line_orient == "Vertical":
                # Changes the line color
                self.line_color = self.vline_color
                # Ensures the vertical lines draws from the top and is contained in the screen
                # If the user draws the line from the starting to the ending point
                if self.line_starting_point[1] < self.line_ending_point[1]:
                    # Draw the line
                    self.line_ending_point[1] = int(self.line_starting_point[1] + self.line_distance)

                else:
                    # Draw the line backwards
                    self.line_ending_point[1] = int(self.line_starting_point[1] - self.line_distance)

                # Match the x-axis of the starting and ending points of the lines
                self.line_ending_point[0] = self.line_starting_point[0]

            else:

                # Changes the line color
                self.line_color = self.hline_color
                # Ensures the horizontal lines draws from the side and is contained in the screen
                # If the user draws the line from the starting to the ending point
                if self.line_starting_point[0] < self.line_ending_point[0]:
                    self.line_ending_point[0] = int(self.line_starting_point[0] + self.line_distance)
                else:
                    # Draw the line backwards
                    self.line_ending_point[0] = int(self.line_starting_point[0] - self.line_distance)

                # Match the y-axis of the starting and ending points of the lines
                self.line_ending_point[1] = self.line_starting_point[1]

            # Draw the line created on the clone, trackbar and original image.
            cv2.line(self.clone, self.line_starting_point, self.line_ending_point, self.line_color, 2)
            cv2.line(self.trackbar_img, self.line_starting_point, self.line_ending_point, self.line_color, 2)
            cv2.line(self.original_image, self.line_starting_point, self.line_ending_point, self.line_color, 2)

            self.show_image()

            # Store the line
            store_line = MyLine(self.line_starting_point, self.line_ending_point,
                                self.line_orientation_angle, self.line_orient,
                                self.line_color)

            if not calibration_mode:
                # Store the line
                self.lines.append(store_line)

                print("Line Dist(pixels) = ", self.line_distance)

                if self.CALIBRATION_COMPLETE:
                    print("Line Dist(mm) = ", self.__pixel_to_mm(self.line_distance))

                print("Angle = ", self.line_orientation_angle)
                print(' Previous Starting: {}, Ending: {}'.format(old_starting_point, old_ending_point))
                print('Adjusted Starting: {}, Ending: {}'.format(self.line_starting_point, self.line_ending_point))
                print("-------------------------------------------------------------------")
                print("-------------------------------------------------------------------")
            else:
                # Flag to show calibration mode is on
                self.calibration_line_complete = True
                self.calibration_lines.append(store_line)

            self.line_starting_point = None
            self.line_ending_point = None
            self.line_dist = None
            self.line_color = None
            self.line_orient = None
            self.line_orientation_angle = None
            self.line_complete = 0

    def __draw_point(self, event, x, y):
        if event == cv2.EVENT_LBUTTONUP:
            self.points.append(MyPoint([x, y]))

            # Draw the point created on the clone, trackbar and original image.
            cv2.circle(self.clone, self.points[-1].point_coord, 1, self.point_color, 2)
            cv2.circle(self.trackbar_img, self.points[-1].point_coord, 1, self.point_color, 2)
            cv2.circle(self.original_image, self.points[-1].point_coord, 1, self.point_color, 2)

            self.show_image()
            # print the coordinates of the point to screen.
            print('point {}'.format(self.points[-1].point_coord))

    def calibration_mode(self, event, x, y):
        self.__draw_line(event, x, y, calibration_mode=True)

        # Do this if a line completely drawn in calibration mode
        if self.calibration_line_complete:
            # Get the last line object in calibration_lines
            calibration_line = self.calibration_lines[-1]

            # Append the length of the calibration line
            # self.linelen_pixel_measure.append(math.dist(self.lines_coordinates[-2], self.lines_coordinates[-1]))
            self.linelen_pixel_measure.append(calibration_line.get_line_dist())

            # Display the length of the line in pixels
            print("Line distance in Pixels: ", self.linelen_pixel_measure[-1])

            # Get and append the line's length in mm
            userinput = input("How many millimeters(mm) is this line?: ")
            self.linelen_calib_measure.append(userinput)

            # Display the image
            self.show_image()
            self.calibration_line_complete = False

            # If the total number of calibration lines is equal to the maximum points set for the regression...
            if len(self.linelen_calib_measure) == self.total_calibration_num:
                self.CALIBRATION_COMPLETE = True
                # Start the line regression to find the relationship between pixel and mm measurements.
                self.lreg = LinearReg(self.linelen_pixel_measure, self.linelen_calib_measure)
                # self.lreg.show_result()
                print("========================")
                print("Estimated Relationship: Y = " + str(f"{self.lreg.get_intercept():.4f}") + " + " + str(
                    f"{self.lreg.get_slope():.4f}") + "x")
                print("Estimated Accuracy: " + str(f"{self.lreg.get_R_squared() * 100:.2f}") + "%")
                print("========================")
                # Get and store the slope and intercept of the line.
                self.__calib_slope = self.lreg.get_slope()
                self.__calib_intercept = self.lreg.get_intercept()
                # Reset and clear when calibraation is done.
                self.reset_all()
                print("CALIBRATION COMPLETED.")
                print("Press the 'm' key to return to the main menu.")

    def zoom_img(self, event, x, y, flags):

        # If Zooming in or out
        if event == cv2.EVENT_MOUSEWHEEL:
            zoom_speed = 1.1
            if flags > 0:
                self.zoom *= zoom_speed
                self.zoom = min(self.zoom, self.MAX_ZOOM)  # zoom in
                self.full_zoomed_OUT_flag = False
                if self.zoom == self.MAX_ZOOM:
                    self.full_zoomed_IN_flag = True


            else:
                self.zoom /= zoom_speed
                self.zoom = max(self.zoom, self.MIN_ZOOM)  # zoom out
                self.full_zoomed_IN_flag = False
                if self.zoom == self.MIN_ZOOM:
                    self.full_zoomed_OUT_flag = True

            img = self.clone.copy()

            # Calculate zoomed-in image size
            new_width = round(img.shape[1] / self.zoom)
            new_height = round(img.shape[0] / self.zoom)

            # Calculate offset
            x1_offset = round(x - (x / self.zoom))
            x2_offset = x1_offset + new_width

            y1_offset = round(y - (y / self.zoom))
            y2_offset = y1_offset + new_height

            # Calculate zoom factors and zoom constants
            fx = (x2_offset - x1_offset)
            fy = (y2_offset - y1_offset)

            self.zoom_slopex = 1 / fx
            self.zoom_constantx = -x1_offset / fx

            self.zoom_slopey = 1 / fy
            self.zoom_constanty = -y1_offset / fy

            # Crop image
            cropped_img = img[
                          y1_offset: y2_offset,
                          x1_offset: x2_offset
                          ]

            # Stretch image to full size
            self.img_zoom_cache = cv2.resize(cropped_img, (self.edged_image.shape[1], self.edged_image.shape[0]))
            self.show_image()

        # if the mouse is moving and the image is fully zoomed in...
        if event == cv2.EVENT_MOUSEMOVE and self.full_zoomed_IN_flag:
            # Calculate the position of the mouse on the zoomed image
            # to its supposed position on the main image.
            zoom_factorx = self.zoom_slopex * x + self.zoom_constantx
            zoom_factory = self.zoom_slopey * y + self.zoom_constanty

            zoomed_xpos = int(zoom_factorx * self.edged_image.shape[1])  # factorx * 402 col
            zoomed_ypos = int(zoom_factory * self.edged_image.shape[0])  # factory * 730 row

            # Draw a visual tracking circle to follow the mouse's position on the zoomed image.
            img = self.img_zoom_cache.copy()
            cv2.circle(self.img_zoom_cache, (zoomed_xpos, zoomed_ypos), 3, (255, 255, 0), 3)
            self.show_image()
            self.img_zoom_cache = img.copy()

    # Converts pixel measurement to mm measurement
    # based on slope and intercept gotten from regression.
    def __pixel_to_mm(self, pixel_line_distance):
        return self.__calib_slope * pixel_line_distance + self.__calib_intercept

    def get_edged_img(self):
        return self.clone

    def get_lines(self):
        return self.lines

    def get_points(self):
        return self.points

    # when trackbar is slided by user
    def __on_trackbar(self, val):
        self.trackbar_value = val

        # when alpha is max, show original image
        # Vice-versa when beta is max, show trackbar_image
        alpha = val / self.alpha_slider_max
        beta = (1.0 - alpha)

        # Transition from one image to another based on alpha and beta
        trackbar_transition_img = cv2.addWeighted(self.original_image,
                                                  alpha, self.trackbar_img,
                                                  beta,
                                                  0.0)

        self.clone = trackbar_transition_img.copy()

        # Display the transition
        cv2.imshow('Main Image', self.clone)

    def __create_trackbar(self):
        # create the trackbar on the window
        cv2.createTrackbar(self.trackbar_name, self.trackbar_window_name, 0, self.alpha_slider_max, self.__on_trackbar)

    def show_trackbar(self):
        # Created the named trackbar window
        cv2.namedWindow(self.trackbar_window_name)
        # Resize to the window to a mini size
        cv2.resizeWindow(self.trackbar_window_name, self.TRACKBR_WINDW_WIDTH, self.TRACKBR_WINDW_HEIGHT)
        # If the trackbar has been created once, dont create anymore trackbars
        if not self.trackbar_created:
            self.__create_trackbar()
            self.trackbar_created = True
        # Move the window to the top right side
        cv2.moveWindow(self.trackbar_window_name, 100 + self.IMG_WIDTH + self.TRACKBR_WINDW_WIDTH, 10)

    def reset_all(self):
        # Reset all global variables
        self.line_starting_point = None
        self.line_ending_point = None
        self.line_dist = None
        self.line_color = None
        self.line_orient = None
        self.line_orientation_angle = None

        self.lines = []

        self.linelen_calib_measure = []
        self.linelen_pixel_measure = []

        self.full_zoomed_IN_flag = False
        self.full_zoomed_OUT_flag = True

        self.clone = self.edged_image.copy()
        self.original_image = self.img_untouched.copy()
        self.img_zoom_cache = self.edged_image.copy()
        self.show_image()

    def show_image(self):
        # move and Display the zoom and main images
        cv2.imshow('Zoomed Image', self.img_zoom_cache)
        cv2.imshow('Main Image', self.clone)
        cv2.moveWindow('Zoomed Image', 100, 10)
        cv2.moveWindow('Main Image', 100 + self.IMG_WIDTH, 10)

        cv2.waitKey(1)
