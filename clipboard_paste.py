"""
@author: AlexL
@title: ComfyUI-Hangover-Clipboard_Paste
@nickname: Clipboard_Paste
@description: Automatic paste the image from the clipboard
"""

# from nodes import MAX_RESOLUTION
# import comfy.utils
# import torch.nn.functional as F
import torch
import numpy as np
from PIL import ImageGrab
from PIL import Image
from PIL.PngImagePlugin import PngImageFile
from PIL import UnidentifiedImageError
import hashlib
import json

def GetPILImageFromClipboard():
    clip: PngImageFile = ImageGrab.grabclipboard()
    if isinstance(clip, list):
        result = Image.open(clip[-1]).convert("RGB")
    else:
        try:
            result = Image.frombytes(clip.mode, clip.size, clip.tobytes()).convert("RGB")
        except (AttributeError, UnidentifiedImageError):
            result = None

    return result


class PasteImage():
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "paste"
    CATEGORY = "Hangover"

    @classmethod
    def INPUT_TYPES(s):
        return {"optional": {
                   "alt_image": ("IMAGE",),
                   },
                }


    @classmethod
    def IS_CHANGED(s, alt_image=None):
        sha = hashlib.sha256()
        img = GetPILImageFromClipboard()
        if img is None:
            if alt_image is not None:
                sha.update(alt_image.numpy().tobytes())
        else:
            sha.update(img.tobytes())
        
        return sha.digest().hex()

    def paste(self, alt_image=None) -> tuple[torch.tensor]:
        result: torch.tensor = None
        image = GetPILImageFromClipboard()
        if image is not None:
            result = np.array(image).astype(np.float32) / 255.0
            result = torch.from_numpy(result).unsqueeze(0)
            print(f"Clipboard has an image with {result.shape=}")
        else:
            result = alt_image

        return result,


def run_test():
    print(f"{PasteImage.IS_CHANGED()=}")
    clp: PasteImage = PasteImage()
    print(f"{clp.INPUT_TYPES()=}")
    tensor = clp.paste()
    pil = GetPILImageFromClipboard()
    if pil:
        pil.show()
    else:
        print("Clipboard does not contain an image")



if __name__ == "__main__":
    run_test()