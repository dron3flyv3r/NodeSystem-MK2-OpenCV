import cv2
import numpy as np
import dearpygui.dearpygui as dpg
from NodeEditor import Node, NodePackage

class TemplateMatcher(Node):
    def __init__(self):
        super().__init__("Template Matcher", "Analytics", 250)
        self.add_input("image", "image")
        self.add_input("template", "template")
        self.add_output("image", "Visualization")
        self.add_output("mask", "mask")
        
        # UI Controls
        self.method_id = dpg.generate_uuid()
        self.threshold_id = dpg.generate_uuid()
        self.max_matches_id = dpg.generate_uuid()
        
        # Default values
        self.method = cv2.TM_CCOEFF_NORMED
        self.threshold = 0.8
        self.max_matches = 3
        
    def compose(self):
        dpg.add_text("Match Method:")
        dpg.add_combo(
            items=["TM_CCOEFF_NORMED", "TM_CCORR_NORMED", "TM_SQDIFF_NORMED"],
            default_value="TM_CCOEFF_NORMED",
            callback=self.update_params,
            tag=self.method_id,
            width=185
        )
        
        dpg.add_text("Threshold:")
        dpg.add_slider_float(
            default_value=self.threshold,
            min_value=0.1,
            max_value=1.0,
            callback=self.update_params,
            tag=self.threshold_id,
            width=185
        )
        
        dpg.add_text("Max Matches:")
        dpg.add_input_int(
            default_value=self.max_matches,
            min_value=1,
            max_value=20,
            callback=self.update_params,
            tag=self.max_matches_id,
            width=185
        )

    def update_params(self):
        method_text = dpg.get_value(self.method_id)
        self.method = {
            "TM_CCOEFF_NORMED": cv2.TM_CCOEFF_NORMED,
            "TM_CCORR_NORMED": cv2.TM_CCORR_NORMED,
            "TM_SQDIFF_NORMED": cv2.TM_SQDIFF_NORMED
        }.get(method_text, cv2.TM_CCOEFF_NORMED)
        
        self.threshold = dpg.get_value(self.threshold_id)
        self.max_matches = dpg.get_value(self.max_matches_id)
        self.update()

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        if len(inputs) < 2 or inputs[0].image_or_mask is None or inputs[1].image_or_mask is None:
            return [NodePackage(), NodePackage()]
            
        image = inputs[0].image_or_mask
        template = inputs[1].image_or_mask
        
        # Convert both to grayscale if needed
        if len(image.shape) == 3:
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = image.copy()
            
        if len(template.shape) == 3:
            gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            gray_template = template.copy()
            
        # Match template
        result = cv2.matchTemplate(gray_image, gray_template, self.method)
        
        # Find matches
        if self.method == cv2.TM_SQDIFF_NORMED:
            matches = np.where(result <= 1.0 - self.threshold)
        else:
            matches = np.where(result >= self.threshold)
            
        # Create visualization and mask
        if len(image.shape) == 2:
            vis_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            vis_image = image.copy()
            
        mask = np.zeros(gray_image.shape, dtype=np.uint8)
        h, w = template.shape[:2]
        
        # Draw rectangles around matches
        matches_list = list(zip(*matches[::-1]))
        matches_list = sorted(matches_list, key=lambda x: result[x[1], x[0]], reverse=True) # type: ignore
        matches_list = matches_list[:self.max_matches]
        
        for pt in matches_list:
            cv2.rectangle(vis_image, pt, (pt[0] + w, pt[1] + h), (0, 255, 0), 2)
            cv2.rectangle(mask, pt, (pt[0] + w, pt[1] + h), 255, -1)

        return [NodePackage(image_or_mask=vis_image), NodePackage(image_or_mask=mask)]

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