import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class KMeanClustering(Node):
    def __init__(self):
        super().__init__("K-Means Clustering", "Operations", 200)
        self.add_input("image")
        self.add_output("image")
        
        # UI Controls
        self.clusters_id = dpg.generate_uuid()
        self.iterations_id = dpg.generate_uuid()
        self.epsilon_id = dpg.generate_uuid()
        self.attempts_id = dpg.generate_uuid()
        
        # Default values
        self.clusters = 5
        self.iterations = 10
        self.epsilon = 1.0
        self.attempts = 3

    def on_save(self) -> dict:
        return {
            "clusters": self.clusters,
            "iterations": self.iterations,
            "epsilon": self.epsilon,
            "attempts": self.attempts
        }
    
    def on_load(self, data: dict):
        self.clusters = data["clusters"]
        self.iterations = data["iterations"]
        self.epsilon = data["epsilon"]
        self.attempts = data["attempts"]
        self.update()

    def update_params(self):
        self.clusters = dpg.get_value(self.clusters_id)
        self.iterations = dpg.get_value(self.iterations_id)
        self.epsilon = dpg.get_value(self.epsilon_id)
        self.attempts = dpg.get_value(self.attempts_id)
        self.update()

    def compose(self):
        dpg.add_text("K-Means Parameters:")
        dpg.add_input_int(label="Clusters (K)", default_value=self.clusters,
                         min_value=2, callback=self.update_params, 
                         tag=self.clusters_id, width=185)
        dpg.add_input_int(label="Max Iterations", default_value=self.iterations,
                         min_value=1, callback=self.update_params, 
                         tag=self.iterations_id, width=185)
        dpg.add_input_float(label="Epsilon", default_value=self.epsilon,
                          min_value=0.1, callback=self.update_params,
                          tag=self.epsilon_id, width=185)
        dpg.add_input_int(label="Attempts", default_value=self.attempts,
                         min_value=1, callback=self.update_params,
                         tag=self.attempts_id, width=185)

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        image = data.image_or_mask
        
        if image is None:
            return [NodePackage()]
        
        # Reshape the image for k-means
        Z = image.reshape((-1, 3))
        Z = np.float32(Z)
        
        # Define criteria and apply kmeans
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 
                   self.iterations, self.epsilon)
        
        _, labels, centers = cv2.kmeans(Z, self.clusters, None, criteria,  # type: ignore
                                      self.attempts, cv2.KMEANS_RANDOM_CENTERS) # type: ignore
        
        # Convert back to uint8 and reshape
        centers = np.uint8(centers)
        segmented = centers[labels.flatten()] # type: ignore
        result = segmented.reshape(image.shape)
        
        return [NodePackage(image_or_mask=result)]

    def viewer(self, outputs: list[NodePackage]):
        print("KMeans Clustering Viewer")
        data = outputs[0]
        img_tag = dpg.generate_uuid()
        with dpg.texture_registry():
            dpg.add_dynamic_texture(400, 400, [0.0, 0.0, 0.0, 0.0]*400*400, tag=img_tag)
        
        dpg.add_image(img_tag)
        
        image_rgba = data.copy_resize((400, 400), keep_alpha=True)
        image_rgba = image_rgba.astype(float)
        image_rgba /= 255

        dpg.set_value(img_tag, image_rgba.flatten())