"""
@author: AlexL
@title: ComfyUI-Hangover-Make_Inpaint_Model
@nickname: Hangover-Inpaint_Model
@description: Easy make an inpaint version of any model on the fly.
"""

import folder_paths
import comfy.sd
from comfy.model_patcher import ModelPatcher

class MakeInpaintModel():

    V1_5_PRUNED = "Please select the original SD 1.5 pruned model"
    V1_5_INPAINT = "Please select the original SD 1.5 inpaint model"
    ckpts = folder_paths.get_filename_list(folder_name="checkpoints")
    for f in ckpts:
        if "v1-5-pruned-emaonly." in f.lower():
            V1_5_PRUNED = f
        if "v1-5-inpainting." in f.lower():
            V1_5_INPAINT = f

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
                    "model": ("MODEL",),
                    "sd1_5_pruned": (cls.ckpts,{"default": cls.V1_5_PRUNED}),
                    "sd1_5_inpaint": (cls.ckpts,{"default": cls.V1_5_INPAINT}),
                    }
                }


    RETURN_TYPES = ("MODEL",)
    FUNCTION = "merge"
    OUTPUT_NODE = False
    CATEGORY = "Hangover"


    def merge(self, model: ModelPatcher, sd1_5_pruned: str, sd1_5_inpaint: str) -> tuple[ModelPatcher | None]:

        '''
        add difference: result =  (sd1_5_inpaint - sd1_5_pruned) + model 
        '''
        ckpt_ip = folder_paths.get_full_path(folder_name="checkpoints", filename=sd1_5_inpaint)
        ckpt_pr = folder_paths.get_full_path(folder_name="checkpoints", filename=sd1_5_pruned)
        # load original sd1.5 inpaint model:
        ip = comfy.sd.load_checkpoint_guess_config(ckpt_path=ckpt_ip, output_vae=False, output_clip=False, embedding_directory=folder_paths.get_folder_paths("embeddings"))[0]
        # load original sd1.5 pruned model
        pr = comfy.sd.load_checkpoint_guess_config(ckpt_path=ckpt_pr, output_vae=False, output_clip=False, embedding_directory=folder_paths.get_folder_paths("embeddings"))[0]
        # subtract models (inpaint - pruned)
        if ip and pr:
            kp = pr.get_key_patches(filter_prefix="diffusion_model.")
            for k in kp:
                ip.add_patches(patches={k: kp[k]}, strength_patch=-1.0, strength_model=1.0)

            # add the input model (diff + model)
            kp = model.clone().get_key_patches("diffusion_model.")
            for k in kp:
                ip.add_patches(patches={k: kp[k]}, strength_patch=1.0, strength_model=1.0)

            return ip,
        
        return None,


def run_test():
    from nodes import CheckpointLoaderSimple

    ipm = MakeInpaintModel()
    inpaint_model = ipm.V1_5_INPAINT
    pruned_model = ipm.V1_5_PRUNED
    print(f"{inpaint_model=}, {pruned_model=}")
    model = CheckpointLoaderSimple().load_checkpoint(ckpt_name=pruned_model)[0]
    ipm.merge(model=model, sd1_5_pruned=MakeInpaintModel.V1_5_PRUNED, sd1_5_inpaint=MakeInpaintModel.V1_5_INPAINT) # type: ignore
    print("Test run succesful")


if __name__ == "__main__":
    run_test()
