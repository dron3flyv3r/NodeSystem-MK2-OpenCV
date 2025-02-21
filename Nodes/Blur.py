import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class Blur(Node):
    def __init__(self):
        super().__init__("Blur", "Operations", 200)
        self.add_input("image")
        self.add_output("image")
        self.blur_amount_input = dpg.generate_uuid()
        self.blur_type_id = dpg.generate_uuid()
        self.blur_amount = 5
        self.blur_type = "Gaussian"
        
        self.blur_types = {
            "Gaussian": cv2.GaussianBlur,
            "Median": cv2.medianBlur,
            "Bilateral": cv2.bilateralFilter,
            "Box": cv2.boxFilter,
        }
        
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

    def compose(self):
        dpg.add_text("Blur Amount:")
        dpg.add_input_int(default_value=self.blur_amount, callback=self.update_blur, tag=self.blur_amount_input, width=185)
        dpg.add_text("Blur Type:")
        dpg.add_combo(items=list(self.blur_types.keys()), default_value="Gaussian", callback=self.update_blur, tag=self.blur_type_id, width=185)

    def update_blur(self):
        self.blur_amount = dpg.get_value(self.blur_amount_input)
        self.blur_type = dpg.get_value(self.blur_type_id)
        self.update()

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask
        
        self.blur_amount = self.blur_amount if self.blur_amount % 2 == 1 else self.blur_amount + 1

        match self.blur_type:
            case "Gaussian":
                blurred_image = cv2.GaussianBlur(image, (self.blur_amount, self.blur_amount), 0)
            case "Median":
                blurred_image = cv2.medianBlur(image, self.blur_amount)
            case "Bilateral":
                blurred_image = cv2.bilateralFilter(image, self.blur_amount, 75, 75)
            case "Box":
                blurred_image = cv2.boxFilter(image, -1, (self.blur_amount, self.blur_amount))
            case _:
                blurred_image = image

        return [NodePackage(image_or_mask=blurred_image)]
