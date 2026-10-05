def chunk_text(text: str, max_chars: int = 800, overlap_chars: int = 150) -> list[str]:
    """Split text into overlapping chunks for embedding/retrieval.

    Paragraph-aware: consecutive paragraphs are packed together up to
    max_chars, so related sentences usually stay in one chunk. A paragraph
    longer than max_chars on its own is hard-split. Each chunk after the
    first starts with a bit of overlap from the end of the previous one,
    so context near a chunk boundary isn't lost to retrieval.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    packed: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > max_chars:
            packed.append(current)
            current = current[-overlap_chars:] + "\n\n" + paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph

    if current:
        packed.append(current)

    chunks: list[str] = []
    for chunk in packed:
        if len(chunk) <= max_chars:
            chunks.append(chunk)
            continue

        start = 0
        while start < len(chunk):
            end = start + max_chars
            chunks.append(chunk[start:end])
            start = end - overlap_chars

    return chunks
