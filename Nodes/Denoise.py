import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class Denoise(Node):
    def __init__(self):
        super().__init__("Denoise", "Operations", 200)
        self.add_input("image")
        self.add_output("image")

        self.denoise_type_id = dpg.generate_uuid()
        self.blur_amount_input = dpg.generate_uuid()
        self.bilateral_diameter_input = dpg.generate_uuid()
        self.bilateral_sigma_color_input = dpg.generate_uuid()
        self.bilateral_sigma_space_input = dpg.generate_uuid()
        self.nlmeans_h_input = dpg.generate_uuid()
        self.nlmeans_template_size_input = dpg.generate_uuid()
        self.nlmeans_search_size_input = dpg.generate_uuid()

        self.denoise_type = "Gaussian Blur"
        self.blur_amount = 3
        self.bilateral_diameter = 9
        self.bilateral_sigma_color = 75
        self.bilateral_sigma_space = 75
        self.nlmeans_h = 10
        self.nlmeans_template_size = 7
        self.nlmeans_search_size = 21

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

    def compose(self):
        dpg.add_text("Denoise Type:")
        dpg.add_combo(items=["Gaussian Blur", "Median Blur", "Bilateral Filter", "Non-local Means"], default_value=self.denoise_type, callback=self.update_denoise, tag=self.denoise_type_id, width=185)

        if self.denoise_type == "Gaussian Blur" or self.denoise_type == "Median Blur":
            dpg.add_text("Blur Amount:")
            dpg.add_slider_int(min_value=1, max_value=15, default_value=self.blur_amount, callback=self.update_denoise, tag=self.blur_amount_input, width=185)
        elif self.denoise_type == "Bilateral Filter":
            dpg.add_text("Diameter:")
            dpg.add_slider_int(min_value=1, max_value=15, default_value=self.bilateral_diameter, callback=self.update_denoise, tag=self.bilateral_diameter_input, width=185)
            dpg.add_text("Sigma Color:")
            dpg.add_slider_int(min_value=1, max_value=150, default_value=self.bilateral_sigma_color, callback=self.update_denoise, tag=self.bilateral_sigma_color_input, width=185)
            dpg.add_text("Sigma Space:")
            dpg.add_slider_int(min_value=1, max_value=150, default_value=self.bilateral_sigma_space, callback=self.update_denoise, tag=self.bilateral_sigma_space_input, width=185)
        elif self.denoise_type == "Non-local Means":
            dpg.add_text("h:")
            dpg.add_slider_int(min_value=1, max_value=50, default_value=self.nlmeans_h, callback=self.update_denoise, tag=self.nlmeans_h_input, width=185)
            dpg.add_text("Template Size:")
            dpg.add_slider_int(min_value=1, max_value=15, default_value=self.nlmeans_template_size, callback=self.update_denoise, tag=self.nlmeans_template_size_input, width=185)
            dpg.add_text("Search Size:")
            dpg.add_slider_int(min_value=1, max_value=50, default_value=self.nlmeans_search_size, callback=self.update_denoise, tag=self.nlmeans_search_size_input, width=185)

    def update_denoise(self):
        self.denoise_type = dpg.get_value(self.denoise_type_id)
        if self.denoise_type == "Gaussian Blur" or self.denoise_type == "Median Blur":
            self.blur_amount = dpg.get_value(self.blur_amount_input)
        elif self.denoise_type == "Bilateral Filter":
            self.bilateral_diameter = dpg.get_value(self.bilateral_diameter_input)
            self.bilateral_sigma_color = dpg.get_value(self.bilateral_sigma_color_input)
            self.bilateral_sigma_space = dpg.get_value(self.bilateral_sigma_space_input)
        elif self.denoise_type == "Non-local Means":
            self.nlmeans_h = dpg.get_value(self.nlmeans_h_input)
            self.nlmeans_template_size = dpg.get_value(self.nlmeans_template_size_input)
            self.nlmeans_search_size = dpg.get_value(self.nlmeans_search_size_input)
        self.update()

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask

        if self.denoise_type == "Gaussian Blur":
            blur_amount = self.blur_amount if self.blur_amount % 2 == 1 else self.blur_amount + 1
            denoised_image = cv2.GaussianBlur(image, (blur_amount, blur_amount), 0)
        elif self.denoise_type == "Median Blur":
            blur_amount = self.blur_amount if self.blur_amount % 2 == 1 else self.blur_amount + 1
            denoised_image = cv2.medianBlur(image, blur_amount)
        elif self.denoise_type == "Bilateral Filter":
            denoised_image = cv2.bilateralFilter(image, self.bilateral_diameter, self.bilateral_sigma_color, self.bilateral_sigma_space)
        elif self.denoise_type == "Non-local Means":
            denoised_image = cv2.fastNlMeansDenoisingColored(image, None, self.nlmeans_h, self.nlmeans_template_size, self.nlmeans_search_size)
        else:
            denoised_image = image

        return [NodePackage(image_or_mask=denoised_image)]
