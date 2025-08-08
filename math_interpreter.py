"""
@author: AlexL
@title: ComfyUI-Hangover-Sympy_Interpreter
@nickname: Hangover-Sympy_Interpreter
@description: A mathematic expression interpreter based on the sympy library
"""
from sympy import *
from sympy.parsing.sympy_parser import parse_expr
from comfy.comfy_types import IO

Math_Interpreter_Config = {
    "num_vars": 6,
}


class Sympy_Interpreter:
    RETURN_TYPES = (
        IO.INT,
        IO.FLOAT,
        IO.STRING,
    )
    RETURN_NAMES = (
        "int_A",
        "float_A",
        "str_A",
    )

    FUNCTION = "calc"
    CATEGORY = "Hangover"

    Input_Vars = [chr(c + ord("a")) for c in range(Math_Interpreter_Config["num_vars"])]
    Variables = {key: (IO.ANY,) for key in Input_Vars}

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "expression_A": (IO.STRING, {"multiline": False, "default": "0"}),
            },
            "optional":
                s.Variables,
        }

    def calc(self, expression_A:str, **kwargs):
        print(f"Math_Interpreter: evaluating expression A({expression_A})")
        expr_A = parse_expr(expression_A, local_dict=kwargs)
        try:
            result_A = float(expr_A)
        except TypeError:
            result_A = 0.0

        return (
            floor(result_A),
            result_A,
            str(expr_A),
        )


def test_Sympy_Interpreter():
    math = Sympy_Interpreter()
    input_types = math.INPUT_TYPES()
    res_int, res_flt, res_str = math.calc("a**2", a=5)
    print(f"{input_types=}")
    print(f"{res_int=}, {res_flt=}, {res_str=}")


if __name__ == "__main__":
    test_Sympy_Interpreter()
