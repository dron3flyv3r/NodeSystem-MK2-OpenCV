import random
import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class ConnectedComponents(Node):
    def __init__(self):
        super().__init__("Connected Components", "Analysis", 200)
        self.add_input("Mask", "mask")
        self.add_output("Mask", "mask")
        
        # UI Controls
        self.num_components_id = dpg.generate_uuid()
        self.color_components_id = dpg.generate_uuid()
        
        
        
        # Default values
        self.num_components = 0
        self.color_components = False

    def on_save(self) -> dict:
        return {
            "color_components": dpg.get_value(self.color_components_id),
        }
    
    def on_load(self, data: dict):
        
        dpg.set_value(self.color_components_id, data["color_components"])
        
        self.update()
        
    def compose(self):
        dpg.add_text("Count: 0", tag=self.num_components_id)
        dpg.add_checkbox(label="Colored", callback=self.update, tag=self.color_components_id)

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        
        img = inputs[0].image_or_mask
        
        if len(img.shape) < 2:
            self.on_error("The image is not binary")
            return inputs
        
        num_labels, labels = cv2.connectedComponents(img)
        self.num_components = num_labels
        dpg.set_value(self.num_components_id, f"Count: {self.num_components}")

        output_image = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
        
        if dpg.get_value(self.color_components_id):
            for label in range(1, num_labels):  # Start from 1 to skip the background
                # Generate a random color (R, G, B)
                random_color = [random.randint(0, 255) for _ in range(3)]
                
                # Apply the random color to all pixels belonging to the current label
                output_image[labels == label] = random_color
                return [NodePackage(output_image)]
        return [NodePackage(labels)]
        
        

    def viewer(self, outputs: list[NodePackage]):
        # Display both the visualization and the labels
        for i, data in enumerate(outputs):
            img_tag = dpg.generate_uuid()
            with dpg.texture_registry():
                dpg.add_dynamic_texture(400, 400, [0.0, 0.0, 0.0, 0.0]*400*400, tag=img_tag)
            
            dpg.add_text("Visualization" if i == 0 else "Labels")
            dpg.add_image(img_tag)
            
            image_rgba = data.copy_resize((400, 400), keep_alpha=True)
            image_rgba = image_rgba.astype(float)
            image_rgba /= 255

            dpg.set_value(img_tag, image_rgba.flatten())