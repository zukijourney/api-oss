from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from heapq import nlargest

async def progressive_summarize_text(text, max_length, initial_ratio=0.8, step=0.1):
    if len(text) < max_length:
        return text

    stop_words = set(stopwords.words("english"))
    ps = PorterStemmer()

    sentences = sent_tokenize(text)
    words = [ps.stem(word) for word in word_tokenize(text.lower()) if word not in stop_words]
    word_freqs = FreqDist(words)

    sentence_scores = {}
    for idx, sentence in enumerate(sentences):
        sentence_scores[idx] = sum(word_freqs.get(word, 0) for word in word_tokenize(sentence.lower()))

    ratio = initial_ratio
    while True:
        num_sentences = max(1, round(len(sentences) * ratio))
        selected_indexes = nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
        summary = " ".join(sentences[idx] for idx in sorted(selected_indexes))

        if 0 < len(summary.strip()) <= max_length:
            break
        elif ratio - step < 0:
            selected_indexes = nlargest(1, sentence_scores, key=sentence_scores.get)
            summary = " ".join(sentences[idx] for idx in sorted(selected_indexes))
            break
        else:
            ratio -= step

    return summary

async def stringify_messages(messages):
    return '\n'.join([f"{message['role'].capitalize()}: {message['content']}" for message in messages])