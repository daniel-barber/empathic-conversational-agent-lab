import replicate

replicate_client = replicate.Client(api_token="")

try:
    output = replicate_client.run(
        "meta/meta-llama-3-8b",
        input={
            "prompt": "Say hello to me",
            "temperature": 0.5,
            "top_p": 0.9,
            "max_tokens": 100
        }
    )
    print("Response from Replicate:")
    print(output)
except Exception as e:
    print(f"Error calling Replicate: {e}")
