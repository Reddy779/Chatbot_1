def build_system_prompt(
        user_facts: list[str],
        summaries: list[str],
) -> str:
    """
    Builds the full system prompt injected at the top of every LLM call.
    The richer this prompt, the more personalized the response.
    """
    prompt = "you are a helpful, friendly, and highly personalized assistant.\n\n"

    # - User facts section
    if user_facts:
        prompt += "THINGS YOU KNOW ABOUT THIS USER: \n"
        for fact in user_facts:
            prompt += f"- {fact}\n"
        prompt += "\n"
    else:
        prompt += "You do not know anything specific about this user yet.\n\n"

    # Past summaries section
    if summaries:
        prompt += "SUMMARIES OF PAST CONVERSATIONS WITH THIS USER:\n"
        for i, summary in enumerate(summaries, 1):
            prompt += f"{i}. {summary}\n"
        prompt += "\n"

    # Behaviour instructions
    prompt += (
        "INSTRUCTIONS:\n"
        "- Use everything you know about the user to personalize your responses.\n"
        "- If you know their name, use it naturally in conversation.\n"
        "- If you know their preferences, apply them without being asked.\n"
        "- Be concise, warm, and helpful.\n"
        "- Respond in plain text only.\n"
    )

    return prompt


FACT_EXTRACTION_PROMPT = """You are an AI that extracts personal facts about a user from a conversation.

Given this conversation:
{conversation}

Extract any NEW personal facts about the user such as:
- Their name
- Their location
- Their job or profession
- Their preferences (e.g. likes dark mode, prefers Python)
- Their habits or routines
- Any other personal detail they mentioned

Rules:
- Return ONLY a Python list of short fact strings
- Each fact must be under 20 words
- If no new facts found, return an empty list []
- Do not include facts already known: {existing_facts}

Return format example:
["name is Dhanush", "lives in Bangalore", "prefers dark mode", "works as a software engineer"]

Return ONLY the list, nothing else:"""


SUMMARY_PROMPT = """You are an AI that summarizes conversations.

Summarize this conversation in 3-5 sentences:
{conversation}

Rules:
- Focus on what the user talked about and what was resolved
- Include any important facts or decisions
- Be concise and factual
- Write in third person (e.g. "The user asked about...")

Return ONLY the summary, nothing else:"""