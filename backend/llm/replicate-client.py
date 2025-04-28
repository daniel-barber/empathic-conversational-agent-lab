import replicate

REPLICATE_MODEL = "meta/meta-llama-3-8b-instruct"  

def generate_response(user_input: str) -> str:
    output = replicate.run(
        REPLICATE_MODEL,
        input={
            "prompt": user_input,
            "stop": ["User:", "Assistant:", "Bot:"]
        }
    )
    if isinstance(output, list):
        output = "".join(output)
    return output.strip()

