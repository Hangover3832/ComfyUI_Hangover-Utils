"""
@author: AlexL
@title: ComfyUI-Hangover-Clipboard_Paste
@nickname: Clipboard_Paste
@description: Automatic paste the image from the clipboard
"""

from torch import Tensor, from_numpy
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
        return [Image.open(fp=clip[i]) for i in range(len(clip))]
    elif isinstance(clip, Image.Image):
        return [Image.frombytes(mode=clip.mode, size=clip.size, data=clip.tobytes()).convert(mode="RGB")]
    else:
        return None


class PasteImage():
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "paste"
    CATEGORY = "Hangover"


    @classmethod
    def INPUT_TYPES(cls):
        return {"optional": {
                   "alt_image": ("IMAGE",),
                   },
                }

    @classmethod
    def IS_CHANGED(cls, alt_image: Tensor | None = None) -> str:
        sha = sha256()
        img = GetPILImageFromClipboard()
        if img is None:
            if alt_image is not None:
                sha.update(alt_image.numpy().tobytes())
        else:
            for i in img:
                sha.update(i.tobytes())

        return sha.digest().hex()


    def paste(self, alt_image: Tensor | None = None) -> tuple[Tensor | None]:
        image = GetPILImageFromClipboard()
        if image is not None:
            result = np.array(object=image).astype(dtype=np.float32) / 255.0
            result = from_numpy(result)
            print(f"Clipboard contains {result.shape[0]} image{'s' if result.shape[0]>1 else ''}: {result.shape=}")
        else:
            result = alt_image

        if result is None:
            raise UnidentifiedImageError("Error: No valid image found in the clipboard.")

        return result,


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

        tensor = clp_paste.paste()[0]
        if tensor is not None:
            print(f"{tensor.shape=}")


    except UnidentifiedImageError:
        print("Clipboard does not contain image(s)")
    except:
        raise


if __name__ == "__main__":
    run_test()
