"""
@author: AlexL
@title: ComfyUI-Hangover-Clipboard_Paste
@nickname: Clipboard_Paste
@description: Automatic paste the image from the clipboard

V3 node.
"""
from typing import Generator
import torch
import numpy as np
from PIL import ImageGrab, Image, UnidentifiedImageError
from hashlib import md5
import pillow_avif # this adds avif support to Pillow
from comfy_api.latest import io


class PasteImage(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Image Clipboard Paster",
            display_name="Image Clipboard Paster",
            category="Hangover",
            description="Pastes images from the clipboard. "
                        "The alt_image and alt_mask inputs are not processed by the node, "
                        "they just get passed through in case this node is bypassed. "
                        "Multiple images in the clipboard are batched if they have the same size and format.",
            search_aliases=["paste", "clipboard", "clipboard paster"],
            inputs=[
                io.Image.Input("alt_image", optional=True),
                io.Mask.Input("alt_mask", optional=True),
            ],
            outputs=[
                io.Image.Output(),
                io.Mask.Output(),
            ],
        )

    @classmethod
    def GetPILImageFromClipboard(cls) -> Generator[Image.Image, None, None]:
        """Get the image(s) from clipboard, convert and yield the image."""

        try:
            clip: Image.Image | list[str] | None = ImageGrab.grabclipboard()
            if clip is None:
                return

            if isinstance(clip, list):
                for img in clip:
                    try:
                        yield Image.open(fp=img)
                    except FileNotFoundError:
                        pass
                return

            if isinstance(clip, Image.Image):
                yield clip.copy() # Image.frombytes(mode=clip.mode, size=clip.size, data=clip.tobytes())
                return

        except:
            pass
        finally:
            return


    @classmethod
    def fingerprint_inputs(cls, **kwargs) -> str:
        # necessary for a change in the clipboard to be recognized by ComfyUI
        hash_md5 = md5()
        for img in cls.GetPILImageFromClipboard():
            hash_md5.update(img.tobytes())
        return hash_md5.digest().hex()


    @classmethod
    def execute(cls, *, alt_image: torch.Tensor | None = None, alt_mask: torch.Tensor | None = None, **kwargs) -> io.NodeOutput:
        samples: torch.Tensor | None = None
        mask: torch.Tensor | None = None

        for image in cls.GetPILImageFromClipboard():
            if image.mode == 'I':
                image = image.point(lambda i: i/255.)

            """
            convert the image to a tensor and add a batch dimension.
            Since image.convert() throws an anoing warning to the console if a palette image with transparency
            is converted with "RGB", we always convert to RGBA and trow away the extra channel in the tensor.
            """
            s: torch.Tensor = torch.from_numpy(
                        np.array(object=image.convert(mode="RGBA", )
                        ).astype(dtype=np.float32)/255.
                        )[None,:,:,:3]

            # extract the alpha channel if it exists and convert it to a mask tensor with an extra batch dimension:
            if 'A' in image.getbands():
                m: torch.Tensor = 1.0 - torch.from_numpy(
                    np.array(image.getchannel(channel='A')
                    ).astype(dtype=np.float32) / 255.)[None,]
            elif 'P' in image.mode and 'transparency' in image.info:
                m: torch.Tensor = 1.0 - torch.from_numpy(
                    np.array(image.convert(mode='RGBA').getchannel(channel='A')
                    ).astype(dtype=np.float32) / 255.0)[None,]
            else:
                m: torch.Tensor = torch.zeros(size=(1, 64, 64)) # use a default empty mask

            try:
                if samples is None:
                    samples = s
                else:
                    samples = torch.cat(tensors=(samples, s), dim=0)

                if mask is None:
                    mask = m
                else:
                    mask = torch.cat(tensors=(mask, m), dim=0)

            except RuntimeError as e:
                raise RuntimeError(f"Pasting multiple images of different shape is not supported:\n{e}")

        if samples is None or mask is None:
            raise UnidentifiedImageError("Clipboard does not contain valid image(s)!")

        return io.NodeOutput(samples, mask)


def run_test() -> None:
    from time import sleep

    print(f"{PasteImage.INPUT_TYPES()=}")
    old_sha = ""

    while True:
        print("Listen for change...")
        while (new_sha := PasteImage.fingerprint_inputs()) == old_sha:
            print(new_sha, end='\r', flush=True)
            sleep(0.1)

        print(f"\n{new_sha}")
        old_sha = PasteImage.fingerprint_inputs()

        try:
            for img in PasteImage.GetPILImageFromClipboard():
                print(img) #.show()

            tensor, mask = PasteImage.execute().args
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

        sleep(0.1)

if __name__ == "__main__":
    run_test()
