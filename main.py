import cv2, csv
from SplineMaster import MySpline
import tkinter as tk
import EdgedMenu


root = tk.Tk()
SCREEN_WIDTH = root.winfo_screenwidth()
SCREEN_HEIGHT = root.winfo_screenheight()
root.destroy()

def send_to_file(coordinates, file_name):
    #header = ['X','Y']
    #points_file = open('points.csv', 'w+', newline='')

    filename = file_name + ".csv"

    with open(filename, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerows([["P1", "P2"]])
        csv_writer.writerows(coordinates)
    csv_file.close()

def images_same_size(img1, img2):
    if img1.shape == img2.shape:
        return True
    else:
        return False

def img_up_resizer(image):
    new_width = int(0.25 * SCREEN_WIDTH)
    new_height = int(0.75 * SCREEN_HEIGHT)
    new_size = (new_width, new_height)
    resized_img = cv2.resize(image, new_size, interpolation=cv2.INTER_LINEAR)
    return resized_img
def main_menu():
    print("What mode would you like to run?:")
    print("Press l for Straight Line Mode.")
    print("Press p for Point Mode.")
    print("Press c for Calibration Mode.")
    print("Press u to undo added point(s).")
    print("Press q to close the application.")
    print("Press m to see this menu again.")
    global select_main_menu
    select_main_menu = False



#file_path1 = 'C:/Users/jcasu/OneDrive/Documents/Years/Spring/Spring 2024/Dr.Persad/Drop Images/Cylinder image 5.png'
#file_path2 = 'C:/Users/jcasu/OneDrive/Documents/Years/Spring/Spring 2024/Dr.Persad/Drop Images/edged Images/edged cylinder image 2.jpg'

img, img_edged = EdgedMenu.original_img, EdgedMenu.final_edged_img

img = img_up_resizer(cv2.imread(img))
img_edged = img_up_resizer(cv2.imread(img_edged))


if images_same_size(img_edged, img):
    spline = MySpline(img_edged, img)
    running = True
    select_main_menu = True

    spline.show_image()
    spline.show_trackbar()

    while running:
        key = cv2.waitKey(1)

        if select_main_menu or key == ord('m')or key == ord('M'):
            main_menu()

        if key == ord('l')or key == ord('L'):
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

        elif key == ord('c')or key == ord('C'):
            if spline.CALIBRATION_COMPLETE: #If calibration is already done
                select_main_menu = True #call main menu
                spline.CALIBRATION_COMPLETE = False #Reset the calibration mode
                spline.modeselect = None
            else:
                spline.reset_all()
                print("========================")
                print("CALIBRATION MODE")
                print("========================")
                print("Enter", spline.TOTAL_CALIBRATION_NUM, "entries to calibrate the pixel to mm relationship.")
                print("Press the 'm' key after 'CALIBRATION COMPLETED' message to return to the main menu.")
                spline.modeselect = "Calibration"
                spline.mode()

        elif key == ord('u') or key == ord('U'):
            spline.undo_point()

        # Close program with keyboard 'q'
        elif key == ord('q') or key == ord('Q'):
            if not spline.get_points_coord() or not spline.get_lines_coord():
                #points_list = spline.get_points_coord()
                lines_list = spline.get_lines_coord()
                vlines_list = spline.get_v_lines_coord()
                hlines_list = spline.get_h_lines_coord()

                #print("Points = {}".format(points_list))
                print("Lines = {}".format(lines_list))
                print(" Vertical Lines = {}".format(vlines_list))
                print(" Horizontal Lines = {}".format(hlines_list))

                send_to_file(vlines_list, "Vertical_Lines")
                send_to_file(hlines_list, "Horizontal_Lines")


            cv2.destroyAllWindows()
            exit(0)
else:
    print("Images are not the same size.")

