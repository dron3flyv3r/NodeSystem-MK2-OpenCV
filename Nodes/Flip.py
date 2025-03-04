import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class Flip(Node):
    def __init__(self):
        super().__init__("Flip", "Operations", 200)
        self.add_input("image")
        self.add_output("image")
        
        # UI Controls
        self.flip_mode_id = dpg.generate_uuid()
        self.flip_mode = "Horizontal"
        
        self.flip_modes = {
            "Horizontal": 1,
            "Vertical": 0,
            "Both": -1
        }

    def on_save(self) -> dict:
        return {
            "flip_mode": self.flip_mode
        }
    
    def on_load(self, data: dict):
        self.flip_mode = data["flip_mode"]
        self.update()

    def update_params(self):
        self.flip_mode = dpg.get_value(self.flip_mode_id)
        self.update()

    def compose(self):
        dpg.add_text("Flip Direction:")
        dpg.add_combo(
            items=list(self.flip_modes.keys()),
            default_value=self.flip_mode,
            callback=self.update_params,
            tag=self.flip_mode_id,
            width=185
        )

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask
        
        if image is None:
            return [NodePackage()]

        result = cv2.flip(image, self.flip_modes[self.flip_mode])
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