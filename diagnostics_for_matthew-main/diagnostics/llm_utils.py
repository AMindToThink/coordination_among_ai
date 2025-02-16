from openai import OpenAI
from api_keys import openai_api_key, perplexity_api_key

def query_gpt(prompt, api_key=openai_api_key, model="gpt-4o"):
    """
    Query the OpenAI GPT API with the given prompt.
    
    :param prompt: The input text to send to GPT
    :param api_key: Your OpenAI API key
    :param model: The GPT model to use (default is "gpt-3.5-turbo")
    :return: The response from GPT
    """
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(model=model,
    messages=[
        {"role": "user", "content": prompt}
    ])

    return response.choices[0].message.content


def test_query_gpt():
    prompt = "What is the capital of France?"
    response = query_gpt(prompt)
    print(F"Response is: \n\n\n {response}")
    assert isinstance(response, str)
    assert len(response) > 0
    print("Test passed!")





def query_perplexity(prompt, system_message="", model="sonar-pro"):
    """
    Query the Perplexity.ai API with the given prompt.
    
    :param prompt: The input text to send to Perplexity
    :param system_message: Optional system message to set context (default="")
    :param model: The model name to use (default="sonar-pro")
    :return: The response text string
    """
    messages = []
    if system_message:
        messages.append({
            "role": "system",
            "content": system_message
        })
    messages.append({
        "role": "user",
        "content": prompt
    })

    client = OpenAI(api_key=perplexity_api_key, base_url="https://api.perplexity.ai")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content

def test_query_perplexity():
    """
    Basic test function to verify query_perplexity works as expected.
    """
    prompt = "How many stars are in the universe?"
    response = query_perplexity(prompt)
    print("Response from query_perplexity:\n", response)
    assert isinstance(response, str)
    assert len(response) > 0
    print("Test passed!")


if __name__ == "__main__":
    #test_query_gpt()
    test_query_perplexity()