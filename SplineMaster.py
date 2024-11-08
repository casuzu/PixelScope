import cv2
import math
from CalibrationRegression import MyCalibRegression as LinearReg
from LineClass import MyLine


# This function checks if two images are equal and returns true if they are and false if not.
def check_images_are_equal(image_1, image_2):
    # Check if the images are the same size, return false if not.
    if image_1.shape == image_2.shape:

        # Get the difference between the two images. The result is an image itself.
        # Any resulting negative pixel is return as 0 to keep in range(0, 255)
        difference = cv2.subtract(image_1, image_2)

        # Split the difference image into number of BGR values
        b, g, r = cv2.split(difference)

        # if all of the total BGR values for the difference image result in 0,
        # there is no difference and the images are equal
        if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
            return True
        else:
            return False
    else:
        # if the images are not the same size
        return False


class MySpline:
    def __init__(self, edged_img, img):
        self.modeselect = None
        self.img_untouched = img.copy()
        self.original_image = self.img_untouched.copy()
        self.edged_image = edged_img.copy()
        self.clone = self.edged_image.copy()
        self.img_zoom_cache = self.edged_image.copy()#A cache for a temp img before storing in clone


        self.line_complete = 0
        self.calibration_line_complete = False

        #vertical and horizontal lines color respectively
        self.vline_color = (0, 0, 225, 0.5)
        self.hline_color = (0, 225, 0, 90)

        # List to store start/end points for line
        self.lines = []
        self.lines_coordinates = []
        self.vlines_coord = []
        self.hlines_coord = []

        # List to store points
        self.points_coordinates = []

        #Used in line calibration calculation
        #8 is used as it is the minimum number of sample that statsmodel will allow before throwing a fit.
        self.TOTAL_CALIBRATION_NUM = 4
        self.CALIBRATION_COMPLETE = False
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
        self.MAX_ZOOM = 5
        self.full_zoomed_OUT_flag = True
        self.full_zoomed_IN_flag = False
        self.zoom_slopex = None
        self.zoom_constantx = None
        self.zoom_slopey = None
        self.zoom_constanty = None

        #Used in trackbar system
        self.trackbar_window_name = "Superimpose Trackbar"
        self.TRACKBR_WINDW_WIDTH = 400
        self.TRACKBR_WINDW_HEIGHT = 40
        self.trackbar_created = False
        self.trackbar_name = "Overlay"
        self.alpha_slider_max = 100
        self.trackbar_img = self.clone.copy()


        #Used in mouse dragging
        self.mouse_dragging = False

        self.IMG_LENGTH, self.IMG_WIDTH = self.edged_image.shape[0], self.edged_image.shape[1] #732, 402

        self.count = 0
    def mode(self):
        self.show_image()
        cv2.setMouseCallback('Main Image', self.__mode_select)





    # Select mode between drawing straight lines or points
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


        self.zoom_img( event, x, y, flags)


    def __mouse_drag(self, event, x, y, flags, parameters):
        mouse_close_to_a_line, closest_line = self.mouse_is_close_to_a_line(x, y)


        if event == cv2.EVENT_LBUTTONDOWN and mouse_close_to_a_line:
            self.mouse_dragging = True


        elif event == cv2.EVENT_MOUSEMOVE:
            if self.mouse_dragging:
                self.line_drag(x, y)


        elif event == cv2.EVENT_LBUTTONUP:
            self.mouse_dragging = False


    def mouse_is_close_to_a_line(self, mouseX, mouseY):
        SHORTEST_MOUSE_TO_LINE_PROXIMITY = 20
        if len(self.lines_coordinates)> 1:
            shortest_mouse_line_pos = 0
            mouse_line_proximity = math.dist((mouseX, mouseY), self.lines_coordinates[0])
            for i in range(0, len(self.lines_coordinates), 2):
                current_mouse_line_proximity = math.dist((mouseX, mouseY), self.lines_coordinates[i])
                if mouse_line_proximity > current_mouse_line_proximity:
                    mouse_line_proximity = current_mouse_line_proximity
                    shortest_mouse_line_pos = i


            if mouse_line_proximity < SHORTEST_MOUSE_TO_LINE_PROXIMITY:
                return True, shortest_mouse_line_pos
            else:
                return False, shortest_mouse_line_pos
        else:
            return False, 0



    def line_drag(self, mouseX, mouseY):
        print("x dragging")




    def __line_orientation(self):
        point1, point2 = self.lines_coordinates[-2], self.lines_coordinates[-1]
        #point1, point2 = self.lines[-1].starting_point, self.lines[-1].ending_point
        if point2[0] == point1[0]:
            point2[0] += 0.1

        #Get the angle
        angle = math.atan( (point2[1] - point1[1]) / (point2[0] - point1[0]))
        #angle = -angle
        angle_deg = angle * (180 / math.pi)
        #print("angle = ", angle * (180 / math.pi))


        if abs(math.sin(angle)) >= abs(math.cos(angle)):
            return angle_deg, "Vertical"


        return angle_deg, "Horizontal"



    def __draw_line(self, event, x, y, calibration_mode = False):

        # Record starting (x,y) coordinates on left mouse button click
        if event == cv2.EVENT_LBUTTONDOWN and not self.mouse_dragging:
            print("mouse dragging:", self.mouse_dragging)
            self.line_complete += 1
            ##if self.line_complete == 1:
                #Create the next line
                #self.lines.append(MyLine([x, y]))
            ##
            self.lines_coordinates.append([x, y])
            ##

            cv2.circle(self.clone, (x, y), 2, [0, 195, 225], 2)
            cv2.circle(self.trackbar_img, (x, y), 2, [0, 195, 225], 2)
            cv2.circle(self.original_image, (x, y), 2, [0, 195, 225], 2)

            self.show_image()

        # Record ending (x,y) coordinates on left mouse bottom release
        elif event == cv2.EVENT_LBUTTONUP:

           # self.line_complete += 1

            if self.line_complete == 2:

                #Add the ending point for the line
                #self.lines[-1].set_ending_point([x, y])
                #Get orientation
                ##
                orientation_angle, orientation = self.__line_orientation()
                #self.lines[-1].set_angle(orientation_angle)
                #self.lines[-1].set_type(orientation)

                # Draw line
                ##
                line_distance = math.dist(self.lines_coordinates[-2], self.lines_coordinates[-1])

                #line_distance = self.lines[-1].set_line_dist()
                previous_point1, previous_point2 = self.lines_coordinates[-2], self.lines_coordinates[-1]
                #previous_point1, previous_point2 = self.lines[-1].starting_point, self.lines[-1].ending_point
                if orientation == "Vertical":
                    #Ensures the vertical lines draws from the top and is contained in the screen
                    #Changes the line color
                    line_color = self.vline_color
                    if int(self.lines_coordinates[-2][1] + line_distance) < self.IMG_LENGTH:
                        self.lines_coordinates[-1][1] = int(self.lines_coordinates[-2][1] + line_distance)
                    else:
                        self.lines_coordinates[-1][1] = int(self.lines_coordinates[-2][1] - line_distance)
                    self.lines_coordinates[-1][0] = self.lines_coordinates[-2][0]
                    self.vlines_coord.append(self.lines_coordinates[-2])
                    self.vlines_coord.append(self.lines_coordinates[-1])
                else:
                    # Ensures the horizontal lines draws from the top and is contained in the screen
                    # Changes the line color
                    line_color = self.hline_color
                    if int(self.lines_coordinates[-2][0] + line_distance) < self.IMG_WIDTH:
                        self.lines_coordinates[-1][0] = int(self.lines_coordinates[-2][0] + line_distance)
                    else:
                        self.lines_coordinates[-1][0] = int(self.lines_coordinates[-2][0] - line_distance)
                    self.lines_coordinates[-1][1] = self.lines_coordinates[-2][1]
                    self.hlines_coord.append(self.lines_coordinates[-2])
                    self.hlines_coord.append(self.lines_coordinates[-1])


                cv2.line(self.clone, self.lines_coordinates[-2], self.lines_coordinates[-1], line_color, 2)
                cv2.line(self.trackbar_img, self.lines_coordinates[-2], self.lines_coordinates[-1], line_color, 2)
                cv2.line(self.original_image, self.lines_coordinates[-2], self.lines_coordinates[-1], line_color, 2)
                self.show_image()


                self.line_complete = 0
                if not calibration_mode:
                    print("Line Dist(pixels) = ", line_distance)

                    if self.CALIBRATION_COMPLETE:
                        print("Line Dist(mm) = ", self.__pixel_to_mm(line_distance))

                    print("Angle = ", orientation_angle)
                    print(' Previous Starting: {}, Ending: {}'.format(previous_point1, previous_point2))
                    print('Adjusted Starting: {}, Ending: {}'.format(self.lines_coordinates[-2], self.lines_coordinates[-1]))
                    print("-------------------------------------------------------------------")
                    print("-------------------------------------------------------------------")
                else:
                    #Flag to show calibration mode is on
                    self.calibration_line_complete = True


    def __draw_point(self, event, x, y):
        if event == cv2.EVENT_LBUTTONUP:
            self.points_coordinates.append([x, y])

            cv2.circle(self.clone, (x, y), 2, [0, 255, 255], 2)
            cv2.circle(self.trackbar_img, (x, y), 2, [0, 255, 255], 2)
            cv2.circle(self.original_image, (x, y), 2, [0, 255, 255], 2)
            self.show_image()
            print('point {}'.format(self.points_coordinates[-1]))

            # Record ending (x,y) coordinates on left mouse bottom release


    def calibration_mode(self, event, x, y):
        self.__draw_line(event, x, y, calibration_mode = True)

        #Do this if a line completely drawn in calibration mode
        if self.calibration_line_complete:
            self.linelen_pixel_measure.append(math.dist(self.lines_coordinates[-2], self.lines_coordinates[-1]))
            print("Line distance in Pixels: ", self.linelen_pixel_measure[-1])

            #print("How many millimeters(mm) is this line?: ")
            userinput = input("How many millimeters(mm) is this line?: ")
            self.linelen_calib_measure.append(userinput)

            #xpoints = np.array([1, 8])
            #ypoints = np.array([3, 10])

            #plt.plot(self.linelen_pixel_measure, self.linelen_calib_measure, 'o')
            #plt.show()
            self.show_image()
            self.calibration_line_complete = False

            if len(self.linelen_calib_measure) == self.TOTAL_CALIBRATION_NUM:
                self.CALIBRATION_COMPLETE = True
                self.lreg = LinearReg(self.linelen_pixel_measure, self.linelen_calib_measure)
                self.lreg.show_result()
                self.__calib_slope = self.lreg.get_slope()
                self.__calib_intercept= self.lreg.get_intercept()
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


            img= self.clone.copy()


            # Calculate zoomed-in image size
            new_width = round(img.shape[1] / self.zoom)
            new_height = round(img.shape[0] / self.zoom)

            # Calculate offset
            x1_offset = round(x - (x / self.zoom))
            x2_offset = x1_offset + new_width

            y1_offset = round(y - (y / self.zoom))
            y2_offset = y1_offset + new_height

            #Calculate zoom factors and zoom constants
            fx = (x2_offset - x1_offset)
            fy = (y2_offset - y1_offset)

            self.zoom_slopex = 1/fx
            self.zoom_constantx = -x1_offset/fx

            self.zoom_slopey = 1/fy
            self.zoom_constanty = -y1_offset/fy


            # Crop image
            cropped_img = img[
                          y1_offset: y2_offset,
                          x1_offset: x2_offset
                          ]




            # Stretch image to full size
            self.img_zoom_cache = cv2.resize(cropped_img, (self.edged_image.shape[1], self.edged_image.shape[0]))
            self.show_image()

        if event == cv2.EVENT_MOUSEMOVE and self.full_zoomed_IN_flag:
            zoom_factorx = self.zoom_slopex * x + self.zoom_constantx
            zoom_factory = self.zoom_slopey * y + self.zoom_constanty

            zoomed_xpos = int(zoom_factorx * self.edged_image.shape[1]) #factorx * 402 col
            zoomed_ypos = int(zoom_factory * self.edged_image.shape[0]) #factory * 730 row

            img = self.img_zoom_cache.copy()
            cv2.circle(self.img_zoom_cache, (zoomed_xpos, zoomed_ypos), 3, (255, 255, 0), 3)
            self.show_image()
            self.img_zoom_cache = img.copy()



    def __pixel_to_mm(self, pixel_line_distance):
        return self.__calib_slope*pixel_line_distance + self.__calib_intercept
    def get_lines_coord(self):
        return self.lines_coordinates

    def get_v_lines_coord(self):
        return self.vlines_coord

    def get_h_lines_coord(self):
        return self.hlines_coord
    def get_points_coord(self):
        return self.points_coordinates

    def undo_point(self):
        if self.modeselect == "Points":
           if not self.points_coordinates:
               print("NO POINT ADDED.")

    #when trackbar is slided by user
    def __on_trackbar(self, val):
        #when alpha is max, show original image
        #Vice-versa when beta is max, show trackbar_image
        alpha = val / self.alpha_slider_max
        beta = (1.0 - alpha)

        #Transition from one image to another based on alpha and beta
        transition_img = cv2.addWeighted(self.original_image, alpha, self.trackbar_img, beta, 0.0)

        self.clone = transition_img.copy()

        #Display the transition
        cv2.imshow('Main Image', self.clone)

    def __create_trackbar(self):
        cv2.createTrackbar(self.trackbar_name, self.trackbar_window_name, 0, self.alpha_slider_max, self.__on_trackbar)

    def show_trackbar(self):
        #Created the named trackbar window
        cv2.namedWindow(self.trackbar_window_name)
        #Resize to the window to a mini size
        cv2.resizeWindow(self.trackbar_window_name, self.TRACKBR_WINDW_WIDTH, self.TRACKBR_WINDW_HEIGHT)
        #If the trackbar has been created once, dont create anymore trackbars
        if not self.trackbar_created:
            self.__create_trackbar()
            self.trackbar_created = True
        #Move the window to the top right side
        cv2.moveWindow(self.trackbar_window_name, 100 + self.IMG_WIDTH + self.TRACKBR_WINDW_WIDTH, 10)

    def reset_all(self):
        self.lines_coordinates = []
        self.vlines_coord = []
        self.hlines_coord = []
        self.points_coordinates = []

        self.linelen_calib_measure = []
        self.linelen_pixel_measure = []

        self.full_zoomed_IN_flag = False
        self.full_zoomed_OUT_flag = True

        self.clone = self.edged_image.copy()
        self.original_image = self.img_untouched.copy()
        self.img_zoom_cache = self.edged_image.copy()
        self.show_image()

    def show_image(self):

        cv2.imshow('Zoomed Image', self.img_zoom_cache)
        cv2.imshow('Main Image', self.clone)
        cv2.moveWindow('Zoomed Image', 100, 10)
        cv2.moveWindow('Main Image', 100 + self.IMG_WIDTH, 10)



        cv2.waitKey(1)


