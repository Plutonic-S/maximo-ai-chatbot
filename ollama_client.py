import os
import json
from dotenv import load_dotenv
import requests
from tool_schemas import TOOL_FUNCTIONS, TOOL_ARG_MODELS, TOOL_SCHEMAS

# load from env
load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")


def chat_with_tools(user_message: str, max_rounds: int = 8) -> str:
    system_instruction = (
        "You are the IBM Maximo AI Assistant, a copilot for querying Maximo Asset Management data. "
        "You have tools to look up service requests/tickets, locations, and classifications — call the relevant tool "
        "for any question about real Maximo data. Never invent ticket IDs, locations, statuses, counts, or any other "
        "Maximo data; only state what a tool result actually returned. "
        "If asked for a total or count, call the relevant tool with count_only=True instead of counting rows yourself — "
        "this uses Maximo's native ?count=1 OSLC parameter and returns an exact number instantly. "
        "You may call more than one tool, or the same tool again with different filters, before giving your final answer. "
        "When a request needs the same kind of lookup repeated for several items (e.g., service requests for each of "
        "several different locations), make all of those calls together in the same turn — you can call the same tool "
        "multiple times in one turn — rather than spreading them one at a time across multiple turns; you only get a "
        "limited number of turns. "
        "If a tool call fails (its result has \"success\": false), tell the user what went wrong in plain language "
        "instead of pretending it worked. For general conversation unrelated to Maximo data, just answer directly "
        "without calling a tool.\n\n"
        "When presenting tabular results (tickets, locations, classifications), always format them as a "
        "GitHub-Flavored Markdown table, one row per line, with a header row and separator row. Example:\n"
        "| Ticket ID | Location | Status | Description | Reported By | Date Reported |\n"
        "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        "| 1187 | 764750 | NEW | Keyboard issue | MAXADMIN | 2025-03-02 |\n"
    )

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_message},
    ]

    for round_num in range(max_rounds):
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "tools": TOOL_SCHEMAS,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        response = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload)
        response.raise_for_status()

        response_data = response.json()
        response_message = response_data["message"]
        messages.append(response_message)

        if not response_message.get("tool_calls"):
            return response_message.get("content") or ""

        for tool_call in response_message.get("tool_calls", []):
            func_info = tool_call["function"]
            name = func_info["name"]
            raw_args = func_info.get("arguments", {})

            arg_model = TOOL_ARG_MODELS.get(name)
            func = TOOL_FUNCTIONS.get(name)

            if not arg_model or not func:
                result = {"success": False, "error": f"Unknown tool: {name}"}
            else:
                try:
                    validated_args = arg_model(**raw_args)
                    result = func(**validated_args.model_dump())
                except Exception as e:
                    result = {"success": False, "error": f"Execution error: {str(e)}"}

            messages.append(
                {
                    "role": "tool",
                    "tool_name": name,
                    "content": json.dumps(result),
                }
            )

    return "Maximum tool execution rounds reached without a final response."
