"""
@author: AlexL
@title: ComfyUI-Hangover-Clipboard_Paste
@nickname: Clipboard_Paste
@description: Automatic paste the image from the clipboard
"""
from typing import Generator
import torch
import numpy as np
from PIL import ImageGrab, Image, UnidentifiedImageError
from PIL.PngImagePlugin import PngImageFile
from hashlib import sha256
import pillow_avif # this adds avif support to PIL
from comfy.comfy_types import IO


def GetPILImageFromClipboard() -> Generator[Image.Image, None, None]:
    """Get the image(s) from clipboard, convert and yield the image."""

    clip: Image.Image | list[str] | None = ImageGrab.grabclipboard()
    if clip is None:
        return
    elif isinstance(clip, list):
        for img in clip:
            yield Image.open(fp=img)
    elif isinstance(clip, Image.Image):
        yield Image.frombytes(mode=clip.mode, size=clip.size, data=clip.tobytes())
    else:
        return


class PasteImage():
    RETURN_TYPES = IO.IMAGE, IO.MASK,
    FUNCTION = "paste"
    CATEGORY = "Hangover"


    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, tuple[IO]]]:
        return {"optional": {
                   "alt_image": (IO.IMAGE,),
                   },
                }


    @classmethod
    def IS_CHANGED(cls, alt_image: torch.Tensor | None = None) -> str:
        """nessesary for the change in the clipboard to be recognized by ConfyUI"""
        sha = sha256()
        for img in GetPILImageFromClipboard():
            sha.update(img.tobytes())
        if alt_image is not None:
            sha.update(alt_image.numpy().tobytes())
        return sha.digest().hex()


    def paste(self, alt_image: torch.Tensor | None = None) -> tuple[torch.Tensor | None, torch.Tensor | None]:
        samples: torch.Tensor | None = None
        mask: torch.Tensor | None = None

        for image in GetPILImageFromClipboard():
            if image.mode == 'I':
                image = image.point(lambda i: i/255)

            """
            convert the image to a tensor and add a batch dimension.
            since image.convert() throws an anoing warning to console if a palette image with transparency
            is converted with "RGB", so we alway convert to RGBA and trow away the extra channel in the tensor.
            """
            s = torch.from_numpy(
                        np.array(object=image.convert(mode="RGBA", )
                        ).astype(dtype=np.float32)/255.
                        )[None,:,:,:3]

            # extract the alpha channel if it exists and convert it to a mask tensor with an extra batch dimension:
            if 'A' in image.getbands():
                m = 1.0 - torch.from_numpy(
                    np.array(object=image.getchannel(channel='A')
                    ).astype(dtype=np.float32) / 255.0)[None,]
            elif 'P' in image.mode and 'transparency' in image.info:
                m = 1.0 - torch.from_numpy(
                    np.array(object=image.convert(mode='RGBA').getchannel(channel='A')
                    ).astype(dtype=np.float32) / 255.0)[None,]
            else:
                m = torch.zeros(size=(1, 64, 64))

            if samples is None:
                samples = s
            else:
                samples = torch.cat(tensors=(samples, s), dim=0)

            if mask is None:
                mask = m
            else:
                mask = torch.cat(tensors=(mask, m), dim=0)

        if samples is None:
            samples = alt_image
            if alt_image is not None and alt_image.shape[3] == 4:
                # extract the mask from the alternative input image
                mask = 1. - alt_image[:, :, :, 3]

        return samples, mask,


def run_test():
    clp_paste = PasteImage()
    print(f"{clp_paste.INPUT_TYPES()=}")
    try:
        for img in GetPILImageFromClipboard():
            img.show()

        tensor, mask = clp_paste.paste()
        if tensor is None:
            print("No image")
        else:
            print(f"{tensor.shape=}")

        if mask is None:
            print("No mask")
        else:
            print(f"{mask.shape=}")

    except UnidentifiedImageError:
        print("Clipboard does not contain image(s)")
    except:
        raise


if __name__ == "__main__":
    run_test()
