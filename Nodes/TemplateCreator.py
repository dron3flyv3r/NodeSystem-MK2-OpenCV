import cv2
import numpy as np
import dearpygui.dearpygui as dpg
from NodeEditor import Node, NodePackage
import os

class TemplateCreator(Node):
    def __init__(self):
        super().__init__("Template Creator", "Analytics", 250)
        self.add_input("image", "image")
        self.add_output("image", "image")
        self.add_output("template", "template")
        
        # UI Controls
        self.x_id = dpg.generate_uuid()
        self.y_id = dpg.generate_uuid()
        self.width_id = dpg.generate_uuid()
        self.height_id = dpg.generate_uuid()
        self.save_id = dpg.generate_uuid()
        self.template_name_id = dpg.generate_uuid()
        self.load_id = dpg.generate_uuid()
        self.templates_combo_id = dpg.generate_uuid()
        
        # Default values
        self.x = 0
        self.y = 0
        self.width = 100
        self.height = 100
        self.template_name = "template1"
        self.templates_dir = "templates"
        self.templates_list = []
        
        # Create templates directory if it doesn't exist
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            
        # Load existing templates
        self.update_templates_list()
        
    def update_templates_list(self):
        if os.path.exists(self.templates_dir):
            self.templates_list = [f for f in os.listdir(self.templates_dir) 
                                 if f.endswith(('.png', '.jpg', '.jpeg'))]
        
    def compose(self):
        dpg.add_text("Template Region:")
        dpg.add_input_int(
            label="X",
            default_value=self.x,
            callback=self.update_params,
            tag=self.x_id,
            width=185
        )
        dpg.add_input_int(
            label="Y",
            default_value=self.y,
            callback=self.update_params,
            tag=self.y_id,
            width=185
        )
        dpg.add_input_int(
            label="Width",
            default_value=self.width,
            callback=self.update_params,
            tag=self.width_id,
            width=185
        )
        dpg.add_input_int(
            label="Height",
            default_value=self.height,
            callback=self.update_params,
            tag=self.height_id,
            width=185
        )
        
        dpg.add_separator()
        dpg.add_text("Save Template:")
        dpg.add_input_text(
            label="Name",
            default_value=self.template_name,
            callback=self.update_params,
            tag=self.template_name_id,
            width=185
        )
        dpg.add_button(
            label="Save Template",
            callback=self.save_template,
            tag=self.save_id,
            width=185
        )
        
        dpg.add_separator()
        dpg.add_text("Load Template:")
        dpg.add_combo(
            items=self.templates_list,
            callback=self.load_template,
            tag=self.templates_combo_id,
            width=185
        )

    def update_params(self):
        self.x = max(0, dpg.get_value(self.x_id))
        self.y = max(0, dpg.get_value(self.y_id))
        self.width = max(1, dpg.get_value(self.width_id))
        self.height = max(1, dpg.get_value(self.height_id))
        self.template_name = dpg.get_value(self.template_name_id)
        self.update()
        
    def save_template(self):
        if not self.current_template is None:
            if not self.template_name.endswith(('.png', '.jpg', '.jpeg')):
                self.template_name += '.png'
            
            save_path = os.path.join(self.templates_dir, self.template_name)
            cv2.imwrite(save_path, self.current_template)
            
            # Update templates list
            self.update_templates_list()
            dpg.configure_item(self.templates_combo_id, items=self.templates_list)
            
    def load_template(self):
        selected = dpg.get_value(self.templates_combo_id)
        if selected:
            template_path = os.path.join(self.templates_dir, selected)
            if os.path.exists(template_path):
                self.current_template = cv2.imread(template_path)
                self.update()

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        if not inputs or inputs[0].image_or_mask is None:
            return [NodePackage(), NodePackage()]
            
        image = inputs[0].image_or_mask
        h, w = image.shape[:2]
        
        # Constrain selection to image bounds
        self.x = min(max(0, self.x), w - 1)
        self.y = min(max(0, self.y), h - 1)
        self.width = min(self.width, w - self.x)
        self.height = min(self.height, h - self.y)
        
        # Create visualization
        vis_image = image.copy()
        cv2.rectangle(vis_image, 
                     (self.x, self.y), 
                     (self.x + self.width, self.y + self.height),
                     (0, 255, 0), 2)
        
        # Extract template region
        self.current_template = image[self.y:self.y + self.height,
                                    self.x:self.x + self.width].copy()
        
        return [NodePackage(image_or_mask=vis_image),
                NodePackage(image_or_mask=self.current_template)]

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