import copy
from cv2.typing import MatLike
from cv2 import Mat
import cv2
import numpy as np

from dataclasses import dataclass, field

@dataclass
class NodePackage:
    image_or_mask: MatLike = field(default_factory=lambda: Mat(np.zeros((1, 1, 3), dtype=np.uint8)))
    
    def copy(self) -> 'NodePackage':
        new_package = NodePackage()
        for key, value in self.__dict__.items():
            setattr(new_package, key, copy.deepcopy(value))
        return new_package
    
    def copy_resize(self, new_shape: tuple[int, int], pad_color: tuple[int, int, int, int] = (0, 0, 0, 0), keep_alpha: bool = False) -> MatLike:
        img = copy.deepcopy(self.image_or_mask)
        old_shape = img.shape
        # Convert to 4 channels if needed
        if len(old_shape) == 3 and old_shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        elif len(old_shape) == 2:
            if len(old_shape) == 2 or (len(old_shape) == 3 and old_shape[2] != 4):
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGBA)
        
        # Calculate the new size while preserving the aspect ratio
        old_height, old_width = old_shape[:2]
        new_height, new_width = new_shape
        aspect_ratio = old_width / old_height

        if new_width / new_height > aspect_ratio:
            new_width = int(new_height * aspect_ratio)
        else:
            new_height = int(new_width / aspect_ratio)

        resized_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)

        # Create a new image with the desired shape and pad color
        new_img = np.full((new_shape[1], new_shape[0], 4), pad_color, dtype=np.uint8)

        # Calculate padding
        pad_top = (new_shape[1] - new_height) // 2
        pad_left = (new_shape[0] - new_width) // 2

        # Place the resized image in the center
        new_img[pad_top:pad_top + new_height, pad_left:pad_left + new_width] = resized_img

        if keep_alpha:
            return new_img

        # Convert the new_img back to the original number of channels
        if len(old_shape) == 3 and old_shape[2] == 3:
            new_img = cv2.cvtColor(new_img, cv2.COLOR_RGBA2BGR)
        elif len(old_shape) == 2:
            new_img = cv2.cvtColor(new_img, cv2.COLOR_RGBA2GRAY)
        
        return new_img


