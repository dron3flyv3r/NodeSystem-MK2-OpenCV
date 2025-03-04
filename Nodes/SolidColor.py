import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class SolidColor(Node):
    def __init__(self):
        super().__init__("Solid Color", "Inputs", 200)
        self.add_output("image")
        
        # UI Controls
        self.color_id = dpg.generate_uuid()
        self.width_id = dpg.generate_uuid()
        self.height_id = dpg.generate_uuid()
        self.alpha_id = dpg.generate_uuid()
        
        # Default values
        self.color = (255, 255, 255, 255)
        self.width = 100
        self.height = 100
        self.use_alpha = False

    def on_save(self) -> dict:
        return {
            "color": self.color,
            "width": self.width,
            "height": self.height,
            "use_alpha": self.use_alpha
        }
    
    def on_load(self, data: dict):
        self.color = data["color"]
        self.width = data["width"]
        self.height = data["height"]
        self.use_alpha = data["use_alpha"]
        self.update()

    def update_params(self):
        self.color = dpg.get_value(self.color_id)
        self.width = dpg.get_value(self.width_id)
        self.height = dpg.get_value(self.height_id)
        self.use_alpha = dpg.get_value(self.alpha_id)
        self.update()

    def compose(self):
        dpg.add_color_picker(
            label="Color",
            default_value=self.color,
            callback=self.update_params,
            tag=self.color_id,
            width=185,
            no_alpha=True
        )
        dpg.add_input_int(
            label="Width",
            default_value=self.width,
            callback=self.update_params,
            tag=self.width_id,
            width=185,
            min_value=1
        )
        dpg.add_input_int(
            label="Height",
            default_value=self.height,
            callback=self.update_params,
            tag=self.height_id,
            width=185,
            min_value=1
        )
        dpg.add_checkbox(
            label="Use Alpha Channel",
            default_value=self.use_alpha,
            callback=self.update_params,
            tag=self.alpha_id
        )

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        # Create solid color image
        channels = 4 if self.use_alpha else 3
        image = np.zeros((self.height, self.width, channels), dtype=np.uint8)
        
        # Fill with color
        if self.use_alpha:
            image[:, :] = self.color
        else:
            image[:, :] = self.color[:3]

        return [NodePackage(image_or_mask=image)]

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