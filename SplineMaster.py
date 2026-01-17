import cv2
import math
from CalibrationRegression import MyCalibRegression as LinearReg
from LineClass import MyLine
from PointClass import MyPoint

import tkinter as tk
from tkinter import simpledialog, messagebox
import tkinter.font as tkfont
from PIL import Image, ImageTk


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


def convert_to_tk_img(opencv_img):  # Converts opencv image to tkinter image
    RGB_img = cv2.cvtColor(opencv_img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB

    # Convert the RGB image (NumPy array) to a PIL Image
    PIL_img = Image.fromarray(RGB_img)

    # convert a PIL Image (or a NumPy array converted to a PIL Image)
    # into a format that can be displayed in a Tkinter GUI application.
    return ImageTk.PhotoImage(PIL_img)


class MySpline:
    def __init__(self, img, edged_img, IMG_SCREEN_RATIO, root):
        self.modeselect = None
        self.img_untouched = img.copy()
        self.original_image = self.img_untouched.copy()
        self.edged_image = edged_img.copy()
        self.clone = self.edged_image.copy()
        self.img_zoom_cache = self.edged_image.copy()  # A cache for a temp img before storing in clone

        self.line_complete = 0

        self.IMG_SCREEN_RATIO = IMG_SCREEN_RATIO

        # Create Tk root
        self.root = root
        # All frames
        self.frame = None
        self.side_frame = None
        self.img_frame = None
        self.button_frame = None
        self.slider_frame = None
        self.display_frame = None

        # For Mode Buttons
        self.ACTIVE_COLOR = "#81C784"  # green
        self.INACTIVE_COLOR = "#E0E0E0"  # default gray
        self.TEXT_ACTIVE = "white"
        self.TEXT_INACTIVE = "black"
        # Dictionary to group the mode buttons
        self.mode_buttons = {}

        # Drawing canvas
        self.drawing_canvas = None

        # To save main tk image and zoom label
        self.tk_main_img = None
        self.zoom_label = None

        # Used to superimpose the original img over the edged img
        self.superimpose_slider = None

        # Used to display events logs and measurement information
        self.event_log_window = None
        self.measure_window = None

        # To keep track of all unique messages and prevent certain
        # messages from repeating on repeat actions
        self._logged_messages = set()

        # Used in slider system
        self.trackbar_value = 0  # To keep track of the slider current value
        self.alpha_slider_max = 100
        self.trackbar_img = self.clone.copy()

        # Font setting for display windows/Tk texts
        self.default_font = tkfont.nametofont("TkDefaultFont")
        self.bold_font = self.default_font.copy()
        self.bold_font.configure(weight="bold")

        # Original line color
        self.orig_line_color = (225, 100, 25, 0.9)

        # vertical and horizontal lines color respectively
        self.vline_color = (0, 0, 225, 0.5)
        self.hline_color = (0, 225, 0, 0.5)

        # List to store start/end points for line
        self.line_starting_point = None
        self.line_ending_point = None
        self.line_dist = None
        self.line_color = None

        self.lines = []

        # List to store points.
        self.points = []
        self.point_color = (0, 255, 255)
        # Used in line calibration calculation.
        # 8 is used as it is the minimum number of sample that statsmodel will allow before throwing a fit.
        self.calibration_lines = []
        self.TOTAL_CALIBRATION_NUM = None  # maximum points set for the regression
        self.MIN_TOTAL_CALIBRATION_NUM = 4  # The mminimum points set or regression. Chosen arbitrarily.
        self.calibration_line_complete = False  # Flag for when calibration line has been completely drawn.
        self.CALIBRATION_COMPLETE = False  # Flag for when calibration of the measurements is complete.
        self.linelen_calib_measure = []
        self.linelen_pixel_measure = []
        # Used to keep one img save for undoing line drawn.
        self.temp_calibration_img = None

        # used in generating the linear relationship
        # between the pixels and mm(millimeters) in real life
        self.lreg = None
        self.__calib_slope = None
        self.__calib_intercept = None

        # Used in line zoom calculation
        self.zoomed_atleast_once = False
        self.zoom = 1
        self.MIN_ZOOM = 1
        self.MAX_ZOOM = 10
        self.new_width = None
        self.new_height = None
        self.x1_offset = None
        self.y1_offset = None
        self.zoomed_xpos = None
        self.zoomed_ypos = None
        self.full_zoomed_OUT_flag = True
        self.full_zoomed_IN_flag = False
        self.zoom_slopex = None
        self.zoom_constantx = None
        self.zoom_slopey = None
        self.zoom_constanty = None

        # Used in tracking if mouse was moved
        self.mouse_moving = False
        self._after_id = None  # stores the after() id so we can cancel it

        # Used to track mouse click x,y position
        self.mouse_xpos = None
        self.mouse_ypos = None

        # Used to track mouse double click x,y position
        self.mouse_dxpos = None
        self.mouse_dypos = None

        # Used in mouse dragging
        self.start_drag = False
        self.mouse_dragging = False
        self.one_line_picked_for_drag = False
        self.closest_mouse_line_id = -1

        # initialize the all frames the main and zoom images
        self.__frames_n_images_init()

        # initialize the side frame widgets
        self.__side_frame_widgets_init()

        # initialize the drawing canvas
        self.__drawing_canvas_init()

        # initialize mouse functions binding
        self.__mouse_binding()

    # Select mode
    def __mode_select(self, mode_selected):
        self.modeselect = mode_selected
        # self.__mouse_drag(event, x, y, flags, parameters)

        if self.modeselect == "Straight Line":  # and not self.mouse_dragging:
            self.log_event("\nStarted Straight Line Measurement Mode", bold=True)
            self.mode_instructions()

        elif self.modeselect == "Points":
            self.__draw_point(event, x, y)

        elif self.modeselect == "Calibration":
            self.log_event("\nStarted Calibration Mode", bold=True)
            self.full_reset_all()
            self.mode_instructions()
            self.__calibration_mode()
            # self.calibration_mode(event, x, y)

        # Clear drawing boxes on right mouse button click
        # if event == cv2.EVENT_RBUTTONDOWN:
        #    self.full_reset_all()

    def __mouse_drag(self, event, x, y, flags, parameters):

        # Finds out if the mouse is close to a drawn line and what line it is.
        mouse_close_to_a_line, closest_line_ID = self.__mouse_is_close_to_a_line(x, y)

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
    def __mouse_is_close_to_a_line(self, mouseX, mouseY):

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
                selected_line.ending_point[1] = int(selected_line.starting_point[1] + selected_line.get_pixel_dist())
            else:
                selected_line.starting_point[0] = int(selected_line.starting_point[0] + displacement[0])
                selected_line.starting_point[1] = mouseY
                selected_line.ending_point[0] = int(selected_line.starting_point[0] + selected_line.get_pixel_dist())
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

    def __draw_line(self, calibration_mode=False):
        # Get mouse (x,y) coordinates on left mouse button double click
        x, y = self.mouse_dxpos, self.mouse_dypos

        self.line_complete += 1
        if self.line_complete == 1:
            # Create the point to make a line
            self.line_starting_point = [x, y]

        # Draw the first point of the line
        radius = 2
        cv2.circle(self.clone, (x, y), radius, [0, 195, 225], 2)
        cv2.circle(self.trackbar_img, (x, y), radius, [0, 195, 225], 2)
        cv2.circle(self.original_image, (x, y), radius, [0, 195, 225], 2)

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
            line_orientation_angle, line_orient = line_orientation(self.line_starting_point,
                                                                   self.line_ending_point)

            # Calculate and Get the length of the line
            line_distance = math.dist(self.line_starting_point, self.line_ending_point)

            # old_starting_point = self.line_starting_point.copy()
            # old_ending_point = self.line_ending_point.copy()

            if line_orient == "Vertical":
                # Changes the line color
                self.line_color = self.vline_color
                # Ensures the vertical lines draws from the top and is contained in the screen
                # If the user draws the line from the starting to the ending point
                if self.line_starting_point[1] < self.line_ending_point[1]:
                    # Draw the line
                    self.line_ending_point[1] = int(self.line_starting_point[1] + line_distance)

                else:
                    # Draw the line backwards
                    self.line_ending_point[1] = int(self.line_starting_point[1] - line_distance)

                # Match the x-axis of the starting and ending points of the lines
                self.line_ending_point[0] = self.line_starting_point[0]

            else:

                # Changes the line color
                self.line_color = self.hline_color
                # Ensures the horizontal lines draws from the side and is contained in the screen
                # If the user draws the line from the starting to the ending point
                if self.line_starting_point[0] < self.line_ending_point[0]:
                    self.line_ending_point[0] = int(self.line_starting_point[0] + line_distance)
                else:
                    # Draw the line backwards
                    self.line_ending_point[0] = int(self.line_starting_point[0] - line_distance)

                # Match the y-axis of the starting and ending points of the lines
                self.line_ending_point[1] = self.line_starting_point[1]

            # Draw the line created on the clone, trackbar and original image.
            cv2.line(self.clone, self.line_starting_point, self.line_ending_point, self.line_color, 2)
            cv2.line(self.trackbar_img, self.line_starting_point, self.line_ending_point, self.line_color, 2)
            cv2.line(self.original_image, self.line_starting_point, self.line_ending_point, self.line_color, 2)

            self.show_image()

            # Store the line
            store_line = MyLine(self.line_starting_point, self.line_ending_point,
                                line_orientation_angle, line_orient,
                                self.line_color)

            if not calibration_mode:
                # Store the line
                self.lines.append(store_line)

                self.log_measurement("-------------------------------------")
                message = "Line Distance (pixels) = " + str(f"{line_distance:.4f}")
                self.log_measurement(message, bullet=True)

                if self.CALIBRATION_COMPLETE:
                    message = "Line Distance(mm) = " + str(f"{self.__pixel_to_mm(line_distance):.4f}")
                    str(f"{self.lreg.get_intercept():.4f}")
                    self.log_measurement(message, bullet=True)

                message = "Angle = " + str(f"{line_orientation_angle:.2f}°")
                self.log_measurement(message, bullet=True)

            else:
                # Flag to show calibration mode is on
                self.calibration_line_complete = True
                self.calibration_lines.append(store_line)

            self.line_starting_point = None
            self.line_ending_point = None
            self.line_color = None
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
            message = 'point {}'.format(self.points[-1].point_coord)
            self.log_measurement(message, bullet=True)

    def __calibration_mode(self):
        if self.TOTAL_CALIBRATION_NUM is None:
            self.temp_calibration_img = self.clone.copy()
            while True:
                try:
                    # Use Tkinter simple dialog box to get the number of calibration lines.
                    self.TOTAL_CALIBRATION_NUM = simpledialog.askinteger(
                        title="Number of Calibration Lines",
                        prompt="Enter the number of calibration lines to use.\n Minimum required: 4\n"
                               "For improved accuracy and statistical stability, 8 or more points are recommended.",
                        parent=self.root
                    )
                    # If the user declines to enter a number of calibration lines...
                    if self.TOTAL_CALIBRATION_NUM is None:
                        # Cancel calibration mode.
                        self.log_event("Calibration mode canceled.", bullet=True)
                        messagebox.showinfo("Calibration Info", "Calibration mode canceled.")
                        self.__update_btns_display(None)
                        self.full_reset_all()
                        return

                    if self.TOTAL_CALIBRATION_NUM < self.MIN_TOTAL_CALIBRATION_NUM:
                        # Tkinter messagebox to show error.
                        messagebox.showerror("Error: Invalid Calibration Input",
                                             "A Minimum of 4 Calibration Lines is Required.")
                    else:
                        break

                except ValueError:
                    messagebox.showerror("Error: Invalid Calibration Input",
                                         f"{self.TOTAL_CALIBRATION_NUM} is not a valid integer.")

        # Do this if a line completely drawn in calibration mode
        if self.calibration_line_complete:
            # For removing calibration measurements and lines.
            remove_calibration = False

            # Get the currrent line drawn
            line_drawn = self.calibration_lines[-1]

            # Append the pixel length of the calibration line
            self.linelen_pixel_measure.append(line_drawn.get_pixel_dist())

            # Get and append the line's length in mm
            real_length = simpledialog.askfloat(
                title="Line Calibration Length",
                prompt="Enter the real-world length of the line (mm):",
                parent=self.root
            )
            # if the user cancels from entering a real length for the line...
            if real_length is None:
                remove_calibration = True
            # or if the user enters a length of 0 for the line's real-world value...
            elif real_length <= 0:
                remove_calibration = True
                messagebox.showerror("Error: Invalid Input",
                                     "The Line length must be greater than 0.")
            else:
                # Update the the temp calibration image.
                self.temp_calibration_img = self.clone.copy()

                # Display the length of the line in pixels
                self.log_measurement("-------------------------------------")
                message = "Line distance in Pixels: " + str(self.linelen_pixel_measure[-1])
                self.log_measurement(message, bullet=True)

                # Append the real length of the calibration line
                self.linelen_calib_measure.append(real_length)

                # Display the length of the line in mm
                message = "Line distance in mm: " + str(self.linelen_calib_measure[-1])
                self.log_measurement(message, bullet=True)

            if remove_calibration:
                messagebox.showinfo("Calibration Line Canceled",
                                    "The last drawn calibration line has been removed.")
                # Revert the shown image to before the last line was drawn.
                self.clone = self.temp_calibration_img.copy()
                self.show_image()
                # if the list is not empty...
                if self.calibration_lines:
                    # Remove the last added calibration line and pixel measurement.
                    self.calibration_lines.pop()
                if self.linelen_calib_measure:
                    # Remove the last added pixel measurement.
                    self.linelen_pixel_measure.pop()

            self.calibration_line_complete = False

        if len(self.calibration_lines) + 1 <= self.TOTAL_CALIBRATION_NUM:
            self.log_event(f"Draw Calibration line No. {len(self.calibration_lines) + 1}...",
                           bullet=True)

        # If the total number of calibration lines is equal to the maximum points set for the regression...
        if len(self.linelen_calib_measure) == self.TOTAL_CALIBRATION_NUM:
            self.CALIBRATION_COMPLETE = True
            # Start the line regression to find the relationship between pixel and mm measurements.
            self.lreg = LinearReg(self.linelen_pixel_measure, self.linelen_calib_measure)
            # self.lreg.show_result()
            unit = "mm"
            # self.log_measurement("-------------------------------------")
            self.log_measurement("===================")
            message = "Estimated Relationship:"
            self.log_measurement(message)
            message = f"1 {unit} = " + str(f"{self.lreg.get_intercept():.4f}") + " + " + str(
                f"{self.lreg.get_slope()}") + " pixel"
            self.log_measurement(message, bold=True)
            # print("Estimated Accuracy: " + str(f"{self.lreg.get_R_squared() * 100:.2f}") + "%")
            message = "Estimated Accuracy: "
            self.log_measurement(message)
            message = str(f"{self.lreg.get_R_squared() * 100:.2f}") + "%"
            self.log_measurement(message, bold=True)
            self.log_measurement("===================\n")
            # Get and store the slope and intercept of the line.
            self.__calib_slope = self.lreg.get_slope()
            self.__calib_intercept = self.lreg.get_intercept()
            # Reset and clear when calibraation is done.
            self.full_reset_all()
            self.log_event("CALIBRATION COMPLETED.", bullet=True)

    def __zoom_img(self, event):
        x, y = event.x, event.y
        flags = event.delta

        print(self._logged_messages)
        # Display zoom factor on event log window
        if self.zoom != self.MIN_ZOOM and self.zoom != self.MAX_ZOOM:
            message = f"Zoom: {int(self.zoom)}X"
            self.log_event(message, True, repeat=False)

        # If Zooming in or out
        zoom_speed = 1.1
        if flags > 0:
            self._logged_messages.discard("MINIMUM ZOOM REACHED")
            self.zoom *= zoom_speed
            self.zoom = min(self.zoom, self.MAX_ZOOM)  # zoom in
            self.full_zoomed_OUT_flag = False

            # discard the previous max zoom factor logged message
            discard_message = f"Zoom: {int(self.zoom) - 1}X"
            self._logged_messages.discard(discard_message)

            if self.zoom == self.MAX_ZOOM:
                self.full_zoomed_IN_flag = True
                self.log_event("MAXIMUM ZOOM REACHED", True, repeat=False)

        else:
            self._logged_messages.discard("MAXIMUM ZOOM REACHED")
            self.zoom /= zoom_speed
            self.zoom = max(self.zoom, self.MIN_ZOOM)  # zoom out
            self.full_zoomed_IN_flag = False

            # discard the previous min zoom factor logged message
            discard_message = f"Zoom: {int(self.zoom) + 1}X"
            self._logged_messages.discard(discard_message)

            if self.zoom == self.MIN_ZOOM:
                self.full_zoomed_OUT_flag = True
                self.log_event("MINIMUM ZOOM REACHED", True, repeat=False)

        img = self.clone.copy()

        # Calculate zoomed-in image size
        self.new_width = round(img.shape[1] / self.zoom)
        self.new_height = round(img.shape[0] / self.zoom)

        # Calculate offset
        self.x1_offset = round(x - (x / self.zoom))
        x2_offset = self.x1_offset + self.new_width

        self.y1_offset = round(y - (y / self.zoom))
        y2_offset = self.y1_offset + self.new_height

        # Crop image
        cropped_img = img[
                      self.y1_offset: y2_offset,
                      self.x1_offset: x2_offset
                      ]

        # Stretch image to full size
        self.img_zoom_cache = cv2.resize(cropped_img, (self.edged_image.shape[1], self.edged_image.shape[0]))
        self.show_image()

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

    # Call when slider is used by user
    def __on_trackbar(self, val):
        self.trackbar_value = float(val)

        # when alpha is max, show original image
        # Vice-versa when beta is max, show trackbar_image
        alpha = self.trackbar_value / self.alpha_slider_max
        beta = (1.0 - alpha)

        # Transition from one image to another based on alpha and beta
        trackbar_transition_img = cv2.addWeighted(self.original_image,
                                                  alpha, self.trackbar_img,
                                                  beta,
                                                  0.0)

        self.clone = trackbar_transition_img.copy()

        # Display the transition
        self.show_image()

    def full_reset_all(self):

        # Reset all global variables
        self.half_reset()

        self.lines = []

        self.full_zoomed_IN_flag = False
        self.full_zoomed_OUT_flag = True

        self.clone = self.edged_image.copy()
        self.trackbar_img = self.clone.copy()
        self.original_image = self.img_untouched.copy()
        self.img_zoom_cache = self.edged_image.copy()
        self.show_image()

    def half_reset(self):
        self.line_starting_point = None
        self.line_ending_point = None
        self.TOTAL_CALIBRATION_NUM = None
        self.calibration_line_complete = False
        self.calibration_lines = []
        self.linelen_calib_measure = []
        self.linelen_pixel_measure = []

    def __frames_n_images_init(self):
        # Window frame setup
        self.frame = tk.Frame(self.root)

        # Change the background color of the frame using configure
        self.frame.configure(bg='lightblue')
        self.frame.pack(fill="both", expand=True)

        # Create a side frame to contain other widget frames
        side_frame_width = (self.IMG_SCREEN_RATIO * self.root.winfo_screenwidth()) - 100
        self.side_frame = tk.Frame(self.frame, width=side_frame_width, bd=1, relief="raised")
        self.side_frame.pack(side="right", fill="y")
        # Keep the side frame to a fixed width. With "True" the side frame shrinks to its contents
        self.side_frame.pack_propagate(False)

        # Create a frame for the main and zoomed images
        img_frame_width = (self.IMG_SCREEN_RATIO * self.root.winfo_screenwidth())
        self.img_frame = tk.Frame(self.frame, width=img_frame_width, bd=1, bg='lightblue')
        self.img_frame.pack(side="left", anchor="n")

        # Create a sub frame for buttons on the side frame
        self.button_frame = tk.Frame(self.side_frame)
        self.button_frame.pack(side=tk.TOP, fill="x", padx=20, pady=(10, 5))

        # Create a sub frame for the slider on the side frame
        self.slider_frame = tk.Frame(self.side_frame)
        self.slider_frame.pack(side=tk.TOP, fill="x", padx=20, pady=(10, 5))

        # Create a sub frame for the display boxes on the side frame
        self.display_frame = tk.Frame(self.side_frame)
        self.display_frame.pack(side=tk.TOP, fill="both", expand=True)

        # Create a label for the zoomed and main images on the window frame
        self.zoom_label = tk.Label(self.img_frame, bd=0, highlightthickness=0)
        self.zoom_label.pack(side=tk.LEFT, padx=10)

    def __drawing_canvas_init(self):
        self.tk_main_img = convert_to_tk_img(self.clone)
        # Create a drawing canvas to allow drawing on the main image
        self.drawing_canvas = tk.Canvas(
            self.img_frame,
            width=self.tk_main_img.width(),
            height=self.tk_main_img.height(),
            bd=0,
            highlightthickness=0
        )
        self.drawing_canvas.pack(side=tk.LEFT)
        self.drawing_canvas.create_image(0, 0, anchor="nw", image=self.tk_main_img, tags="MAIN_IMG")

    def __side_frame_widgets_init(self):

        # Show main menu button and set the button position
        self.mode_buttons["Main Menu"] = tk.Button(self.button_frame,
                                                   text="MAIN MENU",
                                                   bg=self.INACTIVE_COLOR,
                                                   fg=self.TEXT_INACTIVE
                                                   )
        # Puts the button on grid:side-by-side
        self.mode_buttons["Main Menu"].grid(row=0, column=0, sticky="ew", padx=3)

        # Show calibration button and set the button position
        self.mode_buttons["Calibration"] = tk.Button(self.button_frame,
                                                     text="CALIBRATION",
                                                     command=lambda: self.__update_btns_display("Calibration"),
                                                     bg=self.INACTIVE_COLOR,
                                                     fg=self.TEXT_INACTIVE
                                                     )
        self.mode_buttons["Calibration"].grid(row=0, column=1, sticky="ew", padx=3)

        # Show line measurement button and set the button position
        self.mode_buttons["Straight Line"] = tk.Button(self.button_frame,
                                                       text="MEASURE",
                                                       command=lambda: self.__update_btns_display("Straight Line"),
                                                       bg=self.INACTIVE_COLOR,
                                                       fg=self.TEXT_INACTIVE
                                                       )
        self.mode_buttons["Straight Line"].grid(row=0, column=2, sticky="ew", padx=3)

        # Show export button that finishes exports and closes the program
        self.mode_buttons["Export"] = tk.Button(self.button_frame,
                                                text="EXPORT",
                                                bg=self.INACTIVE_COLOR,
                                                fg=self.TEXT_INACTIVE
                                                )
        self.mode_buttons["Export"].grid(row=0, column=3, sticky="ew", padx=3)

        # Make the buttons share space evenly
        self.button_frame.columnconfigure(0, weight=1)  # Main menu button
        self.button_frame.columnconfigure(1, weight=1)  # calibration button
        self.button_frame.columnconfigure(2, weight=1)  # line measurement button
        self.button_frame.columnconfigure(3, weight=1)  # Export button

        # Text widget for slider name
        tk.Label(
            self.slider_frame,
            text="SUPERIMPOSE IMAGES",
            anchor="center"
        ).pack(fill="x", pady=(0, 1))

        # Create a slider for superimposing the original img over the edged img
        self.superimpose_slider = tk.Scale(self.slider_frame,
                                           from_=0, to=100,
                                           orient='horizontal',
                                           length=200,  # width in pixels
                                           bd=2,
                                           relief="raised",
                                           troughcolor="#8fdbc7",
                                           highlightthickness=3,
                                           command=self.__on_trackbar)
        self.superimpose_slider.set(0)

        # Show the slider
        self.superimpose_slider.pack(padx=10)

        # Create a label for the event log window
        tk.Label(
            self.display_frame,
            text="EVENT LOG",
            anchor="center",
            font=self.bold_font
        ).grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 0))

        # Create a event log window
        self.event_log_window = tk.Text(
            self.display_frame,
            height=20,
            wrap="word",
            state="disabled",
            bg="black",
            fg="white"
        )
        self.event_log_window.tag_config("normal", font=self.default_font)
        self.event_log_window.tag_config("bold", font=self.bold_font)
        self.event_log_window.grid(row=1, column=0, sticky="nsew", padx=3)

        # Create a label for the measurement log window
        tk.Label(
            self.display_frame,
            text="MEASUREMENTS",
            anchor="center",
            font=self.bold_font
        ).grid(row=0, column=1, sticky="ew", padx=6, pady=(4, 0))

        # Create a measurement display window
        self.measure_window = tk.Text(
            self.display_frame,
            height=20,
            wrap="word",
            state="disabled",
            bg="black",
            fg="white"
        )
        self.measure_window.tag_config("normal", font=self.default_font)
        self.measure_window.tag_config("bold", font=self.bold_font)
        self.measure_window.grid(row=1, column=1, sticky="nsew", padx=3)

        # Make the display windows share space evenly
        self.display_frame.columnconfigure(0, weight=1)  # Event log label & window
        self.display_frame.columnconfigure(1, weight=1)  # Measurement log window

    def __update_btns_display(self, mode):
        # Change the button background color and text to display
        # the current button selected.
        for name, btn in self.mode_buttons.items():
            if name == mode:
                btn.config(bg=self.ACTIVE_COLOR, fg=self.TEXT_ACTIVE)
            else:
                btn.config(bg=self.INACTIVE_COLOR, fg=self.TEXT_INACTIVE)

        # Call the mode associated the button clicked.
        self.__mode_select(mode)

    def log_event(self, message, bullet=False, bold=False, repeat=True):
        if not repeat and message in self._logged_messages:
            return  # already logged once

        self._logged_messages.add(message)

        self.event_log_window.config(state="normal")

        # Prefix certain messages as though it were bullet points.
        prefix = "- " if bullet else ""
        tag = "bold" if bold else "normal"

        self.event_log_window.insert("end", prefix + message + "\n", tag)
        self.event_log_window.see("end")  # auto-scroll
        self.event_log_window.config(state="disabled")

    def log_measurement(self, message, bullet=False, bold=False):
        self.measure_window.config(state="normal")

        # Prefix certain messages as though it were bullet points.
        prefix = "- " if bullet else ""
        tag = "bold" if bold else "normal"

        self.measure_window.insert("end", prefix + message + "\n", tag)
        self.measure_window.see("end")  # auto-scroll
        self.measure_window.config(state="disabled")

    def __mouse_binding(self):
        self.drawing_canvas.bind("<Button-1>", self.__on_mouse_left_click)
        self.drawing_canvas.bind("<Double-Button-1>", self.__on_double_click)
        self.drawing_canvas.bind("<Motion>", self.__on_mouse_move)
        self.drawing_canvas.bind("<MouseWheel>", self.__on_mousewheel)

    def __on_mouse_left_click(self, event):
        self.mouse_xpos = event.x
        self.mouse_ypos = event.y

    def __on_double_click(self, event):
        self.mouse_dxpos = event.x
        self.mouse_dypos = event.y
        # Update the modes called on double clicking the left mouse button.
        self.update_modes()

    def __on_mouse_move(self, event):
        self.mouse_xpos = event.x
        self.mouse_ypos = event.y
        self.mouse_moving = True

        # Cancel previous timer if exists.
        # root.after_cancel is used to cancel the previous scheduled event.
        # if not the previous scheduled event still executes and mouse_stopped function is called
        # after 100ms.

        if self._after_id is not None:
            self.root.after_cancel(self._after_id)

        # Start a new timer everytime the function: on_mouse_move() is called.
        # self.root.after creates scheduled event in Tk that calls mouse_stopped() function,
        # if the mouse has not moved after 100ms.

        # The method self.root.after returns an identifier that can be used
        # to cancel the scheduled event(mouse_stopped) later.

        # 100ms was arbitrarily chosen.

        self._after_id = self.root.after(100, self.__mouse_stopped)

        #
        if self.zoomed_atleast_once:
            self.__calc_mouse_pos_on_zoom_img(event)
            self.__mouse_move_on_zoom_img()

    def __mouse_stopped(self):
        self.mouse_moving = False
        # clear after_id and allow __on_mouse_move() to cancel
        # the previous scheduled event call.
        self._after_id = None

    def __on_mousewheel(self, event):
        self.zoomed_atleast_once = True
        self.__zoom_img(event)

    def __mouse_move_on_zoom_img(self):
        if self.zoomed_xpos is None or self.zoomed_ypos is None:
            return

        max_radius = 4
        min_radius = 1

        radius = max_radius + (self.zoom - self.MIN_ZOOM) * (
                (min_radius - max_radius) / (self.MAX_ZOOM - self.MIN_ZOOM))
        radius = int(radius)
        # Draw a visual tracking circle to follow the mouse's position on the zoomed image.
        img = self.img_zoom_cache.copy()
        # inner circle
        cv2.circle(self.img_zoom_cache,
                   (self.zoomed_xpos, self.zoomed_ypos),
                   radius,
                   (0, 225, 225),
                   -1)
        # Draw a highlighting outer circle around the main circle
        cv2.circle(self.img_zoom_cache,
                   (self.zoomed_xpos, self.zoomed_ypos),
                   radius,
                   (0, 0, 225),
                   2)
        self.show_image()
        self.img_zoom_cache = img.copy()

        # Takes current mouse x, y pos and returns mouse x, y pos on zoomed img

    def __calc_mouse_pos_on_zoom_img(self, event):
        mouse_xpos, mouse_ypos = event.x, event.y
        # Calculate offset
        x2_offset = self.x1_offset + self.new_width
        y2_offset = self.y1_offset + self.new_height

        # Calculate zoom factors and zoom constants
        fx = (x2_offset - self.x1_offset)
        fy = (y2_offset - self.y1_offset)

        self.zoom_slopex = 1 / fx
        self.zoom_constantx = -self.x1_offset / fx

        self.zoom_slopey = 1 / fy
        self.zoom_constanty = -self.y1_offset / fy

        # Calculate the position of the mouse on the zoomed image
        # to its supposed position on the main image.
        zoom_factorx = self.zoom_slopex * mouse_xpos + self.zoom_constantx
        zoom_factory = self.zoom_slopey * mouse_ypos + self.zoom_constanty

        self.zoomed_xpos = int(zoom_factorx * self.img_zoom_cache.shape[1])
        self.zoomed_ypos = int(zoom_factory * self.img_zoom_cache.shape[0])

    def update_modes(self):
        if self.modeselect == "Straight Line":
            self.__draw_line()
        if self.modeselect == "Calibration":
            self.__draw_line(calibration_mode=True)
            self.__calibration_mode()

    def mode_instructions(self):
        if self.modeselect == "Straight Line":
            self.log_event("Welcome to the Straight Line Measurement Mode.",
                           bullet=True)
            self.log_event("This mode allows linear measurements as shown by the lines drawn.",
                           bullet=True)
            self.log_event("Double click anywhere on the canvas to set the coordinates of the line to be drawn.",
                           bullet=True)
            self.log_event("Use diagonal lines to find angles between two spaces on the canvas.",
                           bullet=True)
            self.log_event("The blue line is the original horizontal line drawn.",
                           bullet=True)
            self.log_event("The red/green line is the adjusted vertical/horizontal line.",
                           bullet=True)

        elif self.modeselect == "Calibration":
            self.log_event("Welcome to the Calibration Mode.",
                           bullet=True)
            self.log_event("This mode uses lines to generate an estimated"
                           " linear relationship bewtween the image pixels and"
                           "real-world values entered(in mm)",
                           bullet=True)
            self.log_event("Double click anywhere on the canvas to set the coordinates of the line to be drawn.",
                           bullet=True)
            self.log_event("The blue line is the original horizontal line drawn.",
                           bullet=True)
            self.log_event("The red/green line is the adjusted vertical/horizontal line.",
                           bullet=True)

    def show_image(self):
        # convert from opencv to tk and show images
        # --MAIN IMAGE--
        self.tk_main_img = convert_to_tk_img(self.clone)

        # Clear ONLY the tagged image
        self.drawing_canvas.delete("MAIN_IMG")

        # Update the drawing canvas
        self.drawing_canvas.create_image(0, 0, anchor="nw", image=self.tk_main_img, tags="MAIN_IMG")

        # --ZOOM IMAGE--
        tk_zoom_img = convert_to_tk_img(self.img_zoom_cache)
        self.zoom_label.config(image=tk_zoom_img)
        self.zoom_label.image = tk_zoom_img  # Keep a reference
