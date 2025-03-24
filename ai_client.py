from openai import OpenAI


def get_file_contents(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"'{filename}' file not found")


class OpenAIClient:
    def __init__(self):
        self.api_key = get_file_contents('api_key_file')
        self.client = OpenAI(api_key=self.api_key)

    def get_response(self, prompt, model="gpt-4o"):
        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model
        )
        return response.choices[0].message.content.strip()

# openai_client = OpenAIClient()
#
# message = 'Привет как дела?'
#
# user_prompt = message.strip()
#
# response = openai_client.get_response(user_prompt)
#
# print(response)
