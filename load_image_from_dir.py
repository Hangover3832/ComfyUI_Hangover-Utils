"""
@author: AlexL
@title: ComfyUI-Hangover-Load_Image_From_Dir
@nickname: Hangover-Load_Image_From_Dir
@description: Loads an image[index] from a directory, returns (IMAGE, MASK).
V3 node.
"""

from typing import Any, Callable
from nodes import MAX_RESOLUTION
import torch
import numpy as np
from pathlib import Path
from PIL import Image, ImageSequence, ImageOps
import pillow_avif # this adds avif support to Pillow
from comfy_api.latest import io
import node_helpers
from hashlib import md5
from _hashlib import HASH
from comfy.model_management import processing_interrupted
from comfy_api_nodes.util.common_exceptions import ProcessingInterrupted


def load_image_with_mask(image_path: Path) -> tuple[torch.Tensor, torch.Tensor]:
    """Load a PNG/image from an arbitrary path, return (image_tensor, mask_tensor).

    Extracts the alpha channel as a mask (inverted: transparent areas → 1).
    Handles multi-frame images (animated WebP/GIF/APNG) by returning all frames batched and avif.

    Returns:
        image_tensor: [B, H, W, C] float32 in [0, 1]
        mask_tensor:  [B, H, W]   float32 in [0, 1], transparent=1
    """
    img = node_helpers.pillow(Image.open, image_path)

    output_images: list[torch.Tensor] = []
    output_masks: list[torch.Tensor] = []

    for frame in ImageSequence.Iterator(img):
        frame = node_helpers.pillow(ImageOps.exif_transpose, frame)
        rgb = frame.convert("RGB")

        if 'A' in frame.getbands():
            # Alpha channel
            mask = np.array(frame.getchannel('A')).astype(np.float32) / 255.0

        elif 'P' in frame.mode and "transparency" in frame.info:
            # Palette with transparency
            mask = np.array(frame.convert(mode="RGBA").getchannel(channel='A')
                ).astype(dtype=np.float32) / 255.0

        else:
            w, h = frame.size
            mask = np.ones((h,w), dtype=np.float32)

        mask = 1.0 - torch.from_numpy(mask)

        image_np = np.array(rgb).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(image_np)[None,]  # [1, H, W, C]

        output_images.append(image_tensor)
        output_masks.append(mask.unsqueeze(0))  # [1, H, W]

    return (
        torch.cat(output_images, dim=0),   # [B, H, W, C]
        torch.cat(output_masks, dim=0),    # [B, H, W]
    )


class LoadImageIndexFromDir(io.ComfyNode):

    valid_extensions = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif"}

    @classmethod
    def _list_images(cls, path:Path, recursive:bool) -> tuple[list[Path], str]:
        """Returns a list of image files under *path* and the md5 hash."""

        results: list[Path] = []
        hash:HASH = md5()

        if path.is_file() and path.suffix.lower() in cls.valid_extensions:
            results = [path]
            hash.update(str(path).encode('utf8'))

        elif path.is_dir():
            glob:Callable = path.rglob if recursive else path.glob

            for p in glob("*"):
                if processing_interrupted():
                    raise ProcessingInterrupted

                if  p.is_file and p.suffix.lower() in cls.valid_extensions:
                    results.append(p)
                    hash.update(str(p).encode('utf8'))

        return results, hash.hexdigest()


    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="hangover_load_image_index_from_dir",
            display_name="Load Image Index From Dir",
            category="Hangover",
            description="Loads an image[index] from a directory",
            search_aliases=["image", "index", "load", "dir"],
            inputs=[
                io.String.Input("dir"),
                io.Int.Input("image_index", default=0, control_after_generate=io.ControlAfterGenerate.fixed),
                io.Boolean.Input("recursive", tooltip="Recursive directory search"),
            ],
            outputs=[
                io.Image.Output(display_name="image"),
                io.Mask.Output(display_name="mask"),
                io.Int.Output(display_name="index"),
                io.String.Output(display_name="image_file")
            ],
        )


    @classmethod
    def execute(cls, *, dir: str, image_index: int, recursive:bool, **kwargs) -> io.NodeOutput:
        dir_path = Path(dir)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory does not exists: {dir}")

        image_list:list[Path] = cls._list_images(dir_path, recursive)[0]
        try:
            file = image_list[image_index]
            img_tensor, mask_tensor = load_image_with_mask(file)
        except IndexError as e:
            raise ValueError("No more images!")

        return io.NodeOutput(img_tensor, mask_tensor, image_index, str(file),)
