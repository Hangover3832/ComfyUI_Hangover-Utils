"""
@author: AlexL
@title: ComfyUI-Hangover-Make_Inpaint_Model
@nickname: Hangover-Inpaint_Model
@description: Easy make an inpaint version of any SD1.5 model on the fly.
"""
import folder_paths
import comfy.sd
from comfy.model_patcher import ModelPatcher
from comfy_api.latest import io


class MakeInpaintModel(io.ComfyNode):
    """ Make an inpaint version of any SD1.5 model on the fly.
    """
    V1_5_PRUNED: str = "Please select the original SD 1.5 pruned model"
    V1_5_INPAINT: str = "Please select the original SD 1.5 inpaint model"
    ckpts: list[str] = folder_paths.get_filename_list(folder_name="checkpoints")
    for f in ckpts:
        if "v1-5-pruned-emaonly." in f.lower():
            V1_5_PRUNED = f
        if "v1-5-inpainting." in f.lower():
            V1_5_INPAINT = f

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Make Inpaint Model",
            display_name="Make Inpaint Model",
            category="Hangover",
            description="Easy make an inpaint version of any model on the fly.",
            search_aliases=["inpaint", "model"],
            inputs=[
                io.Model.Input("model"),
                io.Combo.Input("sd1_5_pruned", options=list(cls.ckpts), default=cls.V1_5_PRUNED),
                io.Combo.Input("sd1_5_inpaint", options=list(cls.ckpts), default=cls.V1_5_INPAINT),
            ],
            outputs=[
                io.Model.Output(),
            ],
        )

    @classmethod
    def execute(cls, *, model: ModelPatcher, sd1_5_pruned: str, sd1_5_inpaint: str, **kwargs) -> io.NodeOutput:

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
                ip.add_patches(patches={k: kp[k]}, strength_patch=-1.0, strength_model=1.0) # sd1_5_inpaint - sd1_5_pruned

            # add the input model (diff + model)
            kp = model.clone().get_key_patches(filter_prefix="diffusion_model.")
            for k in kp:
                ip.add_patches(patches={k: kp[k]}, strength_patch=1.0, strength_model=1.0) # + model
            return io.NodeOutput(ip)
        return io.NodeOutput(None)


def run_test() -> None:
    from nodes import CheckpointLoaderSimple

    ipm = MakeInpaintModel()
    inpaint_model = ipm.V1_5_INPAINT
    pruned_model = ipm.V1_5_PRUNED
    print(f"{inpaint_model=}, {pruned_model=}")
    model = CheckpointLoaderSimple().load_checkpoint(ckpt_name=pruned_model)[0]
    MakeInpaintModel.execute(model=model, sd1_5_pruned=MakeInpaintModel.V1_5_PRUNED, sd1_5_inpaint=MakeInpaintModel.V1_5_INPAINT) # type: ignore
    print("Test run succesful")


if __name__ == "__main__":
    run_test()
