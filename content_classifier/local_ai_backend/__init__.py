from llama_cpp import LlamaGrammar

from content_classifier.clean_obfuscate_text import clean_text
from tags import ContentCategory
from content_classifier.local_ai_backend.ai_assistant import LocalLLM

# TODO: DOc mot luc cac TODO truoc khi bat dau lam viec
# TODO: lam he thong config + log
# TODO: Nghi ra idea load san model
# TODO: Dung git

model_path = "/home/eubebhy/Downloads/gemma-3-1b-it-Q5_K_M.gguf"
# Prefer short system prompt
system_prompt = """
Classify the content of the user's text into one of these labels:

- gore
- porn
- game
- unknown

Classification is based solely on the content of the text. Detect whether the text contains words, phrases, names, or references related to games, pornography, gore, or other relevant topics.

Rules:
- Return exactly one label in lowercase.
- Return only the label. Do not explain your answer.
- Choose the most specific matching label.
- If none of the labels clearly apply, return `unknown`.
""".strip()

temperature = 0.0
max_tokens = 100
top_p = 1.0
n_ctx = 512
repeat_penalty = 1.0
llm = LocalLLM(model_path=model_path, n_ctx=n_ctx)
grammar = LlamaGrammar.from_string(
    r"""
root ::= label
label ::= "gore" | "porn" | "game" | "unknown"
"""
)


def local_ai_classifier(text: str) -> list[ContentCategory]:
    text = clean_text(text=text)
    ai_output = llm.ask(
        prompt=text,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        repeat_penalty=repeat_penalty,
        grammar=grammar,
    )

    category_map = {
        "gore": ContentCategory.Gore,
        "porn": ContentCategory.Pornography,
        "game": ContentCategory.Game,
        "unknown": ContentCategory.Unknown,
    }

    token = ai_output.strip().lower().split(maxsplit=1)[0] if ai_output.strip() else ""
    res = [category_map[token]] if token in category_map else []

    return res or [ContentCategory.Unknown]
