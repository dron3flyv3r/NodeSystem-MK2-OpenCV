import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class Morphological(Node):
    def __init__(self):
        super().__init__("Morphological", "Operations", 200)
        self.add_input("Mask", "mask")
        self.add_output("Mask", "mask")
        
        # UI Controls
        self.kernel_size_id = dpg.generate_uuid()
        self.iterations_id = dpg.generate_uuid()
        self.operation_id = dpg.generate_uuid()
        self.kernel_type_id = dpg.generate_uuid()
        
        # Default values
        self.kernel_size = 3
        self.iterations = 1
        self.operation = "Erosion"
        self.kernel_type = "Rect"
        
        self.operations = {
            "Erosion": cv2.MORPH_ERODE,
            "Dilation": cv2.MORPH_DILATE,
            "Opening": cv2.MORPH_OPEN,
            "Closing": cv2.MORPH_CLOSE
        }
        
        self.kernel_types = {
            "Rect": cv2.MORPH_RECT,
            "Cross": cv2.MORPH_CROSS,
            "Ellipse": cv2.MORPH_ELLIPSE
        }

    def on_save(self) -> dict:
        return {
            "kernel_size": self.kernel_size,
            "iterations": self.iterations,
            "operation": self.operation,
            "kernel_type": self.kernel_type
        }
    
    def on_load(self, data: dict):
        self.kernel_size = data["kernel_size"]
        self.iterations = data["iterations"]
        self.operation = data["operation"]
        self.kernel_type = data["kernel_type"]
        self.update()

    def update_params(self):
        self.kernel_size = dpg.get_value(self.kernel_size_id)
        self.iterations = dpg.get_value(self.iterations_id)
        self.operation = dpg.get_value(self.operation_id)
        self.kernel_type = dpg.get_value(self.kernel_type_id)
        self.update()

    def compose(self):
        dpg.add_text("Morphological Operation:")
        dpg.add_combo(items=list(self.operations.keys()), default_value=self.operation,
                     callback=self.update_params, tag=self.operation_id, width=185)
        
        dpg.add_text("Kernel Type:")
        dpg.add_combo(items=list(self.kernel_types.keys()), default_value=self.kernel_type,
                     callback=self.update_params, tag=self.kernel_type_id, width=185)
        
        dpg.add_input_int(label="Kernel Size", default_value=self.kernel_size,
                         min_value=1, callback=self.update_params, 
                         tag=self.kernel_size_id, width=185)
        
        dpg.add_input_int(label="Iterations", default_value=self.iterations,
                         min_value=1, callback=self.update_params, 
                         tag=self.iterations_id, width=185)

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask

        # Ensure kernel size is odd
        kernel_size = self.kernel_size if self.kernel_size % 2 == 1 else self.kernel_size + 1
        
        # Create kernel
        kernel = cv2.getStructuringElement(
            self.kernel_types[self.kernel_type],
            (kernel_size, kernel_size)
        )
        
        # Apply morphological operation
        result = cv2.morphologyEx(
            image,
            self.operations[self.operation],
            kernel,
            iterations=self.iterations
        ) if self.operation in ["Opening", "Closing"] else cv2.morphologyEx(
            image,
            cv2.MORPH_ERODE if self.operation == "Erosion" else cv2.MORPH_DILATE,
            kernel,
            iterations=self.iterations
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