import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk


def images_same_size(img1, img2):
    if img1.shape == img2.shape:
        return True
    else:
        return False


def convert_to_tk_img(opencv_img):  # Converts opencv image to tkinter image
    RGB_img = cv2.cvtColor(opencv_img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB

    # Convert the RGB image (NumPy array) to a PIL Image
    PIL_img = Image.fromarray(RGB_img)

    # convert a PIL Image (or a NumPy array converted to a PIL Image)
    # into a format that can be displayed in a Tkinter GUI application.
    return ImageTk.PhotoImage(PIL_img)


def convert_to_opencv_img(tk_image):  # Converts tkinter image to opencv image
    # Convert Tkinter PhotoImage to PIL Image
    pil_image = ImageTk.getimage(tk_image)

    # Convert PIL Image to NumPy array
    open_cv_image = np.array(pil_image)

    # Convert RGB to BGR
    open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

    return open_cv_image


class MyEdgedImageMaker:
    def __init__(self, img_screen_ratio, root, on_continue):
        # if this frame is completed, use continue to move to next frame in main.py
        self.on_continue = on_continue  # store callback for main.py

        # Window frame setup
        self.root = root
        self.frame = tk.Frame(root)

        # Half the screen to be used as images display
        self.IMG_SCREEN_RATIO = img_screen_ratio

        # Change the background color of the frame using configure
        self.frame.configure(bg='lightblue')
        self.frame.pack(fill="both", expand=True)

        # Create tk frame for images
        img_frame_width = (self.IMG_SCREEN_RATIO * self.root.winfo_screenwidth())
        self.img_frame = tk.Frame(self.frame, width=img_frame_width, bd=1, bg='lightblue')
        self.img_frame.pack(side="left", anchor="n")

        # Create a main frame for buttons
        self.button_frame = tk.Frame(self.frame)
        self.button_frame.pack(side=tk.RIGHT, padx=20, pady=20, fill=tk.Y)

        # Used to check if the save button has already been added to the frame
        self.save_button_created = False

        # Create a label for the original image
        self.img_label = None

        # Create a label for the Edged Image
        self.edged_img_label = None

        # Used to resized images to the target size
        self.img_target_size = None

        # Canny Edge sliders
        self.low_threshold_slider = None
        self.high_threshold_slider = None

        # The values for canny low and high thresholds were choosen experimentally.
        self.canny_low_threshold = 40
        self.canny_high_threshold = 100

        self.file_path_default = "Filepath not found Cat.jpeg"
        self.img_file_path = ""
        self.edged_img_file_path = ""

        # Update Final images
        self.final_edged_img = None
        self.final_original_img = None
        self.update_final_images()

        # show SAVE button only after an image is initially uploaded
        self.show_save_button = False

        # Error code to change the error messages
        # Error code is set as no main image uploaded.
        self.ERROR_CODE = "NMIUD"  # No Main Image Uploaded

        self.run()

    def close_window_frame(self):  # Close the display window frame
        if self.images_fail_check():
            return
        self.frame.destroy()
        self.on_continue(self.final_original_img, self.final_edged_img)

    def images_fail_check(self):
        self.update_final_images()

        # If all images have been uploaded and are the same size
        if self.img_file_path != self.file_path_default and self.edged_img_file_path != self.file_path_default:
            if not images_same_size(self.final_original_img, self.final_edged_img):
                messagebox.showerror("Image Size Mismatch",
                                     "The images are not the same size.")
                return True  # Check failed because images are not the same size.
            else:
                # Check Passed.
                return False

        if self.ERROR_CODE == "NMIUD":  # Code means No Main Image Uploaded
            messagebox.showerror("Error", "Please upload an image.")
            # Check failed because main image was not uploaded
            # and is the same as the default path.
            return True

        if self.ERROR_CODE == "NEIUD":
            if self.img_file_path != self.file_path_default:
                messagebox.showerror("Error",
                                     "Please upload an edge-detected image.")
            else:
                messagebox.showerror("Error", "Please upload an image.")
            return True

        if self.ERROR_CODE == "EINS":  # Error code: Edged Image Not Saved
            messagebox.showerror("Error",
                                 "Please save the edge-detected image first.")
            # Check failed because edged image was not saved/uploaded
            # and is the same as the default path.
            return True

    def target__resizer(self, col, row):
        resize_factor = col / float(row)
        SCREEN_WIDTH = self.root.winfo_screenwidth()

        # 1/4 of the screenwidth is used as the width of the image
        target_width = (self.IMG_SCREEN_RATIO * SCREEN_WIDTH) / 2.0
        # 1/6 of the screenwidth is used as the height of the image
        target_height = resize_factor * target_width

        self.img_target_size = (int(target_width), int(target_height))

    # Load image from file upload and store as tkinter image
    def upload_new_image(self):

        # Open Window's File upload dialog
        filepath = filedialog.askopenfilename()

        # If filepath does not exist
        if not filepath:
            # Use default image if file not found
            return

        user_answer = messagebox.askyesno("Save Resized Image",
                                          "Do you want to save the resized image to continue?")

        if not user_answer:
            self.ERROR_CODE = "NMIUD"  # No Main Image Uploaded
            return

        # Get image from file path
        img_selected = cv2.imread(filepath)

        self.target__resizer(img_selected.shape[0], img_selected.shape[1])

        # Resize the image
        # Interpolation = cv2.INTER_AREA best for shrinking an image
        img_selected = cv2.resize(img_selected, self.img_target_size, interpolation=cv2.INTER_AREA)

        # Convert to tkinter image
        tk_img = convert_to_tk_img(img_selected)

        # Change the tkinter image display to the user's
        # selected image
        self.img_label.config(image=tk_img)
        self.img_label.image = tk_img  # Keep a reference

        # Save the resized uploaded image
        if not self.save_resized_uploaded_img():
            return
        else:
            # Set the error code for saving an edged image.
            self.ERROR_CODE = "EINS"

        # If the image is uploaded, show the canny threshold sliders
        self.low_threshold_slider.pack(side=tk.TOP, anchor="e")
        self.high_threshold_slider.pack(side=tk.TOP, anchor="e")

        # Displays the SAVE button after an image is initially been uploaded
        # img_btn_save.pack(pady=25, fill=tk.X)
        self.run(add_save_button=True)

        # Calls edge maker after image is uploaded
        self.edge_maker(0)

    def load_first_image(self):
        # Open Window's File upload dialog
        img1_filepath = filedialog.askopenfilename()

        # If filepath does not exist and no main image has been uploaded.
        if not img1_filepath and self.img_file_path == self.file_path_default:

            self.ERROR_CODE = "NMIUD"  # No Main Image Uploaded
            return
        # Set the error code for uploading an edged image.
        else:
            self.ERROR_CODE = "NEIUD"  # No Edged Image Uploaded

        # Get image from file path
        img_selected = cv2.imread(img1_filepath)

        self.target__resizer(img_selected.shape[0], img_selected.shape[1])

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

    def load_second_image(self):
        # Open Window's File upload dialog
        img2_filepath = filedialog.askopenfilename()

        # If filepath does not exist
        if not img2_filepath:
            self.ERROR_CODE = "NEIUD"  # No Edged Image Uploaded
            return

        # Get image from file path
        img_selected = cv2.imread(img2_filepath)

        self.target__resizer(img_selected.shape[0], img_selected.shape[1])

        # Resize the image
        img_selected = cv2.resize(img_selected, self.img_target_size, interpolation=cv2.INTER_CUBIC)

        # Resize the image
        # img_selected = cv2.resize(img_selected, self.img_target_size)

        # Convert to tkinter image
        tk_img = convert_to_tk_img(img_selected)

        # Change the tkinter image display to the user's
        # selected image
        self.edged_img_label.config(image=tk_img)
        self.edged_img_label.image = tk_img  # Keep a reference

        # Save the file path of the selected image
        self.edged_img_file_path = img2_filepath

    def edge_maker(self, val):
        # Convert to opencv image
        img = convert_to_opencv_img(self.img_label.image)
        # Convert to grey scale image
        grey_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Get current values of the sliders (lower and upper thresholds)
        low_thresh = self.low_threshold_slider.get()
        high_thresh = self.high_threshold_slider.get()

        # Apply edge detection techniques: gaussian blur and canny edge detection
        grey_img_blur = cv2.GaussianBlur(grey_img, (3, 3), 0)
        edged_img = cv2.Canny(grey_img_blur, low_thresh, high_thresh)

        # Convert to tkinter image
        edged_img = convert_to_tk_img(edged_img)
        self.edged_img_label.config(image=edged_img)
        self.edged_img_label.image = edged_img  # Keep a reference

    def get_original_img(self):
        if not self.img_file_path:
            self.img_file_path = self.file_path_default
            print("in get_original_img: self.img_file_path = ", self.img_file_path)

        img_selected = cv2.imread(self.img_file_path)

        self.target__resizer(img_selected.shape[0], img_selected.shape[1])

        # Resize the image
        img_selected = cv2.resize(img_selected, self.img_target_size, interpolation=cv2.INTER_CUBIC)

        return img_selected

    def get_edged_img(self):
        if not self.edged_img_file_path:
            self.edged_img_file_path = self.file_path_default

        img_selected = cv2.imread(self.edged_img_file_path)

        self.target__resizer(img_selected.shape[0], img_selected.shape[1])

        # Resize the image
        img_selected = cv2.resize(img_selected, self.img_target_size, interpolation=cv2.INTER_CUBIC)

        return img_selected

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
            return True
        else:
            self.ERROR_CODE = "NMIUD"  # No Main Image Uploaded
            self.img_label.grid_remove()
            return False

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
        else:
            self.ERROR_CODE = "EINS"  # Error code: Edged Image Not Saved

    def run(self, add_save_button=False):
        if not add_save_button:
            # Create sliders (trackbars) for the thresholds
            low_threshold = self.canny_low_threshold
            self.low_threshold_slider = tk.Scale(self.frame, from_=0, to=255, orient='horizontal',
                                                 label="Lower Threshold",
                                                 command=self.edge_maker)
            self.low_threshold_slider.set(low_threshold)

            high_threshold = self.canny_high_threshold
            self.high_threshold_slider = tk.Scale(self.frame, from_=0, to=255, orient='horizontal',
                                                  label="Upper Threshold",
                                                  command=self.edge_maker)
            self.high_threshold_slider.set(high_threshold)

            # Show image and set image position
            self.img_label = tk.Label(self.img_frame)
            self.img_label.grid(row=0, column=0, sticky="nw")

            # Show edged image and set edged image position
            self.edged_img_label = tk.Label(self.img_frame)
            self.edged_img_label.grid(row=0, column=1, sticky="nw")

            # Show upload button and set the button position
            img_btn_upload = tk.Button(self.button_frame, text="UPLOAD NEW IMAGE", command=self.upload_new_image)
            img_btn_upload.pack(pady=25, fill=tk.X)

            # Show load image 1 button and set the button position
            img1_btn_load = tk.Button(self.button_frame, text="LOAD SAVED RESIZED IMAGE", command=self.load_first_image)
            img1_btn_load.pack(pady=25, fill=tk.X)

            # Show load image 2 button and set the button position
            img2_btn_load = tk.Button(self.button_frame, text="LOAD SAVED CANNY IMAGE", command=self.load_second_image)
            img2_btn_load.pack(pady=25, fill=tk.X)

            img_btn_continue = tk.Button(self.button_frame, text="CONTINUE", command=self.close_window_frame)
            img_btn_continue.pack(pady=25, fill=tk.X)

        elif not self.save_button_created:
            # Show save button and set the button position
            img_btn_save = tk.Button(self.button_frame, text="SAVE "
                                                             "CANNY IMAGE", command=self.save_edged_img)
            # Displays and move the button to a new position after image is uploaded
            img_btn_save.pack(pady=25, fill=tk.X)

            self.save_button_created = True

    def update_final_images(self):
        self.final_original_img = self.get_original_img()
        self.final_edged_img = self.get_edged_img()
        print("final original image shape = ", self.final_original_img.shape)
        print("final edged image shape = ", self.final_edged_img.shape)

    def get_final_images(self):
        return self.final_original_img, self.final_edged_img
