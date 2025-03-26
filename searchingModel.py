from google import genai
from pprint import pprint
API_KEY = "your_api_key"

# Create a client
client = genai.Client(api_key=API_KEY)
        
# embeddings = client.models.embed_content(
#             model="models/text-embedding-004", 
#             contents=["H"])
# print("Length of embedding vector: ", len(embeddings.embeddings[0].values))
# print("Embedding vector: ", embeddings.embeddings[0].values)

# for model in client.models.list():
#     for action in model.supported_actions:
#         if action == "generateContent":
#             print(model.name, model.display_name, model.description)


#  This is a faster way to generate content rather then using 'generate_content_stream'. 
chunk = client.models.generate_content(model='gemini-2.0-flash-001', contents='Tell me a story in 100 words.')
print(chunk.candidates[0].content.parts[0].text)

