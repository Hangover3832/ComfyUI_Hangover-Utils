import torch
import numpy as np
from comfy_api.latest import io, ui
from comfy.comfy_types.node_typing import StrEnum
from sympy.parsing.sympy_parser import parse_expr
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

PLOT_DPI = 100


class FunctionType(StrEnum):
    exponential = "Exponential (x^p)"
    cosine = "Cosine (from 0 to pi/2)"
    gauss = "Gauss (e^-x^2 from 0 to p)"
    custom = "Custom function (use x and p)"


class SigmasFunction(io.ComfyNode):
    """ Create exponential sigmas:
    output = input ^ exponent
    """
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="hangover_sigmas_function",  # keep the V1 class type so existing workflows still resolve
            display_name="Hangover Sigmas Function",
            description="Create sigmas from an function with a parameter",
            category="Hangover",
            search_aliases=["sigmas", "exponential", "scheduler"],
            inputs=[
                io.Combo.Input("function", options=FunctionType),
                io.Int.Input("steps", default=8, min=2),
                io.Float.Input("p", default=1.0, step=0.001),
                io.String.Input("custom_function", default="x**p"),
                io.Float.Input("x_from", default=0.0, step=0.001),
                io.Float.Input("x_to", default=1.0, step=0.001),
            ],
            outputs=[
                io.Sigmas.Output(display_name="sigmas"),
                io.Int.Output("steps")
            ],
        )

    @staticmethod
    def _eval_expression(expression:str, x:float, p:float) -> float:
        return float(parse_expr(expression, local_dict={'x': x, 'p': p}))


    @classmethod
    def execute(cls, *,
                function:FunctionType,
                steps:io.Int.Type,
                p:io.Float.Type,
                custom_function:io.String.Type,
                x_from:io.Float.Type,
                x_to:io.Float.Type,
                **kwargs) -> io.NodeOutput:

        sigmas = torch.tensor([1.0, 0.0])
        match function:
            case FunctionType.exponential:
                linspace = torch.linspace(1.0, 0.0, steps+1)
                sigmas = linspace ** p

            case FunctionType.cosine:
                linspace = torch.linspace(0, torch.pi/2.0, steps+1)
                sigmas = torch.cos(linspace)

            case FunctionType.gauss:
                linspace = torch.linspace(0.0, p, steps+1)
                sigmas = torch.exp(-torch.square(linspace))

            case FunctionType.custom:
                linspace = torch.linspace(x_from, x_to, steps+1)
                f = lambda x: cls._eval_expression(custom_function, x, p)
                sigmas = linspace.apply_(f)


        sigmas = torch.round(sigmas, decimals=5)
        return io.NodeOutput(sigmas, steps)


class PlotSigmas(io.ComfyNode):
    """ Plot the sigmas as a 1024x512 image. """
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="hangover_plot_sigmas",
            display_name="Plot Sigmas",
            description="Plot sigmas as a 1024x512 image",
            category="Hangover",
            search_aliases=["sigmas", "plot", "graph", "scheduler"],
            inputs=[
                io.Sigmas.Input("sigmas"),
            ],
            outputs=[
                io.Image.Output(display_name="image"),
            ],
            is_output_node=True,
        )

    @classmethod
    def execute(cls, *, sigmas:io.Sigmas.Type, **kwargs) -> io.NodeOutput:
        values = sigmas.flatten().tolist()

        fig = Figure(figsize=(1024 / PLOT_DPI, 512 / PLOT_DPI), dpi=PLOT_DPI)
        ax = fig.add_subplot(111)
        ax.plot(range(len(values)), values, marker="o")
        ax.set_xlabel("step")
        ax.set_ylabel("sigma")
        ax.grid(True)

        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        w, h = canvas.get_width_height()
        rgb = np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8).reshape(h, w, 4)[:, :, :3]
        image = torch.from_numpy(rgb.astype(np.float32) / 255.0)[None,]

        return io.NodeOutput(image, ui=ui.PreviewImage(image))


if __name__ == "__main__":
    result = SigmasFunction.execute(function=FunctionType.custom, steps=10, p=10.0, custom_function="p-x", x_from=0, x_to=1.0)
    print(result.args)
    plot = PlotSigmas.execute(sigmas=result.args[0])
    print(plot.args[0].shape, plot.args[0].dtype, plot.args[0].min().item(), plot.args[0].max().item())
