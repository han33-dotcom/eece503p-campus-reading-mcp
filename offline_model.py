"""A scripted SDK test double. This is NOT an OpenAI model or language reasoner."""
import json
from uuid import uuid4

from agents import Model, ModelResponse, Usage
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage, ResponseOutputText


class ScriptedDemoModel(Model):
    """Return one specified tool call, then report the actual tool response."""

    def __init__(self, tool_name: str, arguments: dict):
        self.tool_name = tool_name
        self.arguments = arguments

    async def get_response(self, system_instructions, input, model_settings, tools,
                           output_schema, handoffs, tracing, **kwargs):
        outputs = [item for item in input if isinstance(item, dict)
                   and item.get("type") == "function_call_output"] if isinstance(input, list) else []
        if outputs:
            text = "Actual MCP result: " + str(outputs[-1]["output"])
            output = [ResponseOutputMessage(id="msg_" + uuid4().hex, type="message",
                      role="assistant", status="completed",
                      content=[ResponseOutputText(type="output_text", text=text, annotations=[])])]
        else:
            names = {tool.name for tool in tools}
            if self.tool_name not in names:
                raise RuntimeError(f"Tool not discovered through MCP: {self.tool_name}")
            output = [ResponseFunctionToolCall(type="function_call", name=self.tool_name,
                      arguments=json.dumps(self.arguments), call_id="call_" + uuid4().hex)]
        return ModelResponse(output=output, usage=Usage(), response_id=None)

    async def stream_response(self, *args, **kwargs):
        raise NotImplementedError("The offline test double supports non-streaming runs only.")
        yield  # Makes this method an async iterator, as required by Model.
