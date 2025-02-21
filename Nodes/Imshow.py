import cv2
import uuid

from NodeEditor import Node, NodePackage, dpg

class Imshow(Node):
    
    full_image: cv2.typing.MatLike | None = None
    
    def __init__(self) -> None:
        super().__init__("Imshow", "Outputs", 400)
        self.image_input = dpg.generate_uuid()
        self.path = dpg.generate_uuid()
        self.add_input("image")
        
    def save_image(self):
        if self.full_image is None:
            return
        
        path = f"image_{uuid.uuid4().hex}.png"
        cv2.imwrite(path, self.full_image)
        
    def compose(self):        
        with dpg.texture_registry():
            dpg.add_dynamic_texture(400, 400, [0.0, 0.0, 0.0, 0.0]*400*400, tag=self.image_input)
            
        dpg.add_image(self.image_input)
        
        dpg.add_button(label="Save Image", callback=self.save_image)
        
    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        
        image = data.image_or_mask
        self.full_image = image
        rgba_image = image if len(image.shape) == 4 else cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
        
        max_dim = max(image.shape[0], image.shape[1])
        max_dim = max_dim if max_dim > 400 else 400
        scale = 400 / max_dim
        rgba_image = cv2.resize(rgba_image, (int(image.shape[1] * scale), int(image.shape[0] * scale)))
        
        top = (400 - rgba_image.shape[0]) // 2
        bottom = 400 - top - rgba_image.shape[0]
        left = (400 - rgba_image.shape[1]) // 2
        right = 400 - left - rgba_image.shape[1]
        rgba_image = cv2.copyMakeBorder(rgba_image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0, 0])
                
        rgba_image = rgba_image.astype(float)
        rgba_image /= 255
        dpg.set_value(self.image_input, rgba_image.flatten())
                        
        return [data]