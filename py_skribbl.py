"""
A small application that uses OpenCV to convert an image to a drawing, and
draws it using mouse inputs. Use it to prank your friends on Skribbl.io!
"""

import time
import numpy as np
import cv2
import pyautogui
import tkinter as tk
from PIL import ImageTk, Image

def find_resized_size(shape, max_size=600):
    """
    Compute the optimal size of an image.
    :param shape: Shape (w,h) of the original image.
    :max_size: Target size of the largest side.
    :return: Target shape
    """

    w, h = shape
    if w > h:
        w = int(max_size*(h/w))
        h = max_size
    else:
        h = int(max_size*(w/h))
        w = max_size

    return h, w

def actual_coords(coords, top_left, bottom_right, img_size):
    """
    Compute actual coordinates on screen to draw the image in the calibrated
    drawing zone.

    :param coords: Input coordinates on the image.
    :param top_left: Coordinates of the top-left corner of the drawing zone.
    :param bottom_right: Coordinates of the bottom-right corner of the drawing
    zone.
    :param img_size: Size of the input image.
    :return: Output coordinates on screen.
    """

    drawing_size = tuple(a-b for a,b in zip(bottom_right, top_left))
    if drawing_size[0] <= 0 or drawing_size[1] <= 0:
        raise ValueError("Incorrect calibration")

    img_aspect = img_size[0]/img_size[1]

    output = np.zeros_like(coords)

    marginW = drawing_size[0]-img_size[0]
    print(drawing_size)
    print(img_size)
    if marginW < 0:
        target_size = (
            img_size[0]+marginW,
            int((img_size[0]+marginW)/img_aspect)
        )
    else:
        target_size = img_size
    marginH = drawing_size[1]-target_size[1]
    if marginH < 0:
        target_size = (
            int((target_size[1]+marginH)*img_aspect),
            target_size[1]+marginH
        )

    output[:, 0] = top_left[0] + (target_size[0] * coords[:, 0])/img_size[0]
    output[:, 1] = top_left[1] + (target_size[1] * coords[:, 1])/img_size[1]

    return output

#%%

class PySkribbl(tk.Frame):
    """
    Tk frame.
    """

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        bg_color = "#333332"

        self.image_path = "clipart.png"
        self.image_ed = None
        self.contours = None

        # These are my actual settings on my screen
        self.top_left = (474, 285)
        self.bottom_right = (1305, 907)

        self.master.geometry("600x750")
        self.master.title("PySkribbl")
        self.master.configure(background=bg_color)
        self.master.resizable(True, True)
        self.master.attributes('-type', 'dialog')

        self.query_entry = tk.Entry(self.master)
        self.query_entry.grid(row=0, column=0)
        self.query_entry.insert(tk.END, self.image_path)

        self.query_button = tk.Button(self.master, text="Query",
                                      command=self.query)
        self.query_button.grid(row=0, column=1)

        self.draw_button = tk.Button(self.master, text="Draw!",
                                      command=self.draw)
        self.draw_button.grid(row=2, column=0, columnspan=2)

        self.init_button = tk.Button(self.master,
                                     text="Calibrate drawing zone",
                                     command=self.drawing_init)
        self.init_button.grid(row=3, column=0)

        self.instructions = tk.Label(self.master, text="", fg="white",
                                     bg=bg_color)
        self.instructions.grid(row=4, column=0)

        self.precision_label = tk.Label(self.master,
                                        text="Precision (smaller=slower)",
                                        fg="white", bg=bg_color)
        self.precision_label.grid(row=3, column=1)

        self.precision = tk.Entry(self.master)
        self.precision.grid(row=4, column=1)
        self.precision.insert(tk.END, "10")

        self.set_image(True)

    def query(self):
        """
        Query a random image on Google Image to use as a reference.
        """

        # FIXME

        self.image_path = self.query_entry.get()
        self.set_image()

    def draw(self):
        """
        Draw the image on the screen.
        """

        try:
            draw_step = int(self.precision.get())
            if draw_step <= 0:
                draw_step = 10
        except ValueError:
            draw_step = 10

        for n, contour in enumerate(self.contours):
            contour = contour[:, 0, :]

            # Skip small lines (<=3*draw_step)
            if len(contour) <= 3*draw_step:
                continue

            coords = actual_coords(
                contour,
                self.top_left,
                self.bottom_right,
                (self.image_ed.shape[1], self.image_ed.shape[0])
            )

            pyautogui.moveTo(coords[0, 0], coords[0, 1])
                # self.top_left[0]+contour[0, 0],
                #              self.top_left[1]+contour[0, 1])
            for i in range(1, len(coords), draw_step):
                pyautogui.dragTo(coords[i, 0], coords[i, 1])
                    # self.top_left[0]+contour[i, 0],
                    #              self.top_left[1]+contour[i, 1])

            self.instructions.configure(text="{}/{}".format(
                n,
                len(self.contours)
            ))
            self.update()

    def drawing_init(self):
        """
        Calibrate the drawing zone.
        """

        self.instructions.configure(text="Move on top-left corner...")
        self.update()
        time.sleep(2)
        top_left = pyautogui.position()
        self.instructions.configure(text="Move on bottom-right corner...")
        self.update()
        time.sleep(2)
        bottom_right = pyautogui.position()
        self.instructions.configure(text="All done!")

        try:
            actual_coords(np.array([[0, 0]]),
                          top_left,
                          bottom_right,
                          (self.image_ed.shape[1], self.image_ed.shape[0])
            )
            self.top_left = top_left
            self.bottom_right = bottom_right
        except ValueError as e:
            self.instructions.configure(text=e)

    def set_image(self, first=False):
        """
        Pre-compute the retrieved image.

        :param first: Should be True only in __init__.
        """

        image = cv2.imread(self.image_path)
        image = cv2.resize(image, find_resized_size(
            (image.shape[1], image.shape[0])
        ))
        self.image_ed = cv2.Canny(image, 100, 200, True)

        _, self.contours, hierarchy = cv2.findContours(
            self.image_ed,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_NONE
        )

        self.image = ImageTk.PhotoImage(Image.fromarray(self.image_ed))

        if not first:
            self.image_label.grid_forget()

        self.image_label = tk.Label(self.master, image=self.image)
        self.image_label.grid(row=1, column=0, columnspan=2)


if __name__ == "__main__":
    pyautogui.PAUSE = 0.001
    root = tk.Tk()
    PySkribbl(root)
    root.mainloop()
