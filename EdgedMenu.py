import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

#Create the display window and title
root = tk.Tk()
root.title("Edged Image Maker")

SCREEN_WIDTH = root.winfo_screenwidth()
SCREEN_HEIGHT = root.winfo_screenheight()

root.minsize(SCREEN_WIDTH, SCREEN_HEIGHT)

def convert_to_tk_img(opencv_img): #Converts opencv image to tkinter image
    RGB_img = cv2.cvtColor(opencv_img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB

    # Convert the RGB image (NumPy array) to a PIL Image
    PIL_img = Image.fromarray(RGB_img)

    # convert a PIL Image (or a NumPy array converted to a PIL Image)
    # into a format that can be displayed in a Tkinter GUI application.
    return ImageTk.PhotoImage(PIL_img)

def convert_to_opencv_img(tk_image): #Converts tkinter image to opencv image
    # Convert Tkinter PhotoImage to PIL Image
    pil_image = ImageTk.getimage(tk_image)

    # Convert PIL Image to NumPy array
    open_cv_image = np.array(pil_image)

    # Convert RGB to BGR
    open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

    return open_cv_image


def close_window(event=None): #Close the display window and ends the program
    root.destroy()

class MyEdgedImageMaker:
    def __init__(self, img_screen_ratio):

        #Original Image
        self.IMG_SCREEN_RATIO = img_screen_ratio
        self.img_label = None

        #Edged Image
        self.edged_img_label = None

        self.img_target_size = None

        # The values for canny low and high thresholds were choosen experimentally.
        self.canny_low_threshold = 40
        self.canny_high_threshold = 100

        self.file_path_default = "Filepath not found Cat.jpeg"
        self.img_file_path = ""
        self.edged_img_file_path = ""



    def target__resizer(self, col, row):
        resize_factor = col / float(row)

        # 1/3 of the screenwidth is used as the width of the image
        target_width = (self.IMG_SCREEN_RATIO * SCREEN_WIDTH) / 2.0
        # 1/6 of the screenwidth is used as the height of the image
        target_height = resize_factor * target_width

        print("resize_factor = ", resize_factor, "\ntarget_height = ",
              target_height, "\ntarget_width = ", target_width)
        self.img_target_size = (int(target_width), int(target_height))

#Load image from file upload and store as tkinter image
    def upload_new_image(self):

        #Open Window's File upload dialog
        filepath = filedialog.askopenfilename()

        #If filepath does not exist
        if not filepath:
            # Use default image if file not found
            filepath = self.file_path_default

        #Get image from file path
        img_selected = cv2.imread(filepath)

        self.target__resizer(img_selected.shape[0], img_selected.shape[1])


        # Resize the image
        img_selected = cv2.resize(img_selected, self.img_target_size, interpolation=cv2.INTER_CUBIC)

        #Convert to tkinter image
        tk_img = convert_to_tk_img(img_selected)

        #Change the tkinter image display to the user's
        #selected image
        self.img_label.config(image=tk_img)
        self.img_label.image = tk_img  # Keep a reference

        #Save the resized uploaded image
        self.save_resized_uploaded_img()

        # If the image is uploaded, show the canny threshold sliders
        low_threshold_slider.pack(side=tk.TOP, anchor="e")
        high_threshold_slider.pack(side=tk.TOP, anchor="e")

        #Displays and move the button to a new position after image is uploaded
        #img_btn_save.place(x=widget_xpos + 75, y=widget_ypos + 30)
        img_btn_save.pack(pady=25, fill=tk.X)

        #Calls edge maker after image is uploaded
        self.edge_maker(0)


    def load_image1(self):
        # Open Window's File upload dialog
        img1_filepath = filedialog.askopenfilename()

        # If filepath does not exist
        if not img1_filepath:
            # Use default image if file not found
            img1_filepath = self.file_path_default

        # Get image from file path
        img_selected = cv2.imread(img1_filepath)

        self.img_target_size = (int(img_selected[0]), int(img_selected[1]))
        # Resize the image
        img_selected = cv2.resize(img_selected, self.img_target_size, interpolation=cv2.INTER_CUBIC)

        # Convert to tkinter image
        tk_img = convert_to_tk_img(img_selected)

        # Change the tkinter image display to the user's
        # selected image
        self.img_label.config(image=tk_img)
        self.img_label.image = tk_img  # Keep a reference

        # Save the file path of the selected image
        self.img_file_path = img1_filepath

    def load_image2(self):
        # Open Window's File upload dialog
        img2_filepath = filedialog.askopenfilename()

        # If filepath does not exist
        if not img2_filepath:
            # Use default image if file not found
            img2_filepath = self.file_path_default

        # Get image from file path
        img_selected = cv2.imread(img2_filepath)

        # Resize the image
        img_selected = cv2.resize(img_selected, self.img_target_size)

        # Convert to tkinter image
        tk_img = convert_to_tk_img(img_selected)

        # Change the tkinter image display to the user's
        # selected image
        self.edged_img_label.config(image=tk_img)
        self.edged_img_label.image = tk_img  # Keep a reference

        # Save the file path of the selected image
        self.edged_img_file_path = img2_filepath

    def edge_maker(self, val):
        #Convert to opencv image
        img = convert_to_opencv_img(self.img_label.image)
        #Convert to grey scale image
        grey_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Get current values of the sliders (lower and upper thresholds)
        low_thresh = low_threshold_slider.get()
        high_thresh = high_threshold_slider.get()

        # Apply edge detection techniques: gaussian blur and canny edge detection
        grey_img_blur = cv2.GaussianBlur(grey_img, (3, 3), 0)
        edged_img = cv2.Canny(grey_img_blur, low_thresh, high_thresh)

        # Convert to tkinter image
        edged_img = convert_to_tk_img(edged_img)
        self.edged_img_label.config(image=edged_img)
        self.edged_img_label.image = edged_img  # Keep a reference

    def get_original_img_filepath(self):
        if self.img_file_path:
            return self.img_file_path
        else:
            return self.file_path_default

    def get_edged_img_filepath(self):
        if self.edged_img_file_path:
            return self.edged_img_file_path
        else:
            return self.file_path_default

    def save_resized_uploaded_img(self):
        # Open file dialog to choose the location and file name
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"),
                                                            ("JPEG files", "*.jpg;*.jpeg"),
                                                            ("All files", "*.*")])
        if file_path:
            save_uploaded_pil_image = ImageTk.getimage(self.img_label.image)
            # Save the image to the selected file path
            save_uploaded_pil_image.save(file_path)
            self.img_file_path = file_path
            print("Uploaded image saved at ", file_path)

    def save_edged_img(self):
        # Open file dialog to choose the location and file name
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"),
                                                            ("JPEG files", "*.jpg;*.jpeg"),
                                                            ("All files", "*.*")])
        if file_path:
            save_edged_pil_image = ImageTk.getimage(self.edged_img_label.image)
            # Save the image to the selected file path
            save_edged_pil_image.save(file_path)
            self.edged_img_file_path = file_path
            print("Edged image saved at ", file_path)
            close_window()

