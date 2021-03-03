import time
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

    h, w = shape
    if w > h:
        w = int(max_size*(h/w))
        h = max_size
    else:
        h = int(max_size*(w/h))
        w = max_size

    return h, w

class PySkribbl(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        bg_color = "#333332"

        self.image_path = "clipart.png"
        self.image_ed = None
        self.contours = None

        self.top_left = (1, 1)
        self.bottom_right = pyautogui.size()
        self.bottom_right = (self.bottom_right[0]-2, self.bottom_right[1]-2)

        self.master.geometry("600x750")
        self.master.title("PySkribbl")
        self.master.configure(background=bg_color)
        self.master.resizable(True, True)

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
        self.instructions.grid(row=3, column=1)

        self.precision_label = tk.Label(self.master, text="Precision",
                                        fg="white", bg=bg_color)
        self.precision_label.grid(row=4, column=0)

        self.precision = tk.Entry(self.master)
        self.precision.grid(row=4, column=1)
        self.precision.insert(tk.END, "10")

        self.set_image(True)

    def query(self):
        # FIXME

        self.image_path = self.query_entry.get()
        self.set_image()

    def draw(self):
        try:
            draw_step = int(self.precision.get())
            if draw_step <= 0:
                draw_step = 10
        except ValueError:
            draw_step = 10

        for n, contour in enumerate(self.contours):
            if len(contour) <= 3*draw_step:
                continue

            pyautogui.moveTo(self.top_left[0]+contour[0, 0, 0],
                             self.top_left[1]+contour[0, 0, 1])
            for i in range(1, len(contour), draw_step):
                pyautogui.dragTo(self.top_left[0]+contour[i, 0, 0],
                                 self.top_left[1]+contour[i, 0, 1])

            self.instructions.configure(text="{}/{}".format(
                n,
                len(self.contours)
            ))
            self.update()

    def drawing_init(self):
        self.instructions.configure(text="Move on top-left corner...")
        self.update()
        time.sleep(3)
        self.top_left = pyautogui.position()
        self.instructions.configure(text="Move on bottom-right corner...")
        self.update()
        time.sleep(3)
        self.bottom_right = pyautogui.position()
        self.instructions.configure(text="All done!")
        print("Top left  = {}".format(self.top_left))
        print("Bot right = {}".format(self.bottom_right))

    def set_image(self, first=False):
        image = cv2.imread(self.image_path)
        image = cv2.resize(image, find_resized_size(image.shape[0:2]))
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
