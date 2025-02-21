import cv2
from NodeEditor import Node, NodePackage, dpg

class Threshold(Node):
    def __init__(self):
        super().__init__("Threshold", "Operations", 200)
        self.add_input("image", "Image")
        self.add_output("image", "Mask")
        self.threshold_value = 128
        self.max_value = 255
        self.threshold_type = cv2.THRESH_BINARY
        self.threshold_value_input = dpg.generate_uuid()
        self.img_tag = dpg.generate_uuid()
        
    def viewer(self, outputs: list[NodePackage]):
        data = outputs[0]
        
        if not dpg.does_item_exist(self.img_tag):
            with dpg.texture_registry():
                dpg.add_dynamic_texture(400, 400, [0.0, 0.0, 0.0, 0.0]*400*400, tag=self.img_tag)
            
        dpg.add_image(self.img_tag)
        
        image_rgba = data.copy_resize((400, 400), keep_alpha=True)
        
        image_rgba = image_rgba.astype(float)
        image_rgba /= 255

        dpg.set_value(self.img_tag, image_rgba.flatten())
        
    def compose(self):
        dpg.add_text("Threshold Value:")
        dpg.add_slider_int(min_value=0, max_value=255, default_value=self.threshold_value, callback=self.update_threshold, tag=self.threshold_value_input, width=185)

    def update_threshold(self):
        self.threshold_value = dpg.get_value(self.threshold_value_input)
        self.update()

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask

        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresholded_image = cv2.threshold(gray_image, self.threshold_value, self.max_value, self.threshold_type)

        return [NodePackage(image_or_mask=thresholded_image)]
