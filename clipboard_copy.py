"""
@author: AlexL
@title: ComfyUI-Hangover-Clipboard_copy
@nickname: Clipboard_Copy
@description: Copy an image to the clipboard
"""

from torch import Tensor
from PIL import Image
import numpy as np
from pyperclipimg import copy

from comfy_api.latest import io


class CopyImage(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Image Clipboard Copy",  # keep the V1 class type so existing workflows still resolve
            display_name="Image Clipboard Copy",
            description="Copy an image to the clipboard",
            category="Hangover",
            search_aliases=["clipboard", "copy"],
            inputs=[
                io.Image.Input("image"),
            ],
            outputs=[
                io.Image.Output(display_name="image"),
            ],
        )

    @classmethod
    def execute(cls, *, image: Tensor, **kwargs) -> io.NodeOutput:
        if image.shape[0] > 1:
            print(f"Note: copy batched images to the clipboard is not supported, picking the first one")
        img = np.clip(image[0].cpu().numpy() * 255., 0, 255).astype(np.uint8)
        copy(image=Image.fromarray(obj=img))
        return io.NodeOutput(image)
