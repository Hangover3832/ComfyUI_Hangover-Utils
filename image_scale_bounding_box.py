"""
@author: AlexL
@title: ComfyUI-Hangover-Image_Scale_Bouning_Box
@nickname: Hangover-Image_Scale_Bouning_Box
@description: Scales an input image into a given box size, whereby the aspect ratio keeps retained.
"""
from nodes import MAX_RESOLUTION
import comfy.utils
import torch.nn.functional as F
import torch
from comfy.comfy_types.node_typing import ComfyNodeABC, InputTypeDict, IO, StrEnum

class PAD(StrEnum): # Padding Type
    none = "none"; centered = "center"; top = "top"; left = "left"; right = "right"; bottom = "bottom"


class ImageScaleBoundingBox(ComfyNodeABC):
    UPSCALE_METHOD: list[str] = ["lanczos", "nearest-exact", "bilinear", "area", "bicubic"]
    PADDING: list[PAD] = [PAD.none, PAD.centered, PAD.top, PAD.left, PAD.right, PAD.bottom]
    RETURN_TYPES: tuple[IO] = IO.IMAGE,
    FUNCTION = "upscale"
    CATEGORY = "Hangover"


    @classmethod
    def INPUT_TYPES(cls) -> InputTypeDict:
        return {"required": {
                    "image": (IO.IMAGE, {}),
                    "upscale_method": (IO.COMBO, {"options": list(cls.UPSCALE_METHOD), "default": cls.UPSCALE_METHOD[0], "placeholder": "select upscale method.."}), 
                    "box_width": (IO.INT, {"default": 512, "min": 1, "max": MAX_RESOLUTION, "step": 1}),
                    "box_height": (IO.INT, {"default": 512, "min": 1, "max": MAX_RESOLUTION, "step": 1}),
                    "padding": (IO.COMBO, {"options": list(cls.PADDING), "default": PAD.none, "placeholder": "select padding..."}),
                    "pad_color": (IO.INT, {"default": 0, "min": 0, "max": 0xFFFFFF, "step": 1}),
                    }
                }


    def upscale(self, image: torch.Tensor, upscale_method: str, box_width: int, box_height: int, padding: PAD, pad_color: int) -> tuple[torch.Tensor]:
        w = image.shape[2]
        h = image.shape[1]
        scale_by = min(box_width/w, box_height/h)
        new_width = round(number=w * scale_by)
        new_height = round(number=h * scale_by)
        samples = comfy.utils.common_upscale(
            samples=image.movedim(source=-1, destination=1), # prepare the shape for common_upscale()
            width=new_width, height=new_height, 
            upscale_method=upscale_method, crop="disabled"
            ).movedim(source=1, destination=0) # make RGB channels to be dimension 0 makes padding easier later on

        if padding != PAD.none:
            # padding for the case 'center':
            pad_left = (box_width - new_width) // 2
            pad_right = box_width - new_width - pad_left
            pad_top = (box_height - new_height) // 2
            pad_bottom = box_height - new_height - pad_top # ensure that we do not get any rounding error in the output image size
 
            # override padding for the cases 'top', 'left', 'right', and 'bottom':
            match padding:
                case PAD.top:
                    pad_bottom = 0
                    pad_top = box_height - new_height
                case PAD.left:
                    pad_right = 0
                    pad_left = box_width - new_width
                case PAD.right:
                    pad_left = 0
                    pad_right = box_width - new_width
                case PAD.bottom:
                    pad_top = 0
                    pad_bottom = box_height - new_height

            pad = (pad_left, pad_right, pad_top, pad_bottom)
            b, g, r = [((pad_color >> (i * 8)) & 0xFF) / 255. for i in range(3)] # extract rgb values from pad_color

            # apply padding on each color channel and restack the tensor:
            samples = torch.stack(
                        tensors=[F.pad(input=samples[i], 
                        pad=pad, mode='constant', value=value
                        ) for i, value in enumerate(iterable=(r, g, b))])

        samples = samples.movedim(source=0, destination=-1) # restore the original shape of the image tensor
        return samples,
