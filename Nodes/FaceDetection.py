import cv2
import cv2.data
import numpy as np
import dearpygui.dearpygui as dpg
from NodeEditor import Node, NodePackage

class FaceDetection(Node):
    def __init__(self):
        super().__init__("Face Detection", "Vision", 200)
        self.add_input("image", "Image")
        self.add_output("mask", "Mask")
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
    def viewer(self, outputs: list[NodePackage]):
        data = outputs[0]
        img_tag = dpg.generate_uuid()
        with dpg.texture_registry():
            dpg.add_dynamic_texture(400, 400, [0.0, 0.0, 0.0, 0.0]*400*400, tag=img_tag)
        
        dpg.add_image(img_tag)
        
        image_rgba = data.copy_resize((400, 400), keep_alpha=True)
        image_rgba = image_rgba.astype(float)
        image_rgba /= 255

        dpg.set_value(img_tag, image_rgba.flatten())

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

        mask = np.zeros(image.shape[:2], np.uint8)
        for (x, y, w, h) in faces:
            cv2.rectangle(mask, (x, y), (x+w, y+h), 255, -1)

        return [NodePackage(image_or_mask=mask)]
