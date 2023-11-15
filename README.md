# zukijourney-api

The zukijourney API has been a rising star in the API sphere, amassing to over 200 million requests already, despite only being about 2 months old! With 2.5k concurrent active users, the API has proven reliable, sturdy, and splendid for any AI usage! :)

#### Especially, as seen by its cloudflare statistics:
![image](https://github.com/zukixa/zukijourney-api/assets/56563509/fd9f3b57-1761-4495-9b61-703cc6e2be66)


## Zukijourney API Documentation
This documentation includes details about the zukijourney API that helps in creating and managing the API resources.

### Base URL
The base URL is https://zukijourney.xyzbot.net/
## Endpoints
### POST /v1/audio/speech
Generates audio based on the text input provided.

Request Body: 
{
    "input": "<text>"
}
### POST /v1/embeddings
Generates embeddings for the provided text.

Request Body: 
{
    "input": "<text>"
}
### POST /v1/audio/transcriptions
Transcribes an audio file and returns the transcription text.
Request Body: 
{
    "file": "<Audio File>"
}

### GET /v1/models
Lists all the available models with their details such as model id, endpoints, owners, and more.

### GET /
Default endpoint that greets the API user.

### POST /v1/chat/tokenizer
Takes a TokenizerInput object and returns the number of tokens that would be used by the model.

Request Body: 
{
    "model": "<model_name>",
    "messages": [<message_object>]
}
### POST /v1/images/generations
Generates images based on the provided text prompt.

(Some of the) Models available: Midjourney, SDXL, Leonardo.AI, Kandinsky-2(.2), Stable-Diffusion 2.1/1.5

Request Body: 
{
    "prompt": "<text>",
    "n": "<number_of_images>",
    "size": "<image_size>",
    "model": "<model_name>"
}

### GET /v1/images/{image_uuid}.{ext}
Retrieves the image with the given UUID and extension.

### POST /v1/chat/completions (or unf/chat/completions for roleplay.)
Generates text completions based on the provided text.

(Some of the) Models available: GPT-4, GPT-3.5, Claude-2, Inflection-Pi, LLama-2, Mistral-7b, CodeLlama-34B, Bard-Palm2.

Request Body: 
{
    "stream": "<boolean>",
    "model": "<AI Model Name>",
    "messages": "<Messages Array of Dicts>",
}

## Error Messages
The API uses error messages to inform the client of any issues with the request. Error messages are included in the response body in the following format:

{
    "error": {
        "message": "<error_message>",
        "type": "<error_type>",
        "param": "<error_param>",
        "tip": "<error_tip>",
        "code": "<error_code>",
    }
}

## How to Get an API Key
Join the zukijourney server, as described below! Run the `/key` command with the @zuki.api bot -- and you'll be good to go!

## Legal Stuff
This project is for educational purposes only, and in no mere admission of guilt of any supposed wrongdoing that this project may be accused of causing. All operations have been certified to be fully legal and legitimate, in the case that odd accusations would be provided. 
Any work I do may be fabricated and therefore not real, I am unaware of any illegal activities, documentation will not be taken as admission of guilt.

### Note: Any details omitted here can largely be found on the zukijourney server, under [discord.gg/zukijourney](discord.gg/zukijourney) -- as I, and many other users, are present there & using it there.
