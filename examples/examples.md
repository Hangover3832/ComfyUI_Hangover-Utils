## Sympy Math Interpreter examples

[example workflow](d__sympy.json)

### Numerical derivation

![Numerical derivation](../img/math_diff.png)

Numerical 1st derivation of the second-degree polynomial `0.8*x^2+1.8*x+8.9` at the point `5.6`. With the first node, a symbolic first derivation is calculated, which is then evaluated by the second node at point `5.6`.

### Numerical integration

![alt text](../img/math_integr.png)

Numerical integration of the function `e^(-x^2)` within the limits `-20..20`

### Calculate image dimensions

![alt text](../img/image_dimensions.png)

---

## Image scale bounding box examples

![Alt text](../img/scale_openpose.png) \
_Automatic fit an openpose image to the output image size_

---

## Make Inpainting Model example

![Alt text](../img/inpaint_model_example.png) \
_Perfect inpainting with an appropriate inpainting model_


## Extract metadata data from a node

![alt text](../img/workflow_data_prompt.png)
_Extract the prompt from a Clip Text Encode node_

![alt text](../img/workflow_data_sampler.png)
_Extract cfg value and sampler name from a KSampler_
