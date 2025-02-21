import cv2
import dearpygui.dearpygui as dpg
import numpy as np
from NodeEditor import Node, NodePackage

class Video(Node):
    def __init__(self):
        super().__init__("Video", "Inputs", 400)
        self.file_path = dpg.generate_uuid()
        self.image_view = dpg.generate_uuid()
        self.video_selected = ""
        self.cap = None
        self.is_playing = True
        self.toggle_button = dpg.generate_uuid()
        self.add_output("image", "Image")

    def on_save(self) -> dict:
        return {
            "video_selected": self.video_selected,
        }

    def on_load(self, data: dict):
        self.video_selected = data["video_selected"]
        self.set_file_path(None, None)

    def set_file_path(self, sender, app_data):
        if app_data and "selections" in app_data:
            for i in app_data["selections"].values():
                self.video_selected = i
                break
        elif self.video_selected == "":
            return

        self.cap = cv2.VideoCapture(self.video_selected)
        self.update()

    def compose(self):
        with dpg.file_dialog(directory_selector=False, show=False, callback=self.set_file_path, tag=self.file_path, file_count=1, width=700, height=400):
            dpg.add_file_extension("Video Files (*.mp4 *.avi *.mov){.mp4,.avi,.mov}")

        dpg.add_button(label="Select Video", callback=lambda: dpg.show_item(self.file_path))
        dpg.add_button(label="Stop Playing" if self.is_playing else "Start Playing", tag=self.toggle_button, callback=self.toggle_playing)

        with dpg.texture_registry():
            dpg.add_dynamic_texture(400, 400, [0.0, 0.0, 0.0, 255.0] * 400 * 400, tag=self.image_view)

        dpg.add_image(self.image_view, width=400, height=400)

    def toggle_playing(self):
        self.is_playing = not self.is_playing
        dpg.configure_item(self.toggle_button, label="Stop Playing" if self.is_playing else "Start Playing")
        self.update()

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        if not self.is_playing:
            return [NodePackage(image_or_mask=np.zeros((400, 400, 4), dtype=np.uint8))]

        if self.cap is None or not self.cap.isOpened():
            if self.video_selected:
                self.cap = cv2.VideoCapture(self.video_selected)
            else:
                return [NodePackage(image_or_mask=np.zeros((400, 400, 4), dtype=np.uint8))]

        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop the video
            ret, frame = self.cap.read()
            if not ret:
                return [NodePackage(image_or_mask=np.zeros((400, 400, 4), dtype=np.uint8))]

        rgba_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

        max_dim = max(rgba_image.shape[0], rgba_image.shape[1])
        scale = 400 / max_dim
        rgba_image = cv2.resize(rgba_image, (int(rgba_image.shape[1] * scale), int(rgba_image.shape[0] * scale)))

        top = (400 - rgba_image.shape[0]) // 2
        bottom = 400 - top - rgba_image.shape[0]
        left = (400 - rgba_image.shape[1]) // 2
        right = 400 - left - rgba_image.shape[1]
        rgba_image = cv2.copyMakeBorder(rgba_image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0, 0])

        rgba_image = rgba_image.astype(float)
        rgba_image /= 255
        dpg.set_value(self.image_view, rgba_image.flatten())

        return [NodePackage(image_or_mask=frame)]
