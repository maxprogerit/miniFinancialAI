def chunk_text(text: str, max_chars: int = 800, overlap_chars: int = 150) -> list[str]:
    """Split text into overlapping, paragraph-aware chunks."""
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
