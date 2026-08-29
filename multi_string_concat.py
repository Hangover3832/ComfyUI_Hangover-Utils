from comfy_api.latest import io


class MultiStringConcat(io.ComfyNode):
    """ Concatenates all input strings with delimitter"""

    @classmethod
    def define_schema(cls) -> io.Schema:
        template = io.Autogrow.TemplatePrefix(
            input=io.String.Input("text"),
            prefix="text",
            min=0,
            max=25,
        )
        return io.Schema(
            node_id="hangover_StringConcat",
            display_name="Hangover Multi String Concatenate",
            category="Hangover",
            description=(
                "Concatenates all input strings."
            ),
            inputs=[
                io.String.Input("delimiter", default=""),
                io.Autogrow.Input("text", template=template),
            ],
            outputs=[
                io.String.Output("string"),
            ],
        )


    @classmethod
    def execute(cls, *, delimiter:str = "", text: io.Autogrow.Type, **kwargs) -> io.NodeOutput:
        """ Join the autogrow string values with a space when use_text is True,
        otherwise return the fallback string."""
        joined = delimiter.join(str(v) for v in text.values())
        return io.NodeOutput(joined)
