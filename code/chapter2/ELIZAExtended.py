"""第二章习题 3：扩展原版 ELIZA 的规则和会话记忆。"""

import re

from ELIZA import respond as original_response
from ELIZA import swap_pronouns


DIALOGUE_RULES = (
    (r"I work as (.+)", "What do you like about working as {topic}?", "occupation"),
    (r"I am studying (.+)", "What interests you most about studying {topic}?", None),
    (r"I enjoy (.+)", "What do you enjoy most about {topic}?", None),
    (r"I feel stressed about (.+)", "What part of {topic} feels most stressful?", None),
)

MEMORY_RULES = (
    (r"My name is (.+)", "name", "I'll remember your name is {value}."),
    (r"I am ([0-9]+) years old", "age", "I'll remember you are {value} years old."),
)

MEMORY_RESPONSES = {
    "name": "You told me your name is {value}.",
    "age": "You told me you are {value} years old.",
    "occupation": "You told me you work as {value}.",
}


def respond(user_input: str, memory: dict[str, str]) -> str:
    """依次查询记忆、记录字段、匹配话题，最后交给原版规则。"""
    sentence = user_input.strip().rstrip(" .!?")
    recall = re.fullmatch(r"What is my (name|age|occupation)", sentence, re.IGNORECASE)
    if recall:
        field = recall[1].lower()
        if field not in memory:
            return f"You haven't told me your {field} yet."
        return MEMORY_RESPONSES[field].format(value=memory[field])

    for pattern, field, reply in MEMORY_RULES:
        match = re.fullmatch(pattern, sentence, re.IGNORECASE)
        if match:
            memory[field] = match[1]
            return reply.format(value=memory[field])

    for pattern, reply, field in DIALOGUE_RULES:
        match = re.fullmatch(pattern, sentence, re.IGNORECASE)
        if match:
            topic = match[1]
            if field:
                memory[field] = topic
            return reply.format(topic=swap_pronouns(topic))

    return original_response(user_input)


def main() -> None:
    memory: dict[str, str] = {}
    print("ELIZA: Hello! How can I help you today?")
    while True:
        try:
            user_input = input("You: ")
        except EOFError:
            print()
            break
        if user_input.strip().lower() in {"quit", "exit", "bye"}:
            break
        print(f"ELIZA: {respond(user_input, memory)}")
    print("ELIZA: Goodbye. It was nice talking to you.")


if __name__ == "__main__":
    main()
