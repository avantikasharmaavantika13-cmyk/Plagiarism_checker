def check_plagiarism(input_text, reference_texts):
    docs = [input_text] + reference_texts
    tfidf = TfidfVectorizer().fit_transform(docs)
    similarity_matrix = cosine_similarity(tfidf[0:1], tfidf[1:])
    max_score = max(similarity_matrix[0])
    return round(max_score * 100, 2)
