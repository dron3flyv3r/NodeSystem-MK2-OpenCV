import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class MinimumDensity(Node):
    def __init__(self):
        super().__init__("Minimum Density", "Analysis", 200)
        self.add_input("image")
        self.add_output("mask", "mask")
        
        # UI Controls
        self.threshold_id = dpg.generate_uuid()
        self.avg_density_id = dpg.generate_uuid()
        self.relative_threshold_id = dpg.generate_uuid()
        self.invert_id = dpg.generate_uuid()
        
        # Default values
        self.threshold = 100
        self.avg_density = 0
        self.use_relative_threshold = False
        self.invert = False

    def on_save(self) -> dict:
        return {
            "threshold": self.threshold,
            "use_relative_threshold": self.use_relative_threshold,
            "invert": self.invert
        }
    
    def on_load(self, data: dict):
        self.threshold = data["threshold"]
        self.use_relative_threshold = data["use_relative_threshold"]
        self.invert = data["invert"]
        self.update()

    def update_params(self):
        self.threshold = dpg.get_value(self.threshold_id)
        self.use_relative_threshold = dpg.get_value(self.relative_threshold_id)
        self.invert = dpg.get_value(self.invert_id)
        self.update()

    def compose(self):
        dpg.add_text("Average Component Size:", tag=self.avg_density_id)
        dpg.add_input_float(
            label="Size Threshold",
            default_value=self.threshold,
            callback=self.update_params,
            tag=self.threshold_id,
            width=185
        )
        dpg.add_checkbox(
            label="Use Relative Threshold",
            default_value=self.use_relative_threshold,
            callback=self.update_params,
            tag=self.relative_threshold_id
        )
        dpg.add_checkbox(
            label="Invert Selection",
            default_value=self.invert,
            callback=self.update_params,
            tag=self.invert_id
        )

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask
        
        if image is None:
            return [NodePackage()]

        # Convert to binary if needed
        if len(image.shape) > 2:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        else:
            _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)

        # Get connected components with stats
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            binary, connectivity=8
        )

        # Get component sizes (excluding background)
        component_sizes = stats[1:, cv2.CC_STAT_AREA]
        
        # Update average density display
        if len(component_sizes) > 0:
            self.avg_density = np.mean(component_sizes)
        else:
            self.avg_density = 0
        dpg.configure_item(self.avg_density_id, 
                         label=f"Average Component Size: {self.avg_density:.1f}")

        # Create output mask
        result = np.zeros_like(binary)
        
        # Calculate threshold value
        threshold_value = (self.threshold * self.avg_density 
                         if self.use_relative_threshold 
                         else self.threshold)

        # Apply density filtering
        for i in range(1, num_labels):  # Skip background (label 0)
            if self.invert:
                if stats[i, cv2.CC_STAT_AREA] < threshold_value:
                    result[labels == i] = 255
            else:
                if stats[i, cv2.CC_STAT_AREA] >= threshold_value:
                    result[labels == i] = 255

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