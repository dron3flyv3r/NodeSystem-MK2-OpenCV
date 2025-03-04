import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class Invert(Node):
    def __init__(self):
        super().__init__("Invert", "Operations", 200)
        self.add_input("image/mask")
        self.add_output("image/mask")

    def compose(self):
        dpg.add_text("Inverts the colors/intensity of the image")

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask
        
        if image is None:
            return [NodePackage()]

        result = cv2.bitwise_not(image)
        return [NodePackage(image_or_mask=result)]

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
