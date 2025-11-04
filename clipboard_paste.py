"""
@author: AlexL
@title: ComfyUI-Hangover-Clipboard_Paste
@nickname: Clipboard_Paste
@description: Automatic paste the image from the clipboard
"""

# from torch import Tensor, from_numpy
import torch
import numpy as np
from PIL import ImageGrab, Image, UnidentifiedImageError
from PIL.PngImagePlugin import PngImageFile
from hashlib import sha256
import pillow_avif
from comfy.comfy_types import IO


def GetPILImageFromClipboard() -> list[Image.Image] | None:
    """Get the image from clipboard and convert it to PIL Image."""
    clip: Image.Image | list[str] | None = ImageGrab.grabclipboard() # ImageGrab.grabclipboard()
    if clip is None:
        return None
    
    elif isinstance(clip, list):
        # r, g, b, a = img.split()
        result = []
        for i in clip:
            img = Image.open(i)
            img = img.convert(mode="RGBA" if len(img.split()) == 4 else "RGB")
            result.append(img)
        return result
    
    elif isinstance(clip, Image.Image):
        print(f"{clip.mode=}")
        im = Image.frombytes(mode=clip.mode, size=clip.size, data=clip.tobytes())
        return [im.convert(mode="RGBA")]
    
    else:
        return None


class PasteImage():
    RETURN_TYPES = IO.IMAGE, IO.MASK,
    FUNCTION = "paste"
    CATEGORY = "Hangover"


    @classmethod
    def INPUT_TYPES(cls):
        return {"optional": {
                   "alt_image": ("IMAGE",),
                   },
                }

    @classmethod
    def IS_CHANGED(cls, alt_image: torch.Tensor | None = None) -> str:
        """This is nessesary for the change in the clipboard to be recognized by ConfyUI"""
        sha = sha256()
        img = GetPILImageFromClipboard()
        if img is None:
            if alt_image is not None:
                sha.update(alt_image.numpy().tobytes())
        else:
            for i in img:
                sha.update(i.tobytes())

        return sha.digest().hex()


    def paste(self, alt_image: torch.Tensor | None = None) -> tuple[torch.Tensor | None, torch.Tensor | None]:
        images = GetPILImageFromClipboard()
        mask = None
        if images is not None:
            result: torch.Tensor | None = torch.from_numpy((np.array(images, dtype=np.float32) / 255.))
            print(f"Clipboard contains {result.shape[0]} image{'s' if result.shape[0]>1 else ''}: {result.shape=}")
            if result.shape[3] == 4:
                # looks like we have an alpha channel
                mask = 1. - result[:, :, :, 3]
                result = result[:, :, :, :3]
            else:
                mask = torch.zeros(size=(64,64), dtype=torch.float32, device="cpu").unsqueeze(dim=0)
        else:
            result = alt_image

        if result is None:
            raise UnidentifiedImageError("Error: No valid image found in the clipboard.")

        return result, mask,


def run_test():
    clp_paste = PasteImage()
    print(f"{clp_paste.INPUT_TYPES()=}")
    try:
        pil = GetPILImageFromClipboard()
        if pil is None:
            raise UnidentifiedImageError
        else:
            for p in pil:
                p.show()

        tensor, mask = clp_paste.paste()
        if tensor is None:
            print("No image")
        else:
            print(f"{tensor.shape=}")

        if mask is None:
            print("no mask")
        else:
            print(f"{mask.shape=}")

    except UnidentifiedImageError:
        print("Clipboard does not contain image(s)")
    except:
        raise


if __name__ == "__main__":
    run_test()
