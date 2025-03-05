import cv2
import numpy as np
import dearpygui.dearpygui as dpg
from NodeEditor import Node, NodePackage

class ContourAnalysis(Node):
    def __init__(self):
        super().__init__("Contour Analysis", "Analytics", 250)
        self.add_input("image")
        self.add_output("image")  # Visualization output
        self.add_output("mask")   # Contour mask output
        
        # UI Controls
        self.mode_id = dpg.generate_uuid()
        self.method_id = dpg.generate_uuid()
        self.min_area_id = dpg.generate_uuid()
        self.draw_type_id = dpg.generate_uuid()
        
        # Default values
        self.mode = cv2.RETR_EXTERNAL
        self.method = cv2.CHAIN_APPROX_SIMPLE
        self.min_area = 100
        self.draw_type = "All Contours"
        
    def compose(self):
        dpg.add_text("Contour Mode:")
        dpg.add_combo(
            items=["External", "List", "Tree"],
            default_value="External",
            callback=self.update_params,
            tag=self.mode_id,
            width=185
        )
        
        dpg.add_text("Minimum Area:")
        dpg.add_input_float(
            default_value=self.min_area,
            callback=self.update_params,
            tag=self.min_area_id,
            width=185
        )
        
        dpg.add_text("Draw Type:")
        dpg.add_combo(
            items=["All Contours", "Largest Contour", "Convex Hull", "Bounding Boxes"],
            default_value=self.draw_type,
            callback=self.update_params,
            tag=self.draw_type_id,
            width=185
        )

    def update_params(self):
        mode_text = dpg.get_value(self.mode_id)
        self.mode = {
            "External": cv2.RETR_EXTERNAL,
            "List": cv2.RETR_LIST,
            "Tree": cv2.RETR_TREE
        }.get(mode_text, cv2.RETR_EXTERNAL)
        
        self.min_area = dpg.get_value(self.min_area_id)
        self.draw_type = dpg.get_value(self.draw_type_id)
        self.update()

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        if not inputs or inputs[0].image_or_mask is None:
            return [NodePackage(), NodePackage()]
            
        image = inputs[0].image_or_mask
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Find contours
        contours, _ = cv2.findContours(gray, self.mode, self.method)
        
        # Filter contours by area
        contours = [cnt for cnt in contours if cv2.contourArea(cnt) > self.min_area]
        
        # Create visualization
        if len(image.shape) == 2:
            vis_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            vis_image = image.copy()
            
        # Create mask
        mask = np.zeros(gray.shape, dtype=np.uint8)
        
        if contours:
            if self.draw_type == "All Contours":
                cv2.drawContours(vis_image, contours, -1, (0, 255, 0), 2)
                cv2.drawContours(mask, contours, -1, 255, -1) # type: ignore
            
            elif self.draw_type == "Largest Contour":
                largest = max(contours, key=cv2.contourArea)
                cv2.drawContours(vis_image, [largest], -1, (0, 255, 0), 2)
                cv2.drawContours(mask, [largest], -1, 255, -1) # type: ignore
            
            elif self.draw_type == "Convex Hull":
                for cnt in contours:
                    hull = cv2.convexHull(cnt)
                    cv2.drawContours(vis_image, [hull], -1, (0, 255, 0), 2)
                    cv2.drawContours(mask, [hull], -1, 255, -1) # type: ignore
            
            elif self.draw_type == "Bounding Boxes":
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(vis_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.rectangle(mask, (x, y), (x+w, y+h), 255, -1)

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