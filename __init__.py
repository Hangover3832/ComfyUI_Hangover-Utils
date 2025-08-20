from .save_image_extra_metadata import SaveImage_NoWorkflow
from .image_scale_bounding_box import ImageScaleBoundingBox
from .inpaint_model import MakeInpaintModel
from .math_interpreter import Sympy_Interpreter
from .clipboard_paste import PasteImage


# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "Save Image w/o Metadata" : SaveImage_NoWorkflow,
    "Image Scale Bounding Box" : ImageScaleBoundingBox,
    "Make Inpaint Model": MakeInpaintModel,
    "Sympy Math Interpreter": Sympy_Interpreter,
    "Image Clipboard Paster": PasteImage,
}
