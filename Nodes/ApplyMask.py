import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class ApplyMask(Node):
    def __init__(self):
        super().__init__("Apply Mask", "Operations", 200)
        self.add_input("image", "image")
        self.add_input("mask", "mask")
        self.add_output("image", "image")
        
        self.invert_mask_id = dpg.generate_uuid()
        self.invert_mask = False

    def on_save(self) -> dict:
        return {
            "invert_mask": self.invert_mask
        }
    
    def on_load(self, data: dict):
        self.invert_mask = data["invert_mask"]
        self.update()

    def update_params(self):
        self.invert_mask = dpg.get_value(self.invert_mask_id)
        self.update()

    def compose(self):
        dpg.add_text("Mask Options:")
        dpg.add_checkbox(label="Invert Mask", default_value=self.invert_mask,
                        callback=self.update_params, tag=self.invert_mask_id)

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        if len(inputs) < 2:
            return [NodePackage()]
            
        image_data = inputs[0]
        mask_data = inputs[1]
        
        image = image_data.image_or_mask
        mask = mask_data.image_or_mask
        
        if image is None or mask is None:
            return [NodePackage()]

        # Convert image to BGRA if needed
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
        elif len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            
        # Convert mask to grayscale if needed
        if len(mask.shape) == 3:
            if mask.shape[2] == 4:
                mask = cv2.cvtColor(mask, cv2.COLOR_BGRA2GRAY)
            else:
                mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        
        if self.invert_mask:
            mask = cv2.bitwise_not(mask)
        
        # Apply mask
        result = cv2.bitwise_and(image, image, mask=mask)
        
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