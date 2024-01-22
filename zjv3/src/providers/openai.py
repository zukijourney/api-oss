import openai
import json

options = json.load(open('data/config.json', 'r'))
client = openai.AsyncOpenAI(api_key=options['openai_key'])

async def ai(body: dict):
    try:
        body.pop("stream", None)
        body.pop("streaming", None)
        
        messages, model, temperature, frequency_penalty, presence_penalty, top_p = body['messages'], body['model'], body.get("frequency_penalty", 0), body.get("presence_penalty", None), body.get("temperature", 1), body.get("top_p", 1)
        
        gen = await client.chat.completions.create(messages=messages, model=model, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty, temperature=temperature, top_p=top_p)
        
        return gen.choices[0].message.content
    except:
        return None