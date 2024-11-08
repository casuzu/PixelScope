import cv2

file_path1 = 'C:/Users/jcasu/OneDrive/Documents/Years/Spring/Spring 2024/Dr.Persad/Drop Images/Cylinder image 1.png'
file_path2 = 'C:/Users/jcasu/OneDrive/Documents/Years/Spring/Spring 2024/Dr.Persad/Drop Images/edged Images/edged cylinder image 1.jpg'

original_img = cv2.imread(file_path1)
edged_img = cv2.imread(file_path2)

trackbar_name = "Overlay"
title_window = "Main img"
alpha_slider_max = 100


def on_trackbar(val):
    alpha = val / alpha_slider_max
    beta = ( 1.0 - alpha )
    added_img = cv2.addWeighted(original_img, alpha, edged_img, beta, 1)
    cv2.imshow(title_window, added_img)


cv2.namedWindow(title_window)
cv2.createTrackbar(trackbar_name, title_window, 0, alpha_slider_max, on_trackbar)

# Show some stuff
on_trackbar(0)


cv2.waitKey(0)

#added_image = cv2.addWeighted(edged_img,1,original_img,1,0)



#cv2.imshow("Main img", added_image)

