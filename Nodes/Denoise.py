import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class Denoise(Node):
    def __init__(self):
        super().__init__("Denoise", "Operations", 200)
        self.add_input("image")
        self.add_output("image")
        
        # UI Controls
        self.denoise_type_id = dpg.generate_uuid()
        self.blur_amount_id = dpg.generate_uuid()
        self.bilateral_diameter_id = dpg.generate_uuid()
        self.bilateral_sigma_color_id = dpg.generate_uuid()
        self.bilateral_sigma_space_id = dpg.generate_uuid()
        self.nlmeans_h_id = dpg.generate_uuid()
        self.nlmeans_template_size_id = dpg.generate_uuid()
        self.nlmeans_search_size_id = dpg.generate_uuid()
        
        # Default values
        self.denoise_type = "Gaussian Blur"
        self.blur_amount = 5
        self.bilateral_diameter = 9
        self.bilateral_sigma_color = 75
        self.bilateral_sigma_space = 75
        self.nlmeans_h = 3
        self.nlmeans_template_size = 7
        self.nlmeans_search_size = 21

    def on_save(self) -> dict:
        return {
            "denoise_type": self.denoise_type,
            "blur_amount": self.blur_amount,
            "bilateral_diameter": self.bilateral_diameter,
            "bilateral_sigma_color": self.bilateral_sigma_color,
            "bilateral_sigma_space": self.bilateral_sigma_space,
            "nlmeans_h": self.nlmeans_h,
            "nlmeans_template_size": self.nlmeans_template_size,
            "nlmeans_search_size": self.nlmeans_search_size
        }
    
    def on_load(self, data: dict):
        self.denoise_type = data["denoise_type"]
        self.blur_amount = data["blur_amount"]
        self.bilateral_diameter = data["bilateral_diameter"]
        self.bilateral_sigma_color = data["bilateral_sigma_color"]
        self.bilateral_sigma_space = data["bilateral_sigma_space"]
        self.nlmeans_h = data["nlmeans_h"]
        self.nlmeans_template_size = data["nlmeans_template_size"]
        self.nlmeans_search_size = data["nlmeans_search_size"]
        self.update()

    def update_params(self):
        self.denoise_type = dpg.get_value(self.denoise_type_id)
        if self.denoise_type in ["Gaussian Blur", "Median Blur"]:
            self.blur_amount = dpg.get_value(self.blur_amount_id)
        elif self.denoise_type == "Bilateral Filter":
            self.bilateral_diameter = dpg.get_value(self.bilateral_diameter_id)
            self.bilateral_sigma_color = dpg.get_value(self.bilateral_sigma_color_id)
            self.bilateral_sigma_space = dpg.get_value(self.bilateral_sigma_space_id)
        elif self.denoise_type == "Non-local Means":
            self.nlmeans_h = dpg.get_value(self.nlmeans_h_id)
            self.nlmeans_template_size = dpg.get_value(self.nlmeans_template_size_id)
            self.nlmeans_search_size = dpg.get_value(self.nlmeans_search_size_id)
        self.update()

    def compose(self):
        dpg.add_text("Denoise Method:")
        dpg.add_combo(
            items=["Gaussian Blur", "Median Blur", "Bilateral Filter", "Non-local Means"],
            default_value=self.denoise_type,
            callback=self.update_params,
            tag=self.denoise_type_id,
            width=185
        )
        
        if self.denoise_type in ["Gaussian Blur", "Median Blur"]:
            dpg.add_input_int(
                label="Blur Amount",
                default_value=self.blur_amount,
                min_value=1,
                callback=self.update_params,
                tag=self.blur_amount_id,
                width=185
            )
        elif self.denoise_type == "Bilateral Filter":
            dpg.add_input_int(
                label="Diameter",
                default_value=self.bilateral_diameter,
                min_value=1,
                callback=self.update_params,
                tag=self.bilateral_diameter_id,
                width=185
            )
            dpg.add_input_float(
                label="Sigma Color",
                default_value=self.bilateral_sigma_color,
                callback=self.update_params,
                tag=self.bilateral_sigma_color_id,
                width=185
            )
            dpg.add_input_float(
                label="Sigma Space",
                default_value=self.bilateral_sigma_space,
                callback=self.update_params,
                tag=self.bilateral_sigma_space_id,
                width=185
            )
        elif self.denoise_type == "Non-local Means":
            dpg.add_input_float(
                label="H value",
                default_value=self.nlmeans_h,
                callback=self.update_params,
                tag=self.nlmeans_h_id,
                width=185
            )
            dpg.add_input_int(
                label="Template Size",
                default_value=self.nlmeans_template_size,
                min_value=1,
                callback=self.update_params,
                tag=self.nlmeans_template_size_id,
                width=185
            )
            dpg.add_input_int(
                label="Search Size",
                default_value=self.nlmeans_search_size,
                min_value=1,
                callback=self.update_params,
                tag=self.nlmeans_search_size_id,
                width=185
            )

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask
        result = None
        
        if image is None:
            return [NodePackage()]

        if self.denoise_type == "Gaussian Blur":
            blur_amount = self.blur_amount if self.blur_amount % 2 == 1 else self.blur_amount + 1
            result = cv2.GaussianBlur(image, (blur_amount, blur_amount), 0)
        elif self.denoise_type == "Median Blur":
            blur_amount = self.blur_amount if self.blur_amount % 2 == 1 else self.blur_amount + 1
            result = cv2.medianBlur(image, blur_amount)
        elif self.denoise_type == "Bilateral Filter":
            result = cv2.bilateralFilter(
                image,
                self.bilateral_diameter,
                self.bilateral_sigma_color,
                self.bilateral_sigma_space
            )
        elif self.denoise_type == "Non-local Means":
            # Ensure template and search window sizes are odd
            template_size = (self.nlmeans_template_size 
                           if self.nlmeans_template_size % 2 == 1 
                           else self.nlmeans_template_size + 1)
            search_size = (self.nlmeans_search_size 
                         if self.nlmeans_search_size % 2 == 1 
                         else self.nlmeans_search_size + 1)
            
            result = cv2.fastNlMeansDenoisingColored(
                image,
                None,
                self.nlmeans_h,
                self.nlmeans_h,
                template_size,
                search_size
            ) if len(image.shape) > 2 else cv2.fastNlMeansDenoising(
                image,
                None,
                self.nlmeans_h,
                template_size,
                search_size
            )
            
        if result is None:
            self.on_error("No image data")
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
