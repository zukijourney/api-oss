from dataclasses import dataclass, field
from typing import List, Dict, Any, Union, Optional

@dataclass
class ModelPricingInfo:
    price: Union[int, str] = 'per_token'
    multiplier: float = 1.0

    def to_json(self) -> Dict[str, Any]:
        return self.__dict__.copy()

@dataclass
class Model:
    id: str
    object: str = 'model'
    owned_by: str = 'openai'
    endpoint: Union[str, List[str]] = '/v1/chat/completions'
    is_free: bool = True
    is_early_access: bool = False
    pricing: ModelPricingInfo = field(default_factory=ModelPricingInfo)
    voices: List[str] = field(default_factory=list)

    def to_json(self) -> Dict[str, Any]:
        model_dict = self.__dict__.copy()
        model_dict['pricing'] = self.pricing.to_json()

        if not model_dict['voices']:
            del model_dict['voices']

        return model_dict

    @classmethod
    def all_to_json(cls) -> Dict[str, Any]:
        return [model.to_json() for model in ModelRegistry.models.values()]
    
    @classmethod
    def get_model(cls, model_id: str) -> Optional['Model']:
        return next(
            (
                model for model in ModelRegistry.models.values()
                if model.id == model_id
            ),
            None
        )

class ModelRegistryMeta(type):
    def __init__(cls, name: str, bases: tuple, attrs: Dict[str, Any]):
        super().__init__(name, bases, attrs)
        cls.models = {
            value.id: value
            for value in attrs.values()
            if isinstance(value, Model)
        }

