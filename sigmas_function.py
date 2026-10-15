import torch
import numpy as np
from comfy_api.latest import io, ui
from comfy.comfy_types.node_typing import StrEnum
from sympy.parsing.sympy_parser import parse_expr
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import ast
from numpy.polynomial import Polynomial as Poly


class FunctionType(StrEnum):
    exponential = "Exponential {x^p}"
    cosine = "Cosine {cos(x), x from 0 to pi/2 }"
    gauss = "Gauss {e^-x^2 from 0 to p}"
    polynom = "Polynomial regression {least squares fit(points)}"
    polygon = "Linear interpolation {points}"
    custom = "Custom function (use x, p and s)"
    manual = "Manually enter sigmas (points)"
    manual_interp = "Manually enter sigmas and interpolate to `steps`"
    qwen21 = "Qwen Image 2.1 sigmas"


class SigmasFunction(io.ComfyNode):
    """ Create sigmas from a function:
    """

    QWEN_SIGMAS = (1.0,0.978453,0.95418,0.926626,0.89508,0.845148,0.704534,0.414568,0.0)

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="hangover_sigmas_function",  # keep the V1 class type so existing workflows still resolve
            display_name="Hangover Sigmas Function",
            description="Create sigmas from an function with a parameter",
            category="Hangover",
            search_aliases=["sigmas", "function", "scheduler", "math"],
            inputs=[
                io.Combo.Input("function", options=FunctionType),
                io.Int.Input("steps", default=8, min=2),
                io.Float.Input("p", default=0.5, step=0.001, tooltip="parameter p"),
                io.Float.Input("scale", default=1.0, step=0.001, tooltip="scale factor (after clipping)"),
                io.String.Input("points", default="(0.0,1.0), (0.5,0.25), (1.0,0.0)", tooltip="points in pairs (x0, y0), (x1, y1), ..., where x should range from 0.0 to 1.0, parameter p is availabe",),
                io.String.Input("custom_function", default="1-(x**p)", tooltip="parameters x, p and s (scale) are abvailabe"),
                io.Float.Input("x_from", default=0.0, step=0.001),
                io.Float.Input("x_to", default=1.0, step=0.001),
                io.Boolean.Input("clip", default=True, tooltip="clip the output between [0..1]")
            ],
            outputs=[
                io.Sigmas.Output(display_name="sigmas"),
            ],
        )

    @staticmethod
    def _eval_expression(expression:str, x:float, p:float, s:float) -> float:
        return float(parse_expr(expression, local_dict={'x': x, 'p': p, 's': s}))

    @staticmethod
    def gauss(x:float | torch.Tensor) -> torch.Tensor:
        'g(x) = e^(-(x^2))'
        return torch.exp(-torch.square(torch.as_tensor(x)))

    @classmethod
    def execute(cls, *,
                function:FunctionType,
                steps:io.Int.Type,
                p:io.Float.Type,
                scale:io.Float.Type,
                points:io.String.Type,
                custom_function:io.String.Type,
                x_from:io.Float.Type,
                x_to:io.Float.Type,
                clip:io.Boolean.Type,
                **kwargs) -> io.NodeOutput:

        if function == FunctionType.exponential:
            linspace = torch.linspace(1.0, 0.0, steps+1)
            sigmas = linspace ** p

        elif function == FunctionType.cosine:
            linspace = torch.linspace(0, torch.pi/2.0, steps+1)
            sigmas = torch.cos(linspace)

        elif function == FunctionType.gauss:
            x = torch.linspace(0.0, p, steps+1)
            gauss_p = cls.gauss(p)
            gauss_x = cls.gauss(x)
            sigmas = (gauss_x - gauss_p) / (1 - gauss_p) # normalize to constraints [0..1, 0..1]

        elif function == FunctionType.custom:
            linspace = torch.linspace(x_from, x_to, steps+1)
            cf = lambda x: cls._eval_expression(custom_function, x, p, scale)
            sigmas = linspace.apply_(cf)

        elif function in [FunctionType.manual, FunctionType.manual_interp, FunctionType.qwen21]:
            if function == FunctionType.qwen21:
                sigmas = torch.tensor(cls.QWEN_SIGMAS) # qwen sigmas
            else:
                try:
                    sigmas_: tuple[float] = ast.literal_eval(f"({points.lower().replace('p', str(p))})")
                    sigmas = torch.tensor(sigmas_).flatten()
                except (SyntaxError, ValueError) as e:
                    raise ValueError(f"Error: Input sigmas as a comma separated list of numbers (1.0, 0.3, ...): {e}")

            if function in [FunctionType.manual_interp, FunctionType.qwen21]:
                linspace = torch.linspace(0.0, 1.0, steps=steps+1)
                x_values = torch.linspace(0.0, 1.0, len(sigmas))
                y_values = sigmas
                sigmas = torch.from_numpy(np.interp(x=linspace, xp=x_values, fp=y_values))

        elif function in [FunctionType.polynom, FunctionType.polygon]:
            try:
                pts: list[tuple[float, float]] = [(float(x), float(y)) for x, y in ast.literal_eval(points.lower().replace('p', str(p)))]
                if (n := len(pts)) < 2:
                    raise ValueError
            except (TypeError, ValueError) as e:
                raise ValueError(f"Points mut be at least two pairs of (x0,y0), (x1,y1), ..., {e}")

            x_values, y_values = zip(*pts)
            linspace = torch.linspace(0.0, 1.0, steps+1)

            if function == FunctionType.polynom:
                poly = Poly.fit(x_values, y_values, deg=n-1)
                sigmas = linspace.apply_(poly)

            else: # function == FunctionType.polygon:
                xp, fp = np.array(x_values), np.array(y_values)
                sigmas = torch.from_numpy(np.interp(x=linspace, xp=xp, fp=fp))

        else:
            raise ValueError(f"Unknown function type: {function.name}")

        sigmas = scale * torch.clamp(sigmas, 0.0, 1.0) if clip else scale * sigmas
        return io.NodeOutput(torch.round(sigmas, decimals=5).type(dtype=torch.float32))


