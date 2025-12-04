from google import genai
from pprint import pprint

# Create a client
client = genai.Client(api_key="your_api_key")

for m in client.models.list():
  if 'embedContent' in m.supported_actions:
    print(m.name, m.display_name, m.description, m.model_dump_json(), "\n")

# for model in client.models.list():
#     for action in model.supported_actions:
#         if action == "generateContent":
#             print(model.name, model.display_name, model.description)


# #  This is a faster way to generate content rather then using 'generate_content_stream'. 
# model_output = ""
# for next_text in client.models.generate_content_stream(model='gemini-2.5-flash-lite', 
#                                                             contents='Tell me a story in 100 words.'):
#     model_output += next_text.text

# print(model_output)