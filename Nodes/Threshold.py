import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class Threshold(Node):
    def __init__(self):
        super().__init__("Threshold", "Operations", 200)
        self.add_input("Image")
        self.add_output("Mask", "mask")
        
        # UI Controls
        self.threshold_type_id = dpg.generate_uuid()
        self.threshold_value_id = dpg.generate_uuid()
        self.max_value_id = dpg.generate_uuid()
        self.adaptive_method_id = dpg.generate_uuid()
        self.block_size_id = dpg.generate_uuid()
        self.c_value_id = dpg.generate_uuid()
        
        # Default values
        self.threshold_type = "Binary"
        self.threshold_value = 127
        self.max_value = 255
        self.adaptive_method = "Mean"
        self.block_size = 11
        self.c_value = 2
        
        self.threshold_types = {
            "Binary": cv2.THRESH_BINARY,
            "Binary Inverted": cv2.THRESH_BINARY_INV,
            "Truncate": cv2.THRESH_TRUNC,
            "To Zero": cv2.THRESH_TOZERO,
            "To Zero Inverted": cv2.THRESH_TOZERO_INV,
            "Adaptive": None,
            "Otsu": cv2.THRESH_BINARY + cv2.THRESH_OTSU
        }
        
        self.adaptive_methods = {
            "Mean": cv2.ADAPTIVE_THRESH_MEAN_C,
            "Gaussian": cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        }

    def on_save(self) -> dict:
        return {
            "threshold_type": self.threshold_type,
            "threshold_value": self.threshold_value,
            "max_value": self.max_value,
            "adaptive_method": self.adaptive_method,
            "block_size": self.block_size,
            "c_value": self.c_value
        }
    
    def on_load(self, data: dict):
        self.threshold_type = data["threshold_type"]
        self.threshold_value = data["threshold_value"]
        self.max_value = data["max_value"]
        self.adaptive_method = data["adaptive_method"]
        self.block_size = data["block_size"]
        self.c_value = data["c_value"]
        self.update()

    def update_params(self):
        self.threshold_type = dpg.get_value(self.threshold_type_id)
        self.threshold_value = dpg.get_value(self.threshold_value_id)
        self.max_value = dpg.get_value(self.max_value_id)
        self.adaptive_method = dpg.get_value(self.adaptive_method_id)
        self.block_size = dpg.get_value(self.block_size_id)
        self.c_value = dpg.get_value(self.c_value_id)
        self.update()

    def compose(self):
        dpg.add_text("Threshold Type:")
        dpg.add_combo(items=list(self.threshold_types.keys()), default_value=self.threshold_type,
                     callback=self.update_params, tag=self.threshold_type_id, width=185)
        
        # Shown if adaptive
        dpg.add_text("Adaptive Method:", show=False)
        dpg.add_combo(items=list(self.adaptive_methods.keys()), default_value=self.adaptive_method,
                        callback=self.update_params, tag=self.adaptive_method_id, width=185, show=False)
        dpg.add_input_int(label="Block Size", default_value=self.block_size,
                        min_value=3, max_value=99, callback=self.update_params,
                        tag=self.block_size_id, width=185, show=False)
        dpg.add_input_int(label="C Value", default_value=self.c_value,
                        callback=self.update_params, tag=self.c_value_id, width=185, show=False)
        
        # Shown if not adaptive
        dpg.add_input_int(label="Threshold Value", default_value=self.threshold_value,
                        min_value=0, max_value=255, callback=self.update_params,
                        tag=self.threshold_value_id, width=185)
            
        dpg.add_input_int(label="Max Value", default_value=self.max_value,
                         min_value=0, max_value=255, callback=self.update_params,
                         tag=self.max_value_id, width=185)

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask
        
        if image is None:
            return [NodePackage()]

        # Convert to grayscale if needed
        if len(image.shape) > 2:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Check if inputs need to be hidden or shown
        if self.threshold_type == "Adaptive":
            dpg.show_item(self.adaptive_method_id)
            dpg.show_item(self.block_size_id)
            dpg.show_item(self.c_value_id)
            dpg.hide_item(self.threshold_value_id)
            dpg.hide_item(self.max_value_id)
        else:
            dpg.hide_item(self.adaptive_method_id)
            dpg.hide_item(self.block_size_id)
            dpg.hide_item(self.c_value_id)
            dpg.show_item(self.threshold_value_id)
            dpg.show_item(self.max_value_id)

        if self.threshold_type == "Adaptive":
            # Ensure block size is odd
            block_size = self.block_size if self.block_size % 2 == 1 else self.block_size + 1
            result = cv2.adaptiveThreshold(
                gray,
                self.max_value,
                self.adaptive_methods[self.adaptive_method],
                cv2.THRESH_BINARY,
                block_size,
                self.c_value
            )
        elif self.threshold_type == "Otsu":
            _, result = cv2.threshold(
                gray,
                0,  # Ignored when using Otsu's method
                self.max_value,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
        else:
            _, result = cv2.threshold(
                gray,
                self.threshold_value,
                self.max_value,
                self.threshold_types[self.threshold_type]
            )

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
