"""
@author: AlexL
@title: ComfyUI-Hangover-Clipboard_Paste
@nickname: Clipboard_Paste
@description: Copy an image to the clipboard
"""

from torch import Tensor
from PIL import Image
import numpy as np
from comfy.comfy_types import IO
from pyperclipimg import copy

class CopyImage():
    RETURN_TYPES = IO.IMAGE,
    FUNCTION = "copy"
    CATEGORY = "Hangover"


    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
                   "image": (IO.IMAGE,),
                   },
                }


    def copy(self, image: Tensor) -> tuple[Tensor]:
        if image.shape[0] > 1:
            print(f"Note: copy batched images to the clipboard is not supported, picking the first one")
        img = np.clip(image[0].cpu().numpy() * 255., 0, 255).astype(np.uint8)
        copy(image=Image.fromarray(obj=img))
        return image, 
