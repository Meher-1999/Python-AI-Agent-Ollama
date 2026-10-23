# Standard library imports
import os

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

# Safety limit: the max number of model rounds for ONE user question
MAX_STEPS = 5

while True:

    user_input = input("\nUser: ")

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

        response = client.chat.completions.create(
            model=os.getenv("MODEL"),
            messages=messages,
            tools=TOOLS
        )
        # print("Assistant (raw): " + str(response)) # Raw response from the LLM model: qwen3:4b

        msg = response.choices[0].message

        if not msg.tool_calls:
            break

        log(f"Step {step + 1}: model requested {len(msg.tool_calls)}") # Debug log for tool calls

        messages.append(msg)

        for tool_call in msg.tool_calls:
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
        print("Assistant: " + fallback) # Response from the LLM model: qwen3:4b
        continue

    messages.append(
        {
            "role": "assistant",
            "content": msg.content
        }
    )

    print("Assistant: " + (msg.content or "")) # Response from the LLM model: qwen3:4b

    # messages.append(
    #     {
    #         "role": "assistant",
    #         "content": response.choices[0].message.content
    #     }
    # )

    # # print("LLM response:")
    # print("Assistant: " + response.choices[0].message.content) # Response from the LLM model: qwen3:4b
    # # print(response.choices[0].message.role) # Full response object from the LLM model: qwen3:4b