import cv2
import numpy as np
from NodeEditor import Node, NodePackage, dpg

class ImageInfo(Node):
    def __init__(self):
        super().__init__("Image Info", "Analysis", 200)
        self.add_input("image")
        
        # UI Controls for displaying image information
        self.dimensions_id = dpg.generate_uuid()
        self.channels_id = dpg.generate_uuid()
        self.dtype_id = dpg.generate_uuid()
        self.min_val_id = dpg.generate_uuid()
        self.max_val_id = dpg.generate_uuid()
        self.mean_val_id = dpg.generate_uuid()
        self.std_val_id = dpg.generate_uuid()
        
    def compose(self):
        dpg.add_text("Dimensions:", tag=self.dimensions_id)
        dpg.add_text("Channels:", tag=self.channels_id)
        dpg.add_text("Data Type:", tag=self.dtype_id)
        dpg.add_text("Min Value:", tag=self.min_val_id)
        dpg.add_text("Max Value:", tag=self.max_val_id)
        dpg.add_text("Mean Value:", tag=self.mean_val_id)
        dpg.add_text("Std Dev:", tag=self.std_val_id)

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        if not inputs or inputs[0].image_or_mask is None:
            # Reset all text if no input
            dpg.set_value(self.dimensions_id, "Dimensions: N/A")
            dpg.set_value(self.channels_id, "Channels: N/A")
            dpg.set_value(self.dtype_id, "Data Type: N/A")
            dpg.set_value(self.min_val_id, "Min Value: N/A")
            dpg.set_value(self.max_val_id, "Max Value: N/A")
            dpg.set_value(self.mean_val_id, "Mean Value: N/A")
            dpg.set_value(self.std_val_id, "Std Dev: N/A")
            return []

        image = inputs[0].image_or_mask
        
        # Get image properties
        if len(image.shape) == 2:
            height, width = image.shape
            channels = 1
        else:
            height, width, channels = image.shape
            
        # Calculate statistics
        if channels == 1:
            min_val = float(np.min(image))
            max_val = float(np.max(image))
            mean_val = float(np.mean(image))
            std_val = float(np.std(image))
            
            # Update UI with single channel information
            dpg.set_value(self.min_val_id, f"Min Value: {min_val:.2f}")
            dpg.set_value(self.max_val_id, f"Max Value: {max_val:.2f}")
            dpg.set_value(self.mean_val_id, f"Mean Value: {mean_val:.2f}")
            dpg.set_value(self.std_val_id, f"Std Dev: {std_val:.2f}")
        else:
            # Calculate per-channel statistics
            min_vals = [float(np.min(image[:,:,c])) for c in range(channels)]
            max_vals = [float(np.max(image[:,:,c])) for c in range(channels)]
            mean_vals = [float(np.mean(image[:,:,c])) for c in range(channels)]
            std_vals = [float(np.std(image[:,:,c])) for c in range(channels)]
            
            # Format channel values with proper labels (B,G,R,A)
            channel_labels = ['B', 'G', 'R', 'A'][:channels]
            min_str = ', '.join(f'{label}:{val:.2f}' for label, val in zip(channel_labels, min_vals))
            max_str = ', '.join(f'{label}:{val:.2f}' for label, val in zip(channel_labels, max_vals))
            mean_str = ', '.join(f'{label}:{val:.2f}' for label, val in zip(channel_labels, mean_vals))
            std_str = ', '.join(f'{label}:{val:.2f}' for label, val in zip(channel_labels, std_vals))
            
            # Update UI with multi-channel information
            dpg.set_value(self.min_val_id, f"Min Value: {min_str}")
            dpg.set_value(self.max_val_id, f"Max Value: {max_str}")
            dpg.set_value(self.mean_val_id, f"Mean Value: {mean_str}")
            dpg.set_value(self.std_val_id, f"Std Dev: {std_str}")

        # Update basic image information
        dpg.set_value(self.dimensions_id, f"Dimensions: {width}x{height}")
        dpg.set_value(self.channels_id, f"Channels: {channels}")
        dpg.set_value(self.dtype_id, f"Data Type: {image.dtype}")
            
        return inputs  # Pass through the input image