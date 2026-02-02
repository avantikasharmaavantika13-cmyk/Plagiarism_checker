def detect_ai_text_chunks(text):
    sentences = text.split('.')
    ai_scores = []
    for sentence in sentences:
        if sentence.strip():
            ai_score = random.uniform(0.3, 0.9)
            ai_scores.append((sentence.strip(), round(ai_score * 100, 2)))
    return ai_scores
