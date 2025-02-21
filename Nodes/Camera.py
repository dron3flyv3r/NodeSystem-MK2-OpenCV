import time
import cv2
import dearpygui.dearpygui as dpg
import numpy as np
from NodeEditor import Node, NodePackage
import threading

class Camera(Node):
    def __init__(self):
        super().__init__("Camera", "Inputs", 400)
        self.camera_id = 0
        self.camera_selector = dpg.generate_uuid()
        self.image_view = dpg.generate_uuid()
        self.add_output("image", "Image")
        self.rgba_image = None
        self.is_streaming = False
        self.toggle_button = dpg.generate_uuid()
        self.cap = None

    def on_init(self):
        threading.Thread(target=self.stream_camera, daemon=True).start()
        self.available_cameras = self.get_available_cameras()
        self.cap = cv2.VideoCapture(self.camera_id)

    def get_available_cameras(self):
        # Check the first 10 indexes.
        available_cameras = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(str(i))
                cap.release()
        return available_cameras

    def on_save(self) -> dict:
        return {
            "camera_id": self.camera_id,
        }

    def on_load(self, data: dict):
        self.camera_id = data["camera_id"]
        self.cap = cv2.VideoCapture(self.camera_id)
        self.update_camera()

    def update_camera(self):
        self.camera_id = int(dpg.get_value(self.camera_selector))
        self.cap = cv2.VideoCapture(self.camera_id)
        self.update()

    def compose(self):
        dpg.add_text("Select Camera:")
        dpg.add_combo(items=self.available_cameras, default_value=str(self.camera_id), tag=self.camera_selector, width=200, callback=self.update_camera)
        dpg.add_button(label="Stop Streaming" if self.is_streaming else "Start Streaming", tag=self.toggle_button, callback=self.toggle_streaming)

        with dpg.texture_registry():
            dpg.add_dynamic_texture(400, 400, [0.0, 0.0, 0.0, 255.0] * 400 * 400, tag=self.image_view)

        dpg.add_image(self.image_view, width=400, height=400)

    def toggle_streaming(self):
        self.is_streaming = not self.is_streaming
        dpg.configure_item(self.toggle_button, label="Stop Streaming" if self.is_streaming else "Start Streaming")
        self.update()
    
    def stream_camera(self):
        while True:
            if not self.is_streaming:
                time.sleep(0.1)
                continue
            self.force_update()

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        
        if self.cap is None:
            return [NodePackage(image_or_mask=np.zeros((400, 400, 4), dtype=np.uint8))]
        
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_id)
        ret, frame = self.cap.read()
        if not ret:
            return [NodePackage(image_or_mask=np.zeros((400, 400, 4), dtype=np.uint8))]
        frame = cv2.flip(frame, 1)

        rgba_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        self.rgba_image = rgba_image

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
