import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class ConvertImage(Node):
    def __init__(self):
        super().__init__("Convert Image", "Operations", 200)
        self.add_input("image")
        self.add_output("image")
        
        self.color_space_to_id = dpg.generate_uuid()
        self.color_space_from_id = dpg.generate_uuid()
        
        self.color_spaces = {
            "RGB": cv2.COLOR_BGR2RGB,
            "BGR": cv2.COLOR_RGB2BGR,
            "GRAY": cv2.COLOR_BGR2GRAY,
            "RGBA": cv2.COLOR_BGR2RGBA,
            "BGRA": cv2.COLOR_BGR2BGRA,
            "AUTO": None
        }
        
        self.color_space_to = "BGRA"
        self.color_space_from = "AUTO"

    def on_save(self) -> dict:
        return {
            "color_space_to": self.color_space_to,
            "color_space_from": self.color_space_from
        }
    
    def on_load(self, data: dict):
        self.color_space_to = data["color_space_to"]
        self.color_space_from = data["color_space_from"]
        self.update()

    def update_params(self):
        self.color_space_to = dpg.get_value(self.color_space_to_id)
        self.color_space_from = dpg.get_value(self.color_space_from_id)
        self.update()

    def compose(self):
        dpg.add_text("Color Space Conversion:")
        dpg.add_combo(label="From", items=list(self.color_spaces.keys()), 
                     default_value=self.color_space_from,
                     callback=self.update_params, tag=self.color_space_from_id, width=185)
        dpg.add_combo(label="To", items=list(self.color_spaces.keys())[:-1], 
                     default_value=self.color_space_to,
                     callback=self.update_params, tag=self.color_space_to_id, width=185)

    def get_conversion_code(self, from_space: str, to_space: str) -> int | None:
        if from_space == "AUTO":
            # Auto-detect based on image channels
            return None
        
        conversions = {
            ("RGB", "BGR"): cv2.COLOR_RGB2BGR,
            ("RGB", "GRAY"): cv2.COLOR_RGB2GRAY,
            ("RGB", "RGBA"): cv2.COLOR_RGB2RGBA,
            ("RGB", "BGRA"): cv2.COLOR_RGB2BGRA,
            ("BGR", "RGB"): cv2.COLOR_BGR2RGB,
            ("BGR", "GRAY"): cv2.COLOR_BGR2GRAY,
            ("BGR", "RGBA"): cv2.COLOR_BGR2RGBA,
            ("BGR", "BGRA"): cv2.COLOR_BGR2BGRA,
            ("GRAY", "RGB"): cv2.COLOR_GRAY2RGB,
            ("GRAY", "BGR"): cv2.COLOR_GRAY2BGR,
            ("GRAY", "RGBA"): cv2.COLOR_GRAY2RGBA,
            ("GRAY", "BGRA"): cv2.COLOR_GRAY2BGRA,
            ("RGBA", "RGB"): cv2.COLOR_RGBA2RGB,
            ("RGBA", "BGR"): cv2.COLOR_RGBA2BGR,
            ("RGBA", "GRAY"): cv2.COLOR_RGBA2GRAY,
            ("RGBA", "BGRA"): cv2.COLOR_RGBA2BGRA,
            ("BGRA", "RGB"): cv2.COLOR_BGRA2RGB,
            ("BGRA", "BGR"): cv2.COLOR_BGRA2BGR,
            ("BGRA", "GRAY"): cv2.COLOR_BGRA2GRAY,
            ("BGRA", "RGBA"): cv2.COLOR_BGRA2RGBA,
        }
        return conversions.get((from_space, to_space))

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask

        if self.color_space_from == "AUTO":
            # Auto-detect based on image channels
            channels = 1 if len(image.shape) == 2 else image.shape[2]
            if channels == 1:
                from_space = "GRAY"
            elif channels == 3:
                from_space = "BGR"  # OpenCV default
            else:
                from_space = "BGRA"
        else:
            from_space = self.color_space_from

        conversion_code = self.get_conversion_code(from_space, self.color_space_to)
        if conversion_code is not None:
            result = cv2.cvtColor(image, conversion_code)
        else:
            result = image  # No conversion needed

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