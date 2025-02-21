import cv2

from NodeEditor import Node, NodePackage, dpg

import cv2
import dearpygui.dearpygui as dpg

from NodeEditor.Core.Node import Node
from NodeEditor.Core.NodePackage import NodePackage



class Imread(Node):
    image: cv2.typing.MatLike
    
    def __init__(self):
        super().__init__("Imread", "Inputs", 400)
        self.file_path = dpg.generate_uuid()
        self.image_view = dpg.generate_uuid()
        self.image_type = dpg.generate_uuid()
        self.image_selected = ""
        self.add_output("image", "Image")
        
    def on_save(self) -> dict:
        return {
            "image_selected": self.image_selected,
        }
        
    def on_load(self, data: dict):
        self.image_selected = data["image_selected"]
        self.set_file_path(None, None)
        
    def set_file_path(self, sender, app_data):

        if app_data and "selections" in app_data:
            for i in app_data["selections"].values():
                self.image_selected = i
                break
        elif self.image_selected == "":
            return
        
        image_type = dpg.get_value(self.image_type)
        match image_type:
            case "Color":
                self.image = cv2.imread(self.image_selected, cv2.IMREAD_COLOR)
                rgba_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGBA)
                
            case "Grayscale":
                self.image = cv2.imread(self.image_selected, cv2.IMREAD_GRAYSCALE)
                rgba_image = cv2.cvtColor(self.image, cv2.COLOR_GRAY2BGRA)
                
            case "Alpha":
                self.image = cv2.imread(self.image_selected, cv2.IMREAD_UNCHANGED)
                rgba_image = cv2.cvtColor(self.image, cv2.COLOR_BGRA2RGBA)
                
            case _:
                self.image = cv2.imread(self.image_selected)
                rgba_image = cv2.cvtColor(self.image, cv2.COLOR_BGRA2RGBA)
                
        
        max_dim = max(self.image.shape[0], self.image.shape[1])
        
        # Make so the max dimension is 400
        max_dim = max_dim if max_dim > 400 else 400
        scale = 400 / max_dim
        rgba_image = cv2.resize(rgba_image, (int(self.image.shape[1] * scale), int(self.image.shape[0] * scale)))
        
        # Add padding to the image so it is 400x400 with the resized image in the center
        top = (400 - rgba_image.shape[0]) // 2
        bottom = 400 - top - rgba_image.shape[0]
        left = (400 - rgba_image.shape[1]) // 2
        right = 400 - left - rgba_image.shape[1]
        rgba_image = cv2.copyMakeBorder(rgba_image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0, 0])        
        
        rgba_image = rgba_image.astype(float)
        rgba_image /= 255
        dpg.set_value(self.image_view, rgba_image.flatten())
        self.update()
        
    def compose(self):
        with dpg.file_dialog(directory_selector=False, show=False, callback=self.set_file_path, tag=self.file_path, file_count=1, width=700, height=400):
            # Source files (*.cpp *.h *.hpp){.cpp,.h,.hpp} 
            dpg.add_file_extension("Image Files (*.jpg *.png *.jpeg){.jpg,.png,.jpeg}")
            
        dpg.add_button(label="Select Image", callback=lambda: dpg.show_item(self.file_path))
        
        with dpg.texture_registry():
            dpg.add_dynamic_texture(400, 400, [0.0, 0.0, 0.0, 255.0] * 400 * 400, tag=self.image_view)
        
        dpg.add_combo(label="Import Type", items=["Color", "Grayscale", "Alpha"], default_value="Color", tag=self.image_type, width=200, callback=self.set_file_path)
        dpg.add_image(self.image_view, width=400, height=400)
                
        
    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        return [NodePackage(image_or_mask=self.image)]