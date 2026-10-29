def split_into_chunks(text: str, max_chars: int = 800, overlap: int = 100) -> list[str]:

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + max_chars, len(text))

        if end < len(text):
            cut = text.rfind("\n\n", start, end)
            if cut <= start + overlap:
                cut = text.rfind(" ", start, end)
            if cut > start + overlap:
                end = cut

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = end - overlap
    return chunks
