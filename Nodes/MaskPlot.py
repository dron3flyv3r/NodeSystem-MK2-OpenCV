import cv2
import numpy as np
import dearpygui.dearpygui as dpg
from NodeEditor import Node, NodePackage

class MaskPlot(Node):
    def __init__(self):
        super().__init__("Mask Plot", "Vision", 200)
        self.add_input("image", "Image")
        self.add_input("mask", "Mask")
        self.add_output("image", "Image")
        self.color = [255, 0, 0]  # Default color: Red
        self.color_picker = dpg.generate_uuid()

    def compose(self):
        dpg.add_color_picker(default_value=self.color, label="Mask Color", tag=self.color_picker, callback=self.update_color, width=200)

    def update_color(self):
        self.color = dpg.get_value(self.color_picker)
        self.update()

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        image_data = inputs[0]
        mask_data = inputs[1]

        image = image_data.image_or_mask
        mask = mask_data.image_or_mask

        # Ensure mask is the same size as the image
        mask = cv2.resize(mask, (image.shape[1], image.shape[0]))

        # Convert grayscale mask to BGR
        if len(mask.shape) == 2:
            mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        else:
            mask_bgr = mask  # Assume it's already BGR

        # Create a outline of the mask on the image
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(image, contours, -1, self.color, 2)
        return [NodePackage(image_or_mask=image)]
