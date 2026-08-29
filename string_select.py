from comfy_api.latest import io


class StringSelect(io.ComfyNode):
    """ Select a string from a boolean: return the joined input text when the toggle is on,
    otherwise return the fallback string."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        template = io.Autogrow.TemplatePrefix(
            input=io.String.Input("text"),
            prefix="text",
            min=1,
            max=10,
        )
        return io.Schema(
            node_id="hangover_StringSelect",
            display_name="Hangover String Select",
            category="Hangover",
            description=(
                "Selects a string from a boolean. Returns the joined input text when the "
                "boolean is True, otherwise returns the fallback string."
            ),
            inputs=[
                io.Autogrow.Input("text", template=template),
                io.Boolean.Input(
                    "use_text",
                    default=True,
                    label_on="Return text",
                    label_off="Return fallback",
                ),
            ],
            outputs=[
                io.String.Output("string"),
            ],
        )

    @classmethod
    def execute(cls, *, text: io.Autogrow.Type, use_text: bool = True, **kwargs) -> io.NodeOutput:
        """ Join the autogrow string values with a space when use_text is True,
        otherwise return the fallback string."""
        fallback = "fallback"
        joined = " ".join(str(v) for v in text.values())
        return io.NodeOutput(joined if use_text else fallback)
