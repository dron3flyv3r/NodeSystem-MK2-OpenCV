import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class ShapeFinder(Node):
    def __init__(self):
        super().__init__("Shape Finder", "Analysis", 200)
        self.add_input("image")
        self.add_output("image")
        self.add_output("mask")
        
        # UI Controls
        self.min_area_id = dpg.generate_uuid()
        self.max_area_id = dpg.generate_uuid()
        self.epsilon_factor_id = dpg.generate_uuid()
        self.min_vertices_id = dpg.generate_uuid()
        self.max_vertices_id = dpg.generate_uuid()
        self.draw_contours_id = dpg.generate_uuid()
        self.draw_centroids_id = dpg.generate_uuid()
        self.fill_shapes_id = dpg.generate_uuid()
        
        # Default values
        self.min_area = 100
        self.max_area = 10000
        self.epsilon_factor = 0.02
        self.min_vertices = 3
        self.max_vertices = 8
        self.draw_contours = True
        self.draw_centroids = True
        self.fill_shapes = False

    def on_save(self) -> dict:
        return {
            "min_area": self.min_area,
            "max_area": self.max_area,
            "epsilon_factor": self.epsilon_factor,
            "min_vertices": self.min_vertices,
            "max_vertices": self.max_vertices,
            "draw_contours": self.draw_contours,
            "draw_centroids": self.draw_centroids,
            "fill_shapes": self.fill_shapes
        }
    
    def on_load(self, data: dict):
        self.min_area = data["min_area"]
        self.max_area = data["max_area"]
        self.epsilon_factor = data["epsilon_factor"]
        self.min_vertices = data["min_vertices"]
        self.max_vertices = data["max_vertices"]
        self.draw_contours = data["draw_contours"]
        self.draw_centroids = data["draw_centroids"]
        self.fill_shapes = data["fill_shapes"]
        self.update()

    def update_params(self):
        self.min_area = dpg.get_value(self.min_area_id)
        self.max_area = dpg.get_value(self.max_area_id)
        self.epsilon_factor = dpg.get_value(self.epsilon_factor_id)
        self.min_vertices = dpg.get_value(self.min_vertices_id)
        self.max_vertices = dpg.get_value(self.max_vertices_id)
        self.draw_contours = dpg.get_value(self.draw_contours_id)
        self.draw_centroids = dpg.get_value(self.draw_centroids_id)
        self.fill_shapes = dpg.get_value(self.fill_shapes_id)
        self.update()

    def compose(self):
        dpg.add_text("Area Constraints:")
        dpg.add_input_int(
            label="Min Area",
            default_value=self.min_area,
            callback=self.update_params,
            tag=self.min_area_id,
            width=185
        )
        dpg.add_input_int(
            label="Max Area",
            default_value=self.max_area,
            callback=self.update_params,
            tag=self.max_area_id,
            width=185
        )
        
        dpg.add_text("Shape Parameters:")
        dpg.add_input_float(
            label="Epsilon Factor",
            default_value=self.epsilon_factor,
            callback=self.update_params,
            tag=self.epsilon_factor_id,
            width=185
        )
        dpg.add_input_int(
            label="Min Vertices",
            default_value=self.min_vertices,
            min_value=3,
            callback=self.update_params,
            tag=self.min_vertices_id,
            width=185
        )
        dpg.add_input_int(
            label="Max Vertices",
            default_value=self.max_vertices,
            min_value=3,
            callback=self.update_params,
            tag=self.max_vertices_id,
            width=185
        )
        
        dpg.add_text("Visualization:")
        dpg.add_checkbox(
            label="Draw Contours",
            default_value=self.draw_contours,
            callback=self.update_params,
            tag=self.draw_contours_id
        )
        dpg.add_checkbox(
            label="Draw Centroids",
            default_value=self.draw_centroids,
            callback=self.update_params,
            tag=self.draw_centroids_id
        )
        dpg.add_checkbox(
            label="Fill Shapes",
            default_value=self.fill_shapes,
            callback=self.update_params,
            tag=self.fill_shapes_id
        )

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask
        
        if image is None:
            return [NodePackage(), NodePackage()]

        # Convert to grayscale if needed
        if len(image.shape) > 2:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Create a binary image
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create mask and visualization image
        mask = np.zeros_like(gray)
        result = image.copy() if len(image.shape) > 2 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if self.min_area <= area <= self.max_area:
                # Approximate the contour
                epsilon = self.epsilon_factor * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                vertices = len(approx)
                if self.min_vertices <= vertices <= self.max_vertices:
                    # Draw on mask
                    cv2.drawContours(mask, [approx], -1, 255, -1 if self.fill_shapes else 2) # type: ignore
                    
                    # Draw on result image
                    if self.draw_contours:
                        cv2.drawContours(result, [approx], -1, (0, 255, 0), 2)
                    
                    if self.draw_centroids:
                        M = cv2.moments(approx)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            cv2.circle(result, (cx, cy), 5, (255, 0, 0), -1)
        
        return [NodePackage(image_or_mask=result), NodePackage(image_or_mask=mask)]

    def viewer(self, outputs: list[NodePackage]):
        # Display both the result image and the mask
        for i, data in enumerate(outputs):
            img_tag = dpg.generate_uuid()
            with dpg.texture_registry():
                dpg.add_dynamic_texture(400, 400, [0.0, 0.0, 0.0, 0.0]*400*400, tag=img_tag)
            
            dpg.add_text("Result" if i == 0 else "Mask")
            dpg.add_image(img_tag)
            
            image_rgba = data.copy_resize((400, 400), keep_alpha=True)
            image_rgba = image_rgba.astype(float)
            image_rgba /= 255

            dpg.set_value(img_tag, image_rgba.flatten())