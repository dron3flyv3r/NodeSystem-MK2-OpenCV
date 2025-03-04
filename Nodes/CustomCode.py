import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg
import ast
import textwrap

class CustomCode(Node):
    def __init__(self):
        super().__init__("Custom Code", "Operations", 200)
        self.add_input("image")
        self.add_output("image")
        
        # UI Controls
        self.code_id = dpg.generate_uuid()
        
        # Default values
        self.code = textwrap.dedent("""
        # Available variables:
        # image: input image (numpy array)
        # cv2: OpenCV module
        # np: NumPy module
        
        # Example: Gaussian blur
        result = cv2.GaussianBlur(image, (5, 5), 0)
        """).strip()
        
        self.locals = {}
        self.error_message = ""

    def on_save(self) -> dict:
        return {
            "code": self.code
        }
    
    def on_load(self, data: dict):
        self.code = data["code"]
        self.update()

    def update_params(self):
        self.code = dpg.get_value(self.code_id)
        self.error_message = ""
        try:
            # Check if code is valid Python
            ast.parse(self.code)
        except SyntaxError as e:
            self.error_message = f"Syntax Error: {str(e)}"
        self.update()

    def compose(self):
        dpg.add_text("Custom Python Code:")
        dpg.add_input_text(
            default_value=self.code,
            callback=self.update_params,
            tag=self.code_id,
            width=185,
            height=200,
            multiline=True
        )
        
        if self.error_message:
            dpg.add_text(self.error_message, color=(255, 0, 0))

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask
        
        if image is None or self.error_message:
            return [NodePackage()]

        try:
            # Set up environment for code execution
            self.locals = {
                'image': image.copy(),
                'cv2': cv2,
                'np': np,
                'result': None
            }
            
            # Execute the code
            exec(self.code, {}, self.locals)
            
            # Get the result
            result = self.locals.get('result')
            
            if result is None:
                self.error_message = "Error: Code must assign a value to 'result'"
                return [NodePackage()]
            
            if not isinstance(result, np.ndarray):
                self.error_message = "Error: 'result' must be a numpy array"
                return [NodePackage()]
            
            return [NodePackage(image_or_mask=result)]
            
        except Exception as e:
            self.error_message = f"Runtime Error: {str(e)}"
            return [NodePackage()]

    def viewer(self, outputs: list[NodePackage]):
        data = outputs[0]
        img_tag = dpg.generate_uuid()
        with dpg.texture_registry():
            dpg.add_dynamic_texture(400, 400, [0.0, 0.0, 0.0, 0.0]*400*400, tag=img_tag)
        
        if self.error_message:
            dpg.add_text(self.error_message, color=(255, 0, 0))
        
        dpg.add_image(img_tag)
        
        image_rgba = data.copy_resize((400, 400), keep_alpha=True)
        image_rgba = image_rgba.astype(float)
        image_rgba /= 255

        dpg.set_value(img_tag, image_rgba.flatten())