class ModelRegistry(metaclass=ModelRegistryMeta):
    gpt_35_turbo = Model(
        id='gpt-3.5-turbo',
        pricing=ModelPricingInfo(multiplier=0.75)
    )
    gpt_4 = Model(
        id='gpt-4',
        pricing=ModelPricingInfo(multiplier=1.25),
        is_free=False
    )
    gpt_4_32k = Model(
        id='gpt-4-32k',
        pricing=ModelPricingInfo(multiplier=10),
        is_free=False
    )
    gpt_4_1106_preview = Model(
        id='gpt-4-1106-preview',
        pricing=ModelPricingInfo(multiplier=1.5),
        is_free=False
    )
    gpt_4_0125_preview = Model(
        id='gpt-4-0125-preview',
        pricing=ModelPricingInfo(multiplier=1.5),
        is_free=False
    )
    gpt_4_turbo = Model(
        id='gpt-4-turbo',
        pricing=ModelPricingInfo(multiplier=1.25),
        is_free=False
    )
    gpt_4o_mini = Model(
        id='gpt-4o-mini',
        pricing=ModelPricingInfo(multiplier=0.75)
    )
    gpt_4o = Model(
        id='gpt-4o',
        pricing=ModelPricingInfo(multiplier=1.15)
    )
    gpt_4o_2024_11_20 = Model(
        id='gpt-4o-2024-11-20',
        pricing=ModelPricingInfo(multiplier=1.15),
        is_free=False
    )
    chatgpt_4o_latest = Model(
        id='chatgpt-4o-latest',
        pricing=ModelPricingInfo(multiplier=1.15),
        is_free=False
    )
    o1_mini = Model(
        id='o1-mini',
        pricing=ModelPricingInfo(multiplier=2.5),
        is_free=False
    )
    o1_preview = Model(
        id='o1-preview',
        pricing=ModelPricingInfo(multiplier=5),
        is_free=False
    )
    o1 = Model(
        id='o1',
        pricing=ModelPricingInfo(multiplier=5),
        is_free=False
    )
    o3_mini = Model(
        id='o3-mini',
        pricing=ModelPricingInfo(multiplier=2),
        is_free=False
    )
    claude_3_haiku = Model(
        id='claude-3-haiku',
        owned_by='anthropic',
        pricing=ModelPricingInfo(multiplier=0.75)
    )
    claude_35_haiku = Model(
        id='claude-3.5-haiku',
        owned_by='anthropic',
        pricing=ModelPricingInfo(multiplier=1.25)
    )
    claude_3_opus = Model(
        id='claude-3-opus',
        owned_by='anthropic',
        pricing=ModelPricingInfo(multiplier=5),
        is_free=False
    )
    claude_35_sonnet = Model(
        id='claude-3.5-sonnet',
        owned_by='anthropic',
        pricing=ModelPricingInfo(multiplier=1.5),
        is_free=False
    )
    claude_35_sonnet_v2 = Model(
        id='claude-3.5-sonnet-v2',
        owned_by='anthropic',
        pricing=ModelPricingInfo(multiplier=1.5),
        is_free=False
    )
    claude_37_sonnet = Model(
        id='claude-3.7-sonnet',
        owned_by='anthropic',
        pricing=ModelPricingInfo(multiplier=1.75),
        is_free=False
    )
    claude_37_sonnet_thinking = Model(
        id='claude-3.7-sonnet-thinking',
        owned_by='anthropic',
        pricing=ModelPricingInfo(multiplier=3.5),
        is_free=False
    )
    gemini_15_pro_latest = Model(
        id='gemini-1.5-pro-latest',
        owned_by='google'
    )
    gemini_15_flash_latest = Model(
        id='gemini-1.5-flash-latest',
        owned_by='google',
        pricing=ModelPricingInfo(multiplier=0.75)
    )
    gemini_exp_1121 = Model(
        id='gemini-exp-1121',
        owned_by='google',
        pricing=ModelPricingInfo(multiplier=1.5)
    )
    gemini_20_flash_exp = Model(
        id='gemini-2.0-flash-exp',
        owned_by='google',
        pricing=ModelPricingInfo(multiplier=1.5)
    )
    gemini_20_flash_thinking_exp_01_21 = Model(
        id='gemini-2.0-flash-thinking-exp-01-21',
        owned_by='google',
        pricing=ModelPricingInfo(multiplier=2)
    )
    learnlm_15_pro_experimental = Model(
        id='learnlm-1.5-pro-experimental',
        owned_by='google',
        pricing=ModelPricingInfo(multiplier=1.5)
    )
    gemini_20_flash = Model(
        id='gemini-2.0-flash',
        owned_by='google',
        pricing=ModelPricingInfo(multiplier=1.5),
        is_free=False
    )
    gemini_20_flash_lite_preview_02_05 = Model(
        id='gemini-2.0-flash-lite-preview-02-05',
        owned_by='google',
        pricing=ModelPricingInfo(multiplier=1.5),
        is_free=False
    )
    gemini_20_pro_exp_02_05 = Model(
        id='gemini-2.0-pro-exp-02-05',
        owned_by='google',
        pricing=ModelPricingInfo(multiplier=1.5),
        is_early_access=True,
        is_free=False
    )
    mistral_nemo = Model(
        id='mistral-nemo',
        owned_by='mistralai',
        pricing=ModelPricingInfo(multiplier=0.5)
    )
    codestral = Model(
        id='codestral',
        owned_by='mistralai',
        pricing=ModelPricingInfo(multiplier=0.5)
    )
    mistral_large = Model(
        id='mistral-large',
        owned_by='mistralai'
    )
    grok_2 = Model(
        id='grok-2-1212',
        owned_by='x-ai'
    )
    grok_2_mini = Model(
        id='grok-2-vision-1212',
        owned_by='x-ai',
        pricing=ModelPricingInfo(multiplier=0.75)
    )
    grok_2_mini2 = Model(
        id='grok-2-larp',
        owned_by='zukijourney',
        pricing=ModelPricingInfo(multiplier=0.75)
    )
    grok_3 = Model(
        id='grok-3',
        owned_by='xai',
        pricing=ModelPricingInfo(multiplier=2.75)
    )
    grok_3_mini = Model(
        id='grok-3-mini',
        owned_by='xai',
        pricing=ModelPricingInfo(multiplier=1.75)
    )
    reka_core = Model(
        id='reka-core',
        owned_by='reka'
    )
    reka_flash = Model(
        id='reka-flash',
        owned_by='reka'
    )
    gemma_2_27b = Model(
        id='gemma-2-27b',
        owned_by='google'
    )
    gemma_2_9b = Model(
        id='gemma-2-9b',
        owned_by='google',
        pricing=ModelPricingInfo(multiplier=0.25)
    )
    llama_31_405b_instruct = Model(
        id='llama-3.1-405b-instruct',
        owned_by='meta'
    )
    thug_shaker_1 = Model(
        id='thug-shaker-1',
        owned_by='zukijourney'
    )
    llama_32_3b_instruct = Model(
        id='llama-3.2-3b-instruct',
        owned_by='meta',
        pricing=ModelPricingInfo(multiplier=0.25)
    )
    llama_32_11b_instruct = Model(
        id='llama-3.2-11b-instruct',
        owned_by='meta',
        pricing=ModelPricingInfo(multiplier=0.35)
    )
    llama_32_90b_instruct = Model(
        id='llama-3.2-90b-instruct',
        owned_by='meta',
        pricing=ModelPricingInfo(multiplier=0.5)
    )
    toppy_7b = Model(
        id='toppy-7b',
        owned_by='undi95',
        pricing=ModelPricingInfo(multiplier=0.5)
    )
    mythomax_l2_13b = Model(
        id='mythomax-l2-13b',
        owned_by='gryphe'
    )
    minimax = Model(
        id='minimax',
        owned_by='moonshot'
    )
    tulu_3_405b_instruct = Model(
        id='tulu-3-405b-instruct',
        owned_by='allenai'
    )
    tulu_3_70b_instruct = Model(
        id='tulu-3-70b-instruct',
        owned_by='allenai',
        pricing=ModelPricingInfo(multiplier=0.25)
    )
    tulu_3_8b_instruct = Model(
        id='tulu-3-8b-instruct',
        owned_by='allenai',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    olmo_2_13b_instruct = Model(
        id='olmo-2-13b-instruct',
        owned_by='allenai',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    amazon_nova_pro = Model(
        id='amazon-nova-pro-v1.0',
        owned_by='amazon',
        pricing=ModelPricingInfo(multiplier=1.75),
        is_free=False
    )
    amazon_nova_lite = Model(
        id='amazon-nova-lite-v1.0',
        owned_by='amazon',
        pricing=ModelPricingInfo(multiplier=1.25)
    )
    amazon_nova_micro = Model(
        id='amazon-nova-micro-v1.0',
        owned_by='amazon',
        pricing=ModelPricingInfo(multiplier=0.75)
    )
    yandexgpt_3_pro = Model(
        id='YandexGPT-3-Pro',
        owned_by='yandex'
    )
    yandexgpt_4_pro = Model(
        id='YandexGPT-4-Pro',
        owned_by='yandex'
    )
    yandexgpt_experimental = Model(
        id='GigaChat-Max-preview',
        owned_by='sberbank'
    )
    gigachat_pro = Model(
        id='GigaChat-Pro',
        owned_by='sberbank'
    )
    gigachat_plus = Model(
        id='GigaChat-Plus',
        owned_by='sberbank'
    )
    gigachat = Model(
        id='GigaChat',
        owned_by='sberbank'
    )
    deepseek_coder_6_7b_base = Model(
        id='deepseek-coder-6.7b-base',
        owned_by='deepseek',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    deepseek_coder_6_7b_instruct = Model(
        id='deepseek-coder-6.7b-instruct',
        owned_by='deepseek',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    deepseek_math_7b_instruct = Model(
        id='deepseek-math-7b-instruct',
        owned_by='deepseek',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    discolm_german_7b_v1 = Model(
        id='discolm-german-7b-v1',
        owned_by='mistralai',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    falcon_7b_instruct = Model(
        id='falcon-7b-instruct',
        owned_by='tiiuae',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    gemma_7b_it = Model(
        id='gemma-7b-it',
        owned_by='google',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    hermes_2_pro_mistral_7b = Model(
        id='hermes-2-pro-mistral-7b',
        owned_by='nous-research',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    llama_2_13b_chat = Model(
        id='llama-2-13b-chat',
        owned_by='meta',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    llama_2_7b_chat = Model(
        id='llama-2-7b-chat',
        owned_by='meta',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    llama_3_8b_instruct = Model(
        id='llama-3-8b-instruct',
        owned_by='meta',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    llama_3_70b_instruct = Model(
        id='llama-3-70b-instruct',
        owned_by='meta',
        pricing=ModelPricingInfo(multiplier=0.45)
    )
    llama_31_8b_instruct = Model(
        id='llama-3.1-8b-instruct',
        owned_by='meta',
        pricing=ModelPricingInfo(multiplier=0.25)
    )
    llamaguard_7b = Model(
        id='llamaguard-7b',
        owned_by='meta',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    mistral_tiny = Model(
        id='mistral-tiny',
        owned_by='mistralai',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    mistral_small = Model(
        id='mistral-small-latest',
        owned_by='mistralai',
        pricing=ModelPricingInfo(multiplier=0.25)
    )
    neural_chat_7b_v3_1 = Model(
        id='neural-chat-7b-v3-1',
        owned_by='intel',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    openchat_35_0106 = Model(
        id='openchat-3.5-0106',
        owned_by='openchat',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    openhermes_25_mistral_7b = Model(
        id='openhermes-2.5-mistral-7b',
        owned_by='teknium',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    phi_2 = Model(
        id='phi-2',
        owned_by='microsoft',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    phi_4 = Model(
        id='phi-4',
        owned_by='microsoft',
        pricing=ModelPricingInfo(multiplier=0.45),
    )
    qwen15_05b_chat = Model(
        id='qwen1.5-0.5b-chat',
        owned_by='alibaba',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    qwen15_18b_chat = Model(
        id='qwen1.5-1.8b-chat',
        owned_by='alibaba',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    qwen15_7b_chat = Model(
        id='qwen1.5-7b-chat',
        owned_by='alibaba',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    qwen15_14b_chat = Model(
        id='qwen1.5-14b-chat',
        owned_by='alibaba',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    qwen25_72b_instruct = Model(
        id='qwen2.5-72b-instruct',
        owned_by='alibaba'
    )
    qwen25_coder_32b_instruct = Model(
        id='qwen2.5-coder-32b-instruct',
        owned_by='alibaba'
    )
    deepseek_r1_distill_qwen_32b = Model(
        id='deepseek-r1-distill-qwen-32b',
        owned_by='deepseek'
    )
    qwq_32b_preview = Model(
        id='qwq-32b-preview',
        owned_by='alibaba',
        pricing=ModelPricingInfo(multiplier=1)
    )
    sqlcoder_7b_2 = Model(
        id='sqlcoder-7b-2',
        owned_by='defog',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    starling_lm_7b_beta = Model(
        id='starling-lm-7b-beta',
        owned_by='berkeley-nest',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    tinyllama_11b_chat_v10 = Model(
        id='tinyllama-1.1b-chat-v1.0',
        owned_by='tinyllama',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    zephyr_7b_beta = Model(
        id='zephyr-7b-beta',
        owned_by='hugging-face',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    llama_32_1b_instruct = Model(
        id='llama-3.2-1b-instruct',
        owned_by='meta',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    llama_31_70b_instruct = Model(
        id='llama-3.1-70b-instruct',
        owned_by='meta',
        pricing=ModelPricingInfo(multiplier=0.45)
    )
    llama_33_70b_instruct = Model(
        id='llama-3.3-70b-instruct',
        owned_by='meta'
    )
    llama_31_nemotron_70b_instruct = Model(
        id='llama-3.1-nemotron-70b-instruct',
        owned_by='nvidia'
    )
    wizardlm_2_8x22b = Model(
        id='WizardLM-2-8x22B',
        owned_by='microsoft'
    )
    euryale_70b = Model(
        id='euryale-70b',
        owned_by='meta'
    )
    deepseek_chat = Model(
        id='deepseek-chat',
        owned_by='deepseek'
    )
    deepseek_reasoner = Model(
        id='deepseek-reasoner',
        owned_by='deepseek',
        pricing=ModelPricingInfo(multiplier=1.5)
    )
    rogue_rose_103b_v0_2 = Model(
        id='rogue-rose-103b-v0.2',
        owned_by='openrouter',
        pricing=ModelPricingInfo(multiplier=0.15)
    )
    noromaid_20b = Model(
        id='noromaid-20b',
        owned_by='neversleep'
    )
    caramelldansen_1 = Model(
        id='caramelldansen-1',
        owned_by='zukijourney'
    )
    caramelldansen_1_plus = Model(
        id='caramelldansen-1-plus',
        owned_by='zukijourney'
    )
    zukigm_1 = Model(
        id='zukigm-1',
        owned_by='zukijourney',
        pricing=ModelPricingInfo(multiplier=0.25)
    )
    r11776 = Model(
        id='r1-1776',
        owned_by='perplexity'
    )
    sonar = Model(
        id='sonar',
        owned_by='perplexity'
    )
    sonar_pro = Model(
        id='sonar-pro',
        owned_by='perplexity',
        pricing=ModelPricingInfo(multiplier=1.5)
    )
    sonar_reasoning = Model(
        id='sonar-reasoning',
        pricing=ModelPricingInfo(multiplier=1.25),
        is_free=False,
        owned_by='perplexity'
    )
    sonar_reasoning_pro = Model(
        id='sonar-reasoning-pro',
        pricing=ModelPricingInfo(multiplier=1.75),
        is_free=False,
        owned_by='perplexity'
    )
    aion_1_rp = Model(
        id='aion-1-rp',
        owned_by='aion-labs',
        pricing=ModelPricingInfo(multiplier=0.50)
    )
    aion_1 = Model(
        id='aion-1',
        owned_by='aion-labs',
        pricing=ModelPricingInfo(multiplier=0.75)
    )
    aion_1_mini = Model(
        id='aion-1-mini',
        owned_by='aion-labs',
        pricing=ModelPricingInfo(multiplier=0.50)
    )
    dall_e_3 = Model(
        id='dall-e-3',
        pricing=ModelPricingInfo(price=500),
        endpoint='/v1/images/generations',
        is_free=False
    )
    flux_schnell = Model(
        id='flux-schnell',
        pricing=ModelPricingInfo(price=100),
        owned_by='black-forest-labs',
        endpoint='/v1/images/generations'
    )
    flux_dev = Model(
        id='flux-dev',
        pricing=ModelPricingInfo(price=250),
        owned_by='black-forest-labs',
        endpoint='/v1/images/generations'
    )
    flux_pro = Model(
        id='flux-pro',
        pricing=ModelPricingInfo(price=500),
        owned_by='black-forest-labs',
        endpoint='/v1/images/generations'
    )
    flux_11_pro = Model(
        id='flux-1.1-pro',
        pricing=ModelPricingInfo(price=2500),
        owned_by='black-forest-labs',
        endpoint='/v1/images/generations',
        is_free=False
    )
    flux_11_pro_ultra = Model(
        id='flux-1.1-pro-ultra',
        pricing=ModelPricingInfo(price=6000),
        owned_by='black-forest-labs',
        endpoint='/v1/images/generations',
        is_free=False
    )
    flux_11_pro_ultra_raw = Model(
        id='flux-1.1-pro-ultra-raw',
        pricing=ModelPricingInfo(price=7500),
        owned_by='black-forest-labs',
        endpoint='/v1/images/generations',
        is_free=False
    )
    grok2aur = Model(
        id='grok-2a',
        pricing=ModelPricingInfo(price=750),
        owned_by='xai',
        endpoint='/v1/images/generations'
    )
    pollinations = Model(
        id='pollinations',
        pricing=ModelPricingInfo(price=25),
        owned_by='pollinationsai',
        endpoint='/v1/images/generations'
    )
    playground_v25 = Model(
        id='playground-v2.5',
        pricing=ModelPricingInfo(price=100),
        owned_by='playgroundai',
        endpoint='/v1/images/generations'
    )
    playground_v3 = Model(
        id='playground-v3',
        pricing=ModelPricingInfo(price=200),
        owned_by='playgroundai',
        endpoint='/v1/images/generations'
    )
    stable_diffusion_3_medium = Model(
        id='stable-diffusion-3-medium',
        pricing=ModelPricingInfo(price=100),
        owned_by='stability-ai',
        endpoint='/v1/images/generations'
    )
    stable_diffusion_35_large = Model(
        id='stable-diffusion-3.5-large',
        pricing=ModelPricingInfo(price=2000),
        owned_by='stability-ai',
        endpoint='/v1/images/generations',
        is_free=False
    )
    stable_diffusion_35_large_turbo = Model(
        id='stable-diffusion-3.5-large-turbo',
        pricing=ModelPricingInfo(price=750),
        owned_by='stability-ai',
        endpoint='/v1/images/generations'
    )
    stable_image_core = Model(
        id='stable-image-core',
        pricing=ModelPricingInfo(price=650),
        owned_by='stability-ai',
        endpoint='/v1/images/generations'
    )
    stable_image_ultra = Model(
        id='stable-image-ultra',
        pricing=ModelPricingInfo(price=2500),
        owned_by='stability-ai',
        endpoint='/v1/images/generations',
        is_free=False
    )
    tts_1 = Model(
        id='tts-1',
        pricing=ModelPricingInfo(price=200),
        endpoint='/v1/audio/speech',
        voices=['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
    )
    tts_1_hd = Model(
        id='tts-1-hd',
        pricing=ModelPricingInfo(price=200),
        endpoint='/v1/audio/speech',
        is_free=False,
        voices=['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
    )
    elevenlabs = Model(
        id='elevenlabs',
        pricing=ModelPricingInfo(price=200),
        endpoint='/v1/audio/speech',
        owned_by='elevenlabs',
        is_free=False,
        voices=[
            'charlie',
            'george',
            'callum',
            'liam',
            'charlotte',
            'alice',
            'matilda',
            'chris',
            'brian',
            'daniel',
            'lily',
            'bill'
        ]
    )
    elevenlabs_flash = Model(
        id='elevenlabs-flash',
        pricing=ModelPricingInfo(price=300),
        endpoint='/v1/audio/speech',
        owned_by='elevenlabs',
        is_free=False,
        voices=[
            'charlie',
            'george',
            'callum',
            'liam',
            'charlotte',
            'alice',
            'matilda',
            'chris',
            'brian',
            'daniel',
            'lily',
            'bill'
        ]
    )
    speechify = Model(
        id='speechify',
        pricing=ModelPricingInfo(price=200),
        endpoint='/v1/audio/speech',
        owned_by='speechify',
        is_free=False,
        voices=[
            'henry',
            'bwyneth',
            'snoop',
            'mrbeast',
            'gwyneth',
            'cliff',
            'guy',
            'jane',
            'matthew',
            'benwilson',
            'henry',
            'bwyneth',
            'snoop',
            'mrbeast',
            'gwyneth',
            'benwilson',
            'cliff',
            'presidential',
            'guy',
            'jane',
            'matthew',
            'carly',
            'kyle',
            'kristy',
            'oliver',
            'tasha',
            'joe',
            'lisa',
            'george',
            'emily',
            'rob',
            'russell',
            'benjamin',
            'jenny',
            'aria',
            'joanna',
            'nate',
            'mary',
            'salli',
            'joey',
            'ryan',
            'sonia',
            'oliver',
            'amy',
            'michael',
            'thomas',
            'libby',
            'narrator',
            'brian',
            'natasha',
            'william',
            'freya',
            'ken',
            'olivia',
            'aditi',
            'abeo',
            'ezinne',
            'luke',
            'leah',
            'willem',
            'adri',
            'fatima',
            'hamdan',
            'hala',
            'rana',
            'bassel',
            'bashkar',
            'tanishaa',
            'kalina',
            'borislav',
            'joana',
            'enric',
            'xiaoxiao',
            'yunfeng',
            'xiaomeng',
            'yunjian',
            'xiaoyan',
            'yunze',
            'zhiyu',
            'hiumaan',
            'wanlung',
            'hiujin',
            'hsiaochen',
            'hsiaoyu',
            'yunjhe',
            'srecko',
            'gabrijela',
            'antonin',
            'vlasta',
            'christel',
            'jeppe',
            'colette',
            'maarten',
            'laura',
            'ruben',
            'dena',
            'arnaud',
            'anu',
            'kert',
            'blessica',
            'angelo',
            'harri',
            'selma',
            'denise',
            'henri',
            'celeste',
            'claude',
            'sylvie',
            'jean',
            'charline',
            'gerard',
            'ariane',
            'fabrice',
            'katja',
            'christoph',
            'louisa',
            'conrad',
            'vicki',
            'daniel',
            'giorgi',
            'eka',
            'athina',
            'nestoras',
            'avri',
            'hila',
            'madhur',
            'swara',
            'noemi',
            'tamas',
            'gudrun',
            'gunnar',
            'gadis',
            'ardi',
            'irma',
            'benigno',
            'elsa',
            'gianni',
            'palmira',
            'diego',
            'imelda',
            'cataldo',
            'bianca',
            'adriano',
            'mayu',
            'naoki',
            'nanami',
            'daichi',
            'shiori',
            'keita',
            'daulet',
            'aigul',
            'sunhi',
            'injoon',
            'jimin',
            'bongjin',
            'seoyeon',
            'ona',
            'leonas',
            'everita',
            'nils',
            'osman',
            'yasmin',
            'sagar',
            'hemkala',
            'iselin',
            'finn',
            'pernille',
            'farid',
            'dilara',
            'agnieszka',
            'marek',
            'zofia',
            'brenda',
            'donato',
            'yara',
            'fabio',
            'leila',
            'julio',
            'camila',
            'thiago',
            'fernanda',
            'duarte',
            'ines',
            'cristiano',
            'alina',
            'emil',
            'dariya',
            'dmitry',
            'tatyana',
            'maxim',
            'viktoria',
            'lukas',
            'petra',
            'rok',
            'sameera',
            'thilini',
            'saul',
            'vera',
            'arnau',
            'triana',
            'gerardo',
            'carlota',
            'luciano',
            'larissa',
            'lupe',
            'hillevi',
            'sofie',
            'rehema',
            'daudi',
            'pallavi',
            'valluvar',
            'saranya',
            'kumar',
            'kani',
            'surya',
            'venba',
            'anbu',
            'mohan',
            'shruti',
            'premwadee',
            'niwat',
            'emel',
            'ahmet',
            'gul',
            'salman',
            'uzma',
            'asad',
            'polina',
            'ostap',
            'hoaimy',
            'namminh',
            'orla',
            'colm'
        ]
    )
    whisper_1 = Model(
        id='whisper-1',
        pricing=ModelPricingInfo(price=100),
        endpoint=['/v1/audio/transcriptions', '/v1/audio/translations']
    )
    translate = Model(
        id='google-translate',
        pricing=ModelPricingInfo(price=10),
        owned_by='google',
        endpoint='/v1/text/translations'
    )
    upscale = Model(
        id='upscale',
        pricing=ModelPricingInfo(price=100),
        endpoint='/v1/images/upscale'
    )
    moderations = Model(
        id='omni-moderation-latest',
        pricing=ModelPricingInfo(price=100),
        endpoint='/v1/moderations'
    )
    text_embedding_3_large = Model(
        id='text-embedding-3-large',
        pricing=ModelPricingInfo(price=100),
        endpoint='/v1/embeddings'
    )
    text_embedding_3_small = Model(
        id='text-embedding-3-small',
        pricing=ModelPricingInfo(price=100),
        endpoint='/v1/embeddings'
    )