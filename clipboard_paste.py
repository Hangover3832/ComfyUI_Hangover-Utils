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
from hashlib import md5

import pillow_avif  # this adds avif support to Pillow

from comfy_api.latest import ComfyExtension, io


class PasteImage(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="HangoverUtils_ClipboardPaste",
            display_name="Clipboard Paste",
            category="Hangover",
            description="Paste images from the clipboard. Multiple images of the same size are batched.",
            search_aliases=["paste clipboard", "paste image"],
            inputs=[
                io.Image.Input("alt_image", optional=True),
                io.Mask.Input("alt_mask", optional=True),
            ],
            outputs=[
                io.Image.Output(display_name="image"),
                io.Mask.Output(display_name="mask"),
            ],
        )

    hash: md5 = md5()

    @classmethod
    def _get_pil_images(cls) -> Generator[Image.Image, None, None]:
        """Get the image(s) from clipboard, convert and yield the image."""
        try:
            clip = ImageGrab.grabclipboard()
            if clip is None:
                return

            if isinstance(clip, list):
                for img_path in clip:
                    try:
                        yield Image.open(fp=img_path)
                    except FileNotFoundError:
                        pass
                return

            if isinstance(clip, Image.Image):
                yield clip.copy()
                return

        except Exception:
            pass

    @classmethod
    def fingerprint_inputs(
        cls, *, alt_image: torch.Tensor | None = None, alt_mask: torch.Tensor | None = None, **kwargs
    ) -> str:
        changed = False
        for img in cls._get_pil_images():
            if not changed:
                cls.hash = md5()
            cls.hash.update(img.tobytes())
            changed = True
        return cls.hash.digest().hex()

    @classmethod
    def execute(
        cls,
        *,
        alt_image: torch.Tensor | None = None,
        alt_mask: torch.Tensor | None = None,
        **kwargs
    ) -> io.NodeOutput:
        samples: torch.Tensor | None = None
        mask: torch.Tensor | None = None

        for image in cls._get_pil_images():

            if image.mode == 'I':
                image = image.point(lambda i: i / 255.)

            s = torch.from_numpy(
                np.array(image.convert("RGBA")).astype(np.float32) / 255.0
            )[None, :, :, :3]

            if 'A' in image.getbands():
                m = 1.0 - torch.from_numpy(
                    np.array(image.getchannel("A")).astype(np.float32) / 255.0
                )[None, :]
            elif 'P' in image.mode and 'transparency' in image.info:
                m = 1.0 - torch.from_numpy(
                    np.array(image.convert("RGBA").getchannel("A")).astype(np.float32) / 255.0
                )[None, :]
            else:
                m = torch.zeros((1, 64, 64))

            if samples is None:
                samples = s
            else:
                samples = torch.cat((samples, s), dim=0)

            if mask is None:
                mask = m
            else:
                mask = torch.cat((mask, m), dim=0)

        if samples is None or mask is None:
            raise UnidentifiedImageError("Clipboard does not contain valid image(s)!")

        return io.NodeOutput((samples, mask))


# --- Legacy V1 shim kept so old loader paths don't break ---
INPUT_TYPES = lambda: {"optional": {"alt_image": ("IMAGE", {}), "alt_mask": ("MASK", {})}}
RETURN_TYPES = ("IMAGE", "MASK")
FUNCTION = "execute"
CATEGORY = "Hangover"


def run_test() -> None:
    from time import sleep

    clp_paste = PasteImage()
    old_sha = ""

    while True:
        print("Listen for change...")
        while (new_sha := clp_paste.fingerprint_inputs()) == old_sha:
            print(new_sha, end='\r', flush=True)
            sleep(0.1)

        print(f"\n{new_sha}")
        old_sha = clp_paste.fingerprint_inputs()

        try:
            for img in clp_paste._get_pil_images():
                print(img)

            tensor, mask = clp_paste.execute()
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
        except Exception:
            raise

        sleep(0.1)


if __name__ == "__main__":
    run_test()
