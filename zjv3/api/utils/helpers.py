import io
import base64
import random
import string
import asyncio
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from heapq import nlargest
from PIL import Image

background_tasks = set()

def create_background_task(coro):
    task = asyncio.create_task(coro)
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

async def progressive_summarize_text(text, max_length, initial_ratio=0.8, step=0.1):
    if len(text) < max_length:
        return text

    stop_words = set(stopwords.words('english'))
    ps = PorterStemmer()

    sentences = sent_tokenize(text)
    words = [ps.stem(word) for word in word_tokenize(text.lower()) if word not in stop_words]
    word_freqs = FreqDist(words)

    sentence_scores = {idx: sum(word_freqs.get(word, 0) for word in word_tokenize(sentence.lower())) for idx, sentence in enumerate(sentences)}

    ratio = initial_ratio
    while True:
        num_sentences = max(1, round(len(sentences) * ratio))
        selected_indexes = nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
        summary = ' '.join(sentences[idx] for idx in sorted(selected_indexes))

        if 0 < len(summary.strip()) <= max_length or ratio - step < 0:
            break
        else:
            ratio -= step

    return summary

async def stringify_messages(messages):
    return '\n'.join(f"{message['role'].capitalize()}: {message['content']}" for message in messages)

async def generate_random_string(length):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

async def parse_model(model):
    if 'gpt' in model:
        if model == 'gpt-4-0125-preview':
            return 'openai/gpt-4-turbo-preview'
        else:
            return f'openai/{model}'
    elif 'claude' in model:
        if model != 'claude':
            return f'anthropic/{model}'
        else:
            return 'anthropic/claude-v1'
    elif 'mytho' in model:
        return f'gryphe/{model}'
    elif 'mixtral' in model or 'mistral' in model:
        return f'mistralai/{model}'
    elif 'cinematika' in model:
        return f'openrouter/{model}'
    elif 'pplx' in model:
        return f'perplexity/{model}'
    elif 'llama' in model:
        return f'meta-llama/{model}-chat'

def gemini_message_convert(old_messages):
    new_messages = []
    system_encountered = False

    for message in old_messages:
        if message['role'] == 'system':
            new_messages.append({'role': 'user', 'parts': [{'text': message['content']}]} )
            system_encountered = True
        else:
            if system_encountered:
                new_messages.append({'role': 'model', 'parts': [{'text': 'Ok.'}]})
                system_encountered = False
            new_role = 'model' if message['role'] == 'assistant' else message['role']
            new_messages.append({'role': new_role, 'parts': [{'text': message['content']}]} )

    return new_messages

def gemini_vision_parse(messages):
    payload = []

    if isinstance(messages, list) and messages:
        last_message_content = messages[-1].get('content')
        if isinstance(last_message_content, list):
            for content_part in last_message_content:
                if content_part.get('type') == 'text':
                    text_content = content_part.get('text')
                    if text_content:
                        payload.append(text_content)
                elif content_part.get('type') == 'image_url':
                    image_data = content_part.get('image_url', {}).get('url')
                    if image_data.startswith('data:image/jpeg;base64,'):
                        base64_image = image_data.replace('data:image/jpeg;base64,', '')
                        decoded_image = base64.b64decode(base64_image)
                        image = Image.open(io.BytesIO(decoded_image))
                        payload.append(image)

    return payload

async def tokenize(text):
    size = len(text)
    return round(size / 4)

async def decode_base64_image(string):
    image_bytes = base64.b64decode(string.replace("data:image/jpeg;base64,", ""))
    return image_bytes
