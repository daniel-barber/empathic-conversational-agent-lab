# backend/replicate_client_chatbot.py

import replicate

class ReplicateClientChatbot:
    """
    Encapsulates interactions with the Replicate LLaMA-3 model,
    streaming exactly one clean sentence per user query.
    """

    DEFAULT_MODEL = "mistralai/mistral-7b-instruct"
    DEFAULT_SYSTEM_PROMPT = (
        "You are an empathetic, helpful, and friendly AI assistant. "
        "Answer the user's question in exactly one sentence and then stop. "
        "Do NOT ask follow-up questions or include any “User:” lines. "
        "Wait for the next user input."
    )

    def __init__(self, api_token: str, model: str = None, timeout: tuple[float, float] = (5, 300)):
        """
        :param api_token: your REPLICATE_API_TOKEN
        :param model: replicate model name (defaults to LLaMA-3 8B instruct)
        :param timeout: (connect_timeout, read_timeout)
        """
        self.client = replicate.Client(api_token=api_token, timeout=timeout)
        self.model = model or self.DEFAULT_MODEL

    def generate_response(
        self,
        user_input: str,
        history: list[dict] = None,
        system_prompt: str = None,
        top_p: float = 0.9,
        temperature: float = 0.7,
        presence_penalty: float = 1.15,
        max_tokens: int = 100,
        stop_sequences: list[str] = None,
    ) -> str:
        """
        Builds a prompt from the system instruction + history + new user_input,
        then streams back (cutting at stop markers).
        """
        # 1) choose or override the system prompt
        sp = system_prompt or self.DEFAULT_SYSTEM_PROMPT

        # 2) assemble the full prompt
        full_prompt = sp + "\n\n"
        if history:
            for turn in history:
                speaker = "User" if turn["role"] == "user" else "Assistant"
                full_prompt += f"{speaker}: {turn['content']}\n"
        full_prompt += f"User: {user_input}\nAssistant:"

        # 3) prepare replicate input
        stops = stop_sequences or ["\nUser:", "\nAssistant:"]
        payload = {
            "prompt": full_prompt,
            "prompt_template": "{prompt}",
            "top_p": top_p,
            "temperature": temperature,
            "presence_penalty": presence_penalty,
            "max_tokens": max_tokens,
            "stop": stops,
        }

        # 4) stream & cut at first marker
        response = ""
        for chunk in self.client.stream(self.model, input=payload):
            text = str(chunk)
            # check if any stop marker appears in this chunk or accumulated text
            response += text
            for marker in stops:
                idx = response.find(marker)
                if idx != -1:
                    return response[:idx].strip()
        return response.strip()
