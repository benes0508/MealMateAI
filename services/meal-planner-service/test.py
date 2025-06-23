from google import genai

client = genai.Client(api_key="AIzaSyA0QF3AVII4K34xLlR93T4I1OyWxdo9Zv0")

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="Explain how AI works in a few words"
)
print(response.text)