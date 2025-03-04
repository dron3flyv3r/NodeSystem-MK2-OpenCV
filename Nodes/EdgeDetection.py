import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class EdgeDetection(Node):
    def __init__(self):
        super().__init__("Edge Detection", "Operations", 200)
        self.add_input("image")
        self.add_output("image")
        
        # UI Controls
        self.method_id = dpg.generate_uuid()
        self.low_threshold_id = dpg.generate_uuid()
        self.high_threshold_id = dpg.generate_uuid()
        self.x_order_id = dpg.generate_uuid()
        self.y_order_id = dpg.generate_uuid()
        self.ddepth_id = dpg.generate_uuid()
        
        # Default values
        self.method = "Canny"
        self.low_threshold = 100
        self.high_threshold = 200
        self.x_order = 1
        self.y_order = 1
        self.ddepth = 3

    def on_save(self) -> dict:
        return {
            "method": self.method,
            "low_threshold": self.low_threshold,
            "high_threshold": self.high_threshold,
            "x_order": self.x_order,
            "y_order": self.y_order,
            "ddepth": self.ddepth
        }
    
    def on_load(self, data: dict):
        self.method = data["method"]
        self.low_threshold = data["low_threshold"]
        self.high_threshold = data["high_threshold"]
        self.x_order = data["x_order"]
        self.y_order = data["y_order"]
        self.ddepth = data["ddepth"]
        self.update()

    def update_params(self):
        self.method = dpg.get_value(self.method_id)
        if self.method == "Canny":
            self.low_threshold = dpg.get_value(self.low_threshold_id)
            self.high_threshold = dpg.get_value(self.high_threshold_id)
        elif self.method == "Sobel":
            self.x_order = dpg.get_value(self.x_order_id)
            self.y_order = dpg.get_value(self.y_order_id)
        elif self.method == "Laplacian":
            self.ddepth = dpg.get_value(self.ddepth_id)
        self.update()

    def compose(self):
        dpg.add_text("Edge Detection Method:")
        dpg.add_combo(items=["Canny", "Sobel", "Laplacian"], default_value=self.method, 
                     callback=self.update_params, tag=self.method_id, width=185)
        
        if self.method == "Canny":
            dpg.add_text("Canny Parameters:")
            dpg.add_input_int(label="Low Threshold", default_value=self.low_threshold,
                            callback=self.update_params, tag=self.low_threshold_id, width=185)
            dpg.add_input_int(label="High Threshold", default_value=self.high_threshold,
                            callback=self.update_params, tag=self.high_threshold_id, width=185)
        elif self.method == "Sobel":
            dpg.add_text("Sobel Parameters:")
            dpg.add_input_int(label="X Order", default_value=self.x_order, min_value=0, max_value=2,
                            callback=self.update_params, tag=self.x_order_id, width=185)
            dpg.add_input_int(label="Y Order", default_value=self.y_order, min_value=0, max_value=2,
                            callback=self.update_params, tag=self.y_order_id, width=185)
        elif self.method == "Laplacian":
            dpg.add_text("Laplacian Parameters:")
            dpg.add_input_int(label="Depth", default_value=self.ddepth,
                            callback=self.update_params, tag=self.ddepth_id, width=185)

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask
        result = None

        # Convert to grayscale if needed
        if len(image.shape) > 2:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        if self.method == "Canny":
            result = cv2.Canny(gray, self.low_threshold, self.high_threshold)
        elif self.method == "Sobel":
            result = cv2.Sobel(gray, cv2.CV_64F, self.x_order, self.y_order)
            result = cv2.convertScaleAbs(result)
        elif self.method == "Laplacian":
            result = cv2.Laplacian(gray, self.ddepth)
            result = cv2.convertScaleAbs(result)
            
        if result is None:
            self.on_error("No result from edge detection")
            return [NodePackage()]

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