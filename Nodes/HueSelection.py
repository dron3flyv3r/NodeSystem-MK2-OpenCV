import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class HueSelection(Node):
    def __init__(self):
        super().__init__("Hue Selection", "Operations", 200)
        self.add_input("image")
        self.add_output("mask", "mask")
        
        # UI Controls
        self.hue_min_id = dpg.generate_uuid()
        self.hue_max_id = dpg.generate_uuid()
        self.sat_min_id = dpg.generate_uuid()
        self.sat_max_id = dpg.generate_uuid()
        self.val_min_id = dpg.generate_uuid()
        self.val_max_id = dpg.generate_uuid()
        
        # Default values
        self.hue_min = 0
        self.hue_max = 180
        self.sat_min = 0
        self.sat_max = 255
        self.val_min = 0
        self.val_max = 255

    def on_save(self) -> dict:
        return {
            "hue_min": self.hue_min,
            "hue_max": self.hue_max,
            "sat_min": self.sat_min,
            "sat_max": self.sat_max,
            "val_min": self.val_min,
            "val_max": self.val_max
        }
    
    def on_load(self, data: dict):
        self.hue_min = data["hue_min"]
        self.hue_max = data["hue_max"]
        self.sat_min = data["sat_min"]
        self.sat_max = data["sat_max"]
        self.val_min = data["val_min"]
        self.val_max = data["val_max"]
        self.update()

    def update_params(self):
        self.hue_min = dpg.get_value(self.hue_min_id)
        self.hue_max = dpg.get_value(self.hue_max_id)
        self.sat_min = dpg.get_value(self.sat_min_id)
        self.sat_max = dpg.get_value(self.sat_max_id)
        self.val_min = dpg.get_value(self.val_min_id)
        self.val_max = dpg.get_value(self.val_max_id)
        self.update()

    def compose(self):
        dpg.add_text("Hue Range:")
        dpg.add_slider_int(
            label="Min Hue",
            default_value=self.hue_min,
            min_value=0,
            max_value=180,
            callback=self.update_params,
            tag=self.hue_min_id,
            width=185
        )
        dpg.add_slider_int(
            label="Max Hue",
            default_value=self.hue_max,
            min_value=0,
            max_value=180,
            callback=self.update_params,
            tag=self.hue_max_id,
            width=185
        )
        
        dpg.add_text("Saturation Range:")
        dpg.add_slider_int(
            label="Min Saturation",
            default_value=self.sat_min,
            min_value=0,
            max_value=255,
            callback=self.update_params,
            tag=self.sat_min_id,
            width=185
        )
        dpg.add_slider_int(
            label="Max Saturation",
            default_value=self.sat_max,
            min_value=0,
            max_value=255,
            callback=self.update_params,
            tag=self.sat_max_id,
            width=185
        )
        
        dpg.add_text("Value Range:")
        dpg.add_slider_int(
            label="Min Value",
            default_value=self.val_min,
            min_value=0,
            max_value=255,
            callback=self.update_params,
            tag=self.val_min_id,
            width=185
        )
        dpg.add_slider_int(
            label="Max Value",
            default_value=self.val_max,
            min_value=0,
            max_value=255,
            callback=self.update_params,
            tag=self.val_max_id,
            width=185
        )

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask
        
        if image is None:
            return [NodePackage()]

        # Convert to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Create mask for the specified HSV range
        lower = np.array([self.hue_min, self.sat_min, self.val_min])
        upper = np.array([self.hue_max, self.sat_max, self.val_max])
        mask = cv2.inRange(hsv, lower, upper)
        
        return [NodePackage(image_or_mask=mask)]

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