class PlotSigmas(io.ComfyNode):
    """ Plot the sigmas as a 1024x512 image. """

    PLOT_DPI = 100

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
                io.Sigmas.Input("sigmas2", optional=True),
            ],
            outputs=[
                io.Image.Output(display_name="image"),
            ],
            is_output_node=True,
        )

    @classmethod
    def execute(cls, *, sigmas:io.Sigmas.Type, sigmas2:io.Sigmas.Type | None = None, **kwargs) -> io.NodeOutput:
        values = sigmas.flatten().tolist()
        values2 = sigmas2.flatten().tolist() if sigmas2 is not None else None

        fig = Figure(figsize=(1024 / cls.PLOT_DPI, 512 / cls.PLOT_DPI), dpi=cls.PLOT_DPI)
        ax = fig.add_subplot(111)
        ax.plot(range(0, len(values)), values, marker="o")
        if values2 is not None:
            ax.plot(range(0, len(values2)), values2, marker="x")
        ax.set_xlabel("step")
        ax.set_ylabel("sigma")
        ax.grid(True)

        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        w, h = canvas.get_width_height()
        rgb = np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8).reshape(h, w, 4)[:, :, :3]
        image = torch.from_numpy(rgb.astype(np.float32) / 255.0)[None,]

        return io.NodeOutput(image, ui=ui.PreviewImage(image))


def _run_tests():
    result = SigmasFunction.execute(function=FunctionType.custom, steps=10, p=2.0, scale=1.0, custom_function="p-x", x_from=0, x_to=1.0, points="", clip=True)
    print(result.args)
    plot = PlotSigmas.execute(sigmas=result.args[0])
    print(plot.args[0].shape, plot.args[0].dtype, plot.args[0].min().item(), plot.args[0].max().item())


if __name__ == "__main__":
    _run_tests()
