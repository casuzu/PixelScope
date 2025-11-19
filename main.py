import cv2, csv
from PIL import Image
import os
from SplineMaster import MySpline
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

import EdgedMenu

root = tk.Tk()
SCREEN_WIDTH = root.winfo_screenwidth()
SCREEN_HEIGHT = root.winfo_screenheight()



def send_to_file(coordinates, file_name):
    # header = ['X','Y']
    # points_file = open('points.csv', 'w+', newline='')

    filename = file_name + ".csv"

    with open(filename, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerows([["[X1, Y1]", "[X2, Y2]"]])
        csv_writer.writerows(coordinates)
    csv_file.close()


def save_edged_img(save_img):

    # Open file dialog to choose the location and file name
    file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                             filetypes=[("PNG files", "*.png"),
                                                        ("JPEG files", "*.jpg;*.jpeg"),
                                                        ("All files", "*.*")])

    # Save the image to the selected file path
    if file_path:
        pil_save_img = Image.fromarray(save_img)
        try:
            pil_save_img.save(file_path)
            print(f"Image saved successfully to: {file_path}")
        except Exception as e:
            print(f"Error saving image: {e}")


def save_analysis_img(save_img, img_name, save_path):
    try:
        # Remove potential surrounding quotes
        save_path = save_path.strip('"')

        modified_save_path = save_path.replace("\\", "/")
        # Ensure the save path exists
        os.makedirs(modified_save_path, exist_ok=True)

        # Construct the full file path
        full_file_path = os.path.join(modified_save_path, img_name + ".jpeg")

        # Save the image as JPEG
        save_img.convert("RGB").save(full_file_path, "jpeg")
        print(f"Image saved as {full_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")


def images_same_size(img1, img2):
    if img1.shape == img2.shape:
        return True
    else:
        return False


def img_up_resizer(image, img_screen_percent):
    new_width = int(img_screen_percent * SCREEN_HEIGHT)
    new_height = new_width
    new_size = (new_width, new_height)
    resized_img = cv2.resize(image, new_size, interpolation=cv2.INTER_LINEAR)
    return resized_img


def main_menu():
    print("What mode would you like to run?:")
    print("Press the 'l' key for Straight Line Mode.")
    print("Press 'c' key for Calibration Mode.")
    print("Press 'q' key to close the application.")
    print("Press 'm' key to see this menu again.")
    global select_main_menu
    select_main_menu = False


img = EdgedMenu.original_img
img_edged = EdgedMenu.final_edged_img

print("img.shape = ", img.shape)
print("img_edged.shape = ", img_edged.shape)

if images_same_size(img_edged, img):
    spline = MySpline(img_edged, img)
    running = True
    select_main_menu = True

    spline.show_image()
    spline.show_trackbar()

    while running:
        key = cv2.waitKey(1)

        if select_main_menu or key == ord('m') or key == ord('M'):
            main_menu()

        if key == ord('l') or key == ord('L'):
            spline.reset_all()
            print("========================")
            print("STRAIGHT LINE")
            print("========================")
            spline.modeselect = "Straight Line"
            spline.mode()

        elif key == ord('p') or key == ord('P'):
            spline.reset_all()
            print("POINTS")
            spline.modeselect = "Points"
            spline.mode()

        elif key == ord('c') or key == ord('C'):
            if spline.CALIBRATION_COMPLETE:  # If calibration is already done
                select_main_menu = True  # call main menu
                spline.CALIBRATION_COMPLETE = False  # Reset the calibration mode
                spline.modeselect = None
            else:
                spline.reset_all()
                print("========================")
                print("CALIBRATION MODE")
                print("========================")

                spline.total_calibration_num = int(
                    input("Please enter the number(integer) of calibration lines in order"
                          " to calibrate the pixel to mm relationship:  "))
                print("Press the 'm' key after 'CALIBRATION COMPLETED' message to return to the main menu.")
                spline.modeselect = "Calibration"
                spline.mode()


        # Close program with keyboard 'q'
        elif key == ord('q') or key == ord('Q'):
            if spline.get_lines():
                lines_list = [[i.starting_point, i.ending_point] for i in spline.get_lines()]
                print("Lines = {}".format(lines_list))

                vertic_lines_list = [[i.starting_point, i.ending_point]
                                     for i in spline.get_lines()
                                     if i.get_type() == "Vertical"]

                horizon_lines_list = [[i.starting_point, i.ending_point]
                                      for i in spline.get_lines()
                                      if i.get_type() == "Horizontal"]

                print("\nVertical Lines = {}".format(vertic_lines_list))
                print("\nHorizontal Lines = {}".format(horizon_lines_list))

                send_to_file(vertic_lines_list, "Vertical_Lines")
                send_to_file(horizon_lines_list, "Horizontal_Lines")

                final_img = spline.get_edged_img()
                save_edged_img(final_img)
            cv2.destroyAllWindows()
            root.destroy()
            exit(0)
else:
    print("Images are not the same size.")