#Start the loop
#IMG_SCREEN_RATIO = 0.6875
IMG_SCREEN_RATIO = 3/4.0
edged_img_maker = MyEdgedImageMaker(IMG_SCREEN_RATIO)

#Use the computer's screen max width and height as display window
SCREEN_WIDTH_string= str(SCREEN_WIDTH)
SCREEN_HEIGHT_string = str(SCREEN_HEIGHT)
#print("screen size  = [", SCREEN_WIDTH_string, " ", SCREEN_HEIGHT_string, "]")
root.geometry(SCREEN_WIDTH_string + "x" + SCREEN_HEIGHT_string)

# Change the background color using configure
root.configure(bg='lightblue')

# Create sliders (trackbars) for the thresholds
low_threshold = edged_img_maker.canny_low_threshold
low_threshold_slider = tk.Scale(root, from_=0, to=255, orient='horizontal', label="Lower Threshold", command=edged_img_maker.edge_maker)
low_threshold_slider.set(low_threshold)


high_threshold = edged_img_maker.canny_high_threshold
high_threshold_slider = tk.Scale(root, from_=0, to=255, orient='horizontal', label="Upper Threshold", command=edged_img_maker.edge_maker)
high_threshold_slider.set(high_threshold)


#Show image and set image position
edged_img_maker.img_label = tk.Label(root)
edged_img_maker.img_label.pack(side=tk.LEFT, anchor="n")

#Show edged image and set edged image position
edged_img_maker.edged_img_label = tk.Label(root)
edged_img_maker.edged_img_label.pack(side=tk.LEFT, anchor="n")


# Create a main frame for buttons
button_frame = tk.Frame(root)
button_frame.pack(side=tk.RIGHT, padx=20, pady=20, fill=tk.Y)

#Show upload button and set the button position
img_btn_upload = tk.Button(button_frame, text="UPLOAD NEW IMAGE", command=edged_img_maker.upload_new_image)
img_btn_upload.pack(pady=25, fill=tk.X)

#Show load image 1 button and set the button position
img1_btn_load = tk.Button(button_frame, text="LOAD SAVED IMAGE", command=edged_img_maker.load_image1)
img1_btn_load.pack(pady=25, fill=tk.X)

#Show load image 2 button and set the button position
img2_btn_load = tk.Button(button_frame, text="LOAD SAVED CANNY IMAGE", command=edged_img_maker.load_image2)
img2_btn_load.pack(pady=25, fill=tk.X)

img_btn_continue = tk.Button(button_frame, text="CONTINUE", command=close_window)
img_btn_continue.pack(pady=25, fill=tk.X)

#Show save button and set the button position
img_btn_save = tk.Button(button_frame, text="SAVE "
                                            "CANNY IMAGE", command=edged_img_maker.save_edged_img)


# Bind the 'q' key to the close_window function
root.bind("<q>", close_window)
root.bind("<Q>", close_window)

#Loop the setup
root.mainloop()

#Save the final result
original_img_filepath = edged_img_maker.get_original_img_filepath()
final_edged_img_filepath = edged_img_maker.get_edged_img_filepath()