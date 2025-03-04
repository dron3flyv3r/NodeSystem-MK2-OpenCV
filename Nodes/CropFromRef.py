import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class CropFromRef(Node):
    def __init__(self):
        super().__init__("Crop From Reference", "Operations", 200)
        self.add_input("image")
        self.add_input("reference")
        self.add_output("image")
        
        # UI Controls
        self.interpolation_id = dpg.generate_uuid()
        self.maintain_aspect_id = dpg.generate_uuid()
        
        # Default values
        self.interpolation = "Linear"
        self.maintain_aspect = True
        
        self.interpolation_methods = {
            "Nearest": cv2.INTER_NEAREST,
            "Linear": cv2.INTER_LINEAR,
            "Cubic": cv2.INTER_CUBIC,
            "Area": cv2.INTER_AREA,
            "Lanczos": cv2.INTER_LANCZOS4
        }

    def on_save(self) -> dict:
        return {
            "interpolation": self.interpolation,
            "maintain_aspect": self.maintain_aspect
        }
    
    def on_load(self, data: dict):
        self.interpolation = data["interpolation"]
        self.maintain_aspect = data["maintain_aspect"]
        self.update()

    def update_params(self):
        self.interpolation = dpg.get_value(self.interpolation_id)
        self.maintain_aspect = dpg.get_value(self.maintain_aspect_id)
        self.update()

    def compose(self):
        dpg.add_text("Resize Parameters:")
        dpg.add_combo(
            label="Interpolation",
            items=list(self.interpolation_methods.keys()),
            default_value=self.interpolation,
            callback=self.update_params,
            tag=self.interpolation_id,
            width=185
        )
        dpg.add_checkbox(
            label="Maintain Aspect Ratio",
            default_value=self.maintain_aspect,
            callback=self.update_params,
            tag=self.maintain_aspect_id
        )

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        if len(inputs) < 2:
            return [NodePackage()]
            
        image_data = inputs[0]
        ref_data = inputs[1]
        
        image = image_data.image_or_mask
        reference = ref_data.image_or_mask
        
        if image is None or reference is None:
            return [NodePackage()]

        target_height, target_width = reference.shape[:2]
        
        if self.maintain_aspect:
            # Calculate the scaling factor while maintaining aspect ratio
            src_height, src_width = image.shape[:2]
            scale = min(target_width / src_width, target_height / src_height)
            
            new_width = int(src_width * scale)
            new_height = int(src_height * scale)
            
            # Resize maintaining aspect ratio
            resized = cv2.resize(image, (new_width, new_height), 
                               interpolation=self.interpolation_methods[self.interpolation])
            
            # Create a canvas of the target size
            if len(image.shape) == 3:
                result = np.zeros((target_height, target_width, image.shape[2]), dtype=image.dtype)
            else:
                result = np.zeros((target_height, target_width), dtype=image.dtype)
            
            # Calculate position to paste the resized image (center it)
            y_offset = (target_height - new_height) // 2
            x_offset = (target_width - new_width) // 2
            
            # Paste the resized image
            result[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized
        else:
            # Direct resize to target dimensions
            result = cv2.resize(image, (target_width, target_height),
                              interpolation=self.interpolation_methods[self.interpolation])

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