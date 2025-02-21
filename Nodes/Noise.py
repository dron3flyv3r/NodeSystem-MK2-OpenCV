import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class Noise(Node):
    def __init__(self):
        super().__init__("Noise", "Operations", 200)
        self.add_input("image")
        self.add_output("image")

        self.noise_type_id = dpg.generate_uuid()
        self.noise_amount_input = dpg.generate_uuid()
        self.noise_density_input = dpg.generate_uuid()
        self.noise_stddev_input = dpg.generate_uuid()

        self.noise_type = "Gaussian"
        self.noise_amount = 50
        self.noise_density = 0.05
        self.noise_stddev = 25

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
        dpg.add_text("Noise Type:")
        dpg.add_combo(items=["Gaussian", "Salt & Pepper"], default_value=self.noise_type, 
                     callback=self.update_noise, tag=self.noise_type_id, width=185)

        # Add both sliders but control visibility based on noise type
        dpg.add_text("Noise StdDev:")
        dpg.add_slider_int(min_value=0, max_value=255, default_value=self.noise_stddev, 
                          callback=self.update_noise, tag=self.noise_stddev_input, 
                          width=185, show=self.noise_type=="Gaussian")
        
        dpg.add_text("Noise Density:")
        dpg.add_slider_float(min_value=0.0, max_value=1.0, default_value=self.noise_density, 
                           callback=self.update_noise, tag=self.noise_density_input, 
                           width=185, show=self.noise_type=="Salt & Pepper")

    def update_noise(self):
        self.noise_type = dpg.get_value(self.noise_type_id)
        
        # Update visibility of sliders based on noise type
        dpg.configure_item(self.noise_stddev_input, show=self.noise_type=="Gaussian")
        dpg.configure_item(self.noise_density_input, show=self.noise_type=="Salt & Pepper")
        
        # Always update both values
        self.noise_stddev = dpg.get_value(self.noise_stddev_input)
        self.noise_density = dpg.get_value(self.noise_density_input)
        
        self.update()

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask.copy()

        if self.noise_type == "Gaussian":
            mean = 0
            noise = np.random.normal(mean, max(1, self.noise_stddev), image.shape)
            noisy_image = image + noise
            noisy_image = np.clip(noisy_image, 0, 255).astype(np.uint8)
            
        elif self.noise_type == "Salt & Pepper":
            noisy_image = image.copy()
            # Ensure we have a valid density value
            density = float(self.noise_density) if self.noise_density is not None else 0.05
            
            # Salt noise (white pixels)
            salt_prob = density / 2
            salt_mask = np.random.random(image.shape[:2]) < salt_prob
            noisy_image[salt_mask] = 255
            
            # Pepper noise (black pixels)
            pepper_prob = density / 2
            pepper_mask = np.random.random(image.shape[:2]) < pepper_prob
            noisy_image[pepper_mask] = 0
            
        else:
            noisy_image = image

        return [NodePackage(image_or_mask=noisy_image)]
