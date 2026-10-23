# Standard library imports
import os
from types import SimpleNamespace

# Third-party imports
from openai import OpenAI
from dotenv import load_dotenv

# Local modules
from tools import TOOLS, run_tool
from Utilities.utilities import log



load_dotenv() #by deafult looks for .env file

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)

messages = [
    {
        "role": "system",
        "content": "Always respond in English."
    },
    {
        "role": "system",
        "content": (
            "Your are a helpful, humble assistant."
            "Answer general questions (programming, science, advice) from your own knowledge."
            "Use a tool ONLY when the user asks for the current time, the weather, or their city."
            "Keep answers under 100 words."
        )
    }
]

def stream_chat(history):
    stream = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=history,
        tools=TOOLS,
        stream=True
    )

    full_response = ""
    calls = {} # index -> tool call being built
    label_printed = False

    # Streaming started
    try:
        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            #1. Content Streaming : Do we have message (content) from the LLM
            if delta.content:
                if not label_printed:
                    print("🤖 Assistant: ", end="", flush=True)
                    label_printed = True
                print(delta.content, end="", flush=True)
                full_response += delta.content

            #2. Tool Calls
            for tc in (delta.tool_calls or []):
                obj = calls.setdefault(
                    tc.index,
                    SimpleNamespace(id=None, function=SimpleNamespace(name="", arguments="")),
                )
                if tc.id:
                    obj.id = tc.id
                if tc.function and tc.function.name:
                    obj.function.name += tc.function.name
                if tc.function and tc.function.arguments:
                    obj.function.arguments += tc.function.arguments

    except KeyboardInterrupt as e:
        print("\n {Stopped by You}")
        calls = {}

    if label_printed:
        print() # Move to the next line after the assistant's response

    calls_list = []
    for key in sorted(calls):
        calls_list.append(calls[key])

    return full_response, list(calls.values())


def build_tool_calls_payload(tool_calls):
    """
    Converts our collected tool calls into the dict format 
    that the API expects inside an assistant message.
    """

    payload = []
    for tool_call in tool_calls:
        tool_call_dict = {
            "id": tool_call.id,
            "type": "function",
            "function": {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments,
            },
        }
        payload.append(tool_call_dict)

    return payload

# Safety limit: the max number of model rounds for ONE user question
MAX_STEPS = 5

# Chat loop starts from here
while True:

    user_input = input("\n👦🏻 User: ")

    if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
        print("Exiting the assistant. Goodbye!")
        break

    messages.append(
        {
            "role": "user",
            "content": user_input
        }   
    )

    # Chained Tool Calling: The assistant can call multiple tools in a single response, and the tools can call each other in a chain.
    for step in range(MAX_STEPS):

        full_response, tool_calls = stream_chat(messages)

        # print("Assistant (raw): " + str(response)) # Raw response from the LLM model: qwen3:4b

        # msg = response.choices[0].message

        if not tool_calls:
            break

        log(f"Step {step + 1}: model requested {len(tool_calls)}") # Debug log for tool calls

        # messages.append(msg)
        messages.append({
            "role": "assistant",
            "content": full_response,
            "tool_calls": build_tool_calls_payload(tool_calls)
        })

        for tool_call in tool_calls:
            result = run_tool(tool_call)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                }
            )

        # # 2nd call to the LLM API

        # response = client.chat.completions.create(
        #     model=os.getenv("MODEL"),
        #     messages=messages
        # )

        # msg = response.choices[0].message

    else:
        # Ran out of steps: The model never gave the final answer
        fallback = "Sorry, I could not finish this within the step limit."
        messages.append(
            {
                "role": "assistant",
                "content": fallback
            }
        )
        print("🤖 Assistant: " + fallback) # Response from the LLM model: qwen3:4b
        continue

    # Save the assistant's final reply so it is remembered in later turns.
    # (The text was already streamed live in stream_chat, so we don't print it again.)
    messages.append(
        {
            "role": "assistant",
            "content": full_response
        }
    )

    # messages.append(
    #     {
    #         "role": "assistant",
    #         "content": response.choices[0].message.content
    #     }
    # )

    # # print("LLM response:")
    # print("Assistant: " + response.choices[0].message.content) # Response from the LLM model: qwen3:4b
    # # print(response.choices[0].message.role) # Full response object from the LLM model: qwen3:4b