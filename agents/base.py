"""Agent framework — shared base class, LLM helper, and registry.

Nine agents build on this. Each declares metadata and a run() method, works on the
shared knowledge base + vector store, and degrades gracefully without an OpenAI key.
"""
import json
import os


def _load_env():
    for path in ("backend/.env", os.path.join(os.path.dirname(__file__), "..", "backend", ".env")):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"'))


_load_env()
CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o")


def has_key():
    return bool(os.environ.get("OPENAI_API_KEY"))


def llm_chat(system, user, tools=None, tool_choice="auto", temperature=0.1):
    """Thin OpenAI chat wrapper. Returns the message object (may contain tool_calls)."""
    from openai import OpenAI
    client = OpenAI()
    kwargs = {"model": CHAT_MODEL, "temperature": temperature,
              "messages": [{"role": "system", "content": system},
                           {"role": "user", "content": user}]}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice
    return client.chat.completions.create(**kwargs).choices[0].message


class Agent:
    name = "agent"
    title = "Agent"
    description = ""
    uses_llm = False

    def __init__(self, kb, store=None):
        self.kb = kb
        self.store = store

    # convenience accessors over the knowledge base
    def nodes(self, ntype=None, part_no=None):
        for n in self.kb["nodes"]:
            if ntype and n["type"] != ntype:
                continue
            if part_no and n.get("part_no") != part_no:
                continue
            yield n

    def parts(self):
        return {p["meta"]["part_no"]: p for p in self.kb["parts"]}

    def meta(self):
        return {"name": self.name, "title": self.title,
                "description": self.description, "uses_llm": self.uses_llm}

    def run(self, **kwargs):
        raise NotImplementedError
