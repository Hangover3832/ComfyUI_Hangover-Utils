"""
@author: AlexL
@title: ComfyUI-Hangover-Sympy_Interpreter
@nickname: Hangover-Sympy_Interpreter
@description: A mathematic expression interpreter based on the sympy library

V3 node with io.Autogrow for dynamically growing numeric inputs (a, b, c, …).
"""
import math
import string
from sympy.parsing.sympy_parser import parse_expr
from comfy_api.latest import io, ui



class SympyInterpreter(io.ComfyNode):
    """Mathematical expression interpreter based on SymPy.

    Allows adding unlimited inputs at runtime via the Autogrow mechanism.
    Ports are automatically named a, b, c, … (lowercase letters).
    """

    HELP = """
- **Arithmetic operators**: `+`, `-`, `*`, `/`, `**` (power), `%` (modulo)  
- **Relational operators**: `=`, `==`, `!=`, `<`, `>`, `<=`, `>=` (the `=` can be turned into `Eq` with the *convert_equals_signs* transformation)  
- **Factorial notation**: `!` (e.g. `x!`)  

**Built‑in constants**:

| Constant | Symbol |
|----------|--------|
| pi | `pi` |
| e | `E` |
| infinity | `oo` |
| Golden ratio | `golden_ratio` |
| … (other built‑in constants) |  |

**Built‑in functions**:

- **Elementary functions**: `sin`, `cos`, `tan`, `csc`, `sec`, `cot`, `asin`, `acos`, `atan`, `acsc`, `asec`, `acot`, `sinh`, `cosh`, `tanh`, `asinh`, `acosh`, `atanh`
- **Exponential & logarithmic**: `exp`, `log`, `ln`
- **Roots & powers**: `sqrt`, `cbrt`, `root`
- **Trigonometric inverses** (e.g. `asin`, `acos`, …) and hyperbolic inverses
- **Special functions**: `gamma`, `loggamma`, `digamma`, `polygamma`, `erf`, `erfc`, `Ei`, `Si`, `Ci`, `zeta`
- **Piecewise & conditional**: `Piecewise`, `Heaviside`, `sign`
- **Absolute & rounding**: `Abs`, `sign`, `floor`, `ceiling`, `round`
- **Factorial & gamma‑related**: `factorial`, `rf`, `binomial`
- **Combinatorial**: `perm`, `nC`, `nPr`
- **Complex‑number helpers**: `re`, `im`, `conjugate`
- **Symbolic utilities**: `diff`, `integrate`, `limit`, `summation`, `product`, `Series`, `expand`, `simplify`
- **Set operators**{}: `Union`, `Intersection`, `Complement`, `FiniteSet`, `Interval`, `ImageSet`
- **Logical / relational** (if `allow_sets=True`): `And`, `Or`, `Not`, `Implies`, `Equivalent`

"""


    @classmethod
    def define_schema(cls) -> io.Schema:
        autogrow_aw = io.Autogrow.TemplateNames(
            input=io.MultiType.Input("value", [io.Float, io.Int, io.Boolean]),
            names=list("abcdefghijklmnopqrstuvw"),  # a, b, c, d, … 
            min=0,
        )
        autogrow_xyz = io.Autogrow.TemplateNames(
            input=io.MultiType.Input("value", [io.Float, io.Int]),
            names=list("xyz"),  # x, y, z 
            min=0,
        )
        return io.Schema(
            node_id="SympyInterpreter",
            display_name="Sympy Interpreter",
            description="Mathematical expression interpreter based on SymPy",
            category="Hangover",
            search_aliases=[
                "sympy", "math", "interpreter", "expression",
                "form", "calculate", "evaluate", "symbolic",
            ],
            inputs=[
                io.String.Input("expression", default="a", multiline=True,),
                io.Autogrow.Input("values", template=autogrow_aw),
                io.Autogrow.Input("xyz", template=autogrow_xyz),
            ],
            outputs=[
                io.Int.Output(display_name="int"),
                io.Float.Output(display_name="float"),
                io.String.Output(display_name="str"),
                io.Boolean.Output(display_name="bool"),
                io.String.Output(display_name="help"),
            ],
        )


    @classmethod
    def execute(cls, *, 
                expression: io.String.Type, 
                values: io.Autogrow.Type, 
                xyz: io.Autogrow.Type, 
                **kwargs) -> io.NodeOutput:
        """Evaluate the expression and return the results."""

        expression = expression.strip()
        if not expression:
            raise ValueError("Expression cannot be empty.")

        # Gather dynamic ports as dict (a, b, c, …)
        variables: dict = dict(values)
        variables.update(dict(xyz))

        print(f"Math_Interpreter: evaluating expression '{expression}'")
        print(f"  Variables: {variables}")

        expr_A = parse_expr(s=expression, local_dict=variables)

        try:
            result_A = float(expr_A)
        except TypeError:
            result_A = 0.0  # symbolic result, only str_A is meaningful

        result_str = str(expr_A)
        return io.NodeOutput(
            math.floor(result_A),
            result_A,
            result_str,
            result_str == "True",
            cls.HELP,
            ui=ui.PreviewText(result_str),
        )
