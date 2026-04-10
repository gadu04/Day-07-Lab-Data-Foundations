from __future__ import annotations

import math
import re
from pathlib import Path


HEADING_PATTERN = re.compile(r"^\s{0,3}(#{1,6})\s+(\S.*)$")
LIST_PATTERN = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+\S")
TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$")
FENCE_PATTERN = re.compile(r"^\s{0,3}(```|~~~)")


class DocumentStructureChunker:
    """
    Split Markdown/HTML documents by structural blocks.

    The chunker keeps headings as section context and preserves tables,
    lists, fenced code blocks, and HTML-like blocks as atomic units when
    possible. Oversized blocks fall back to recursive splitting.
    """

    def __init__(self, chunk_size: int = 1200, include_heading_context: bool = True) -> None:
        self.chunk_size = max(1, chunk_size)
        self.include_heading_context = include_heading_context

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        blocks = self._parse_blocks(text)
        if not blocks:
            return []

        chunks: list[str] = []
        heading_stack: list[str] = []
        current_blocks: list[str] = []
        current_length = 0

        def heading_context() -> str:
            return "\n".join(heading_stack)

        def flush_current() -> None:
            nonlocal current_blocks, current_length
            if not current_blocks:
                return

            body = "\n\n".join(current_blocks).strip()
            if not body:
                current_blocks = []
                current_length = 0
                return

            if self.include_heading_context and heading_stack:
                context = heading_context()
                chunk_text = f"{context}\n\n{body}".strip()
            else:
                chunk_text = body

            if chunk_text:
                chunks.append(chunk_text)
            current_blocks = []
            current_length = 0

        def append_fragment(fragment: str) -> None:
            nonlocal current_blocks, current_length
            fragment = fragment.strip()
            if not fragment:
                return

            if not current_blocks:
                current_blocks = [fragment]
                current_length = len(fragment)
                return

            candidate_length = current_length + 2 + len(fragment)
            if candidate_length <= self.chunk_size:
                current_blocks.append(fragment)
                current_length = candidate_length
                return

            flush_current()
            current_blocks = [fragment]
            current_length = len(fragment)

        for block_type, block_text in blocks:
            if block_type == "heading":
                flush_current()
                heading_stack = self._update_heading_stack(heading_stack, block_text)
                continue

            fragments = self._split_oversized_block(block_type, block_text)
            for fragment in fragments:
                append_fragment(fragment)

        flush_current()
        return chunks

    def _update_heading_stack(self, heading_stack: list[str], heading_text: str) -> list[str]:
        match = HEADING_PATTERN.match(heading_text)
        if not match:
            return heading_stack

        level = len(match.group(1))
        heading_line = heading_text.strip()
        trimmed_stack = heading_stack[: max(0, level - 1)]
        trimmed_stack.append(heading_line)
        return trimmed_stack

    def _split_oversized_block(self, block_type: str, block_text: str) -> list[str]:
        if len(block_text) <= self.chunk_size:
            return [block_text.strip()]

        if block_type in {"table", "list", "html", "code"}:
            separators = ["\n\n", "\n", " ", ""]
        else:
            separators = ["\n\n", "\n", ". ", " ", ""]

        return RecursiveChunker(separators=separators, chunk_size=self.chunk_size).chunk(block_text)

    def _parse_blocks(self, text: str) -> list[tuple[str, str]]:
        lines = text.splitlines()
        blocks: list[tuple[str, str]] = []
        current_lines: list[str] = []
        index = 0

        def flush_paragraph() -> None:
            nonlocal current_lines
            if not current_lines:
                return
            paragraph = "\n".join(current_lines).strip()
            if paragraph:
                blocks.append(("paragraph", paragraph))
            current_lines = []

        while index < len(lines):
            line = lines[index]
            stripped = line.strip()

            if not stripped:
                flush_paragraph()
                index += 1
                continue

            if HEADING_PATTERN.match(line):
                flush_paragraph()
                blocks.append(("heading", line.strip()))
                index += 1
                continue

            fence_match = FENCE_PATTERN.match(line)
            if fence_match:
                flush_paragraph()
                fence_marker = fence_match.group(1)
                fence_lines = [line]
                index += 1
                while index < len(lines):
                    fence_line = lines[index]
                    fence_lines.append(fence_line)
                    index += 1
                    if fence_line.strip().startswith(fence_marker):
                        break
                blocks.append(("code", "\n".join(fence_lines).strip()))
                continue

            if self._looks_like_table_row(line):
                flush_paragraph()
                table_lines = [line]
                index += 1
                while index < len(lines) and self._looks_like_table_row(lines[index]):
                    table_lines.append(lines[index])
                    index += 1
                blocks.append(("table", "\n".join(table_lines).strip()))
                continue

            if LIST_PATTERN.match(line):
                flush_paragraph()
                list_lines = [line]
                index += 1
                while index < len(lines):
                    next_line = lines[index]
                    next_stripped = next_line.strip()
                    if not next_stripped:
                        break
                    if LIST_PATTERN.match(next_line):
                        list_lines.append(next_line)
                        index += 1
                        continue
                    if next_line.startswith((" ", "\t")):
                        list_lines.append(next_line)
                        index += 1
                        continue
                    break
                blocks.append(("list", "\n".join(list_lines).strip()))
                continue

            if line.lstrip().startswith("<") and line.rstrip().endswith(">"):
                flush_paragraph()
                html_lines = [line]
                index += 1
                while index < len(lines):
                    next_line = lines[index]
                    next_stripped = next_line.strip()
                    if not next_stripped:
                        break
                    if next_stripped.startswith("<") or next_line.startswith((" ", "\t")):
                        html_lines.append(next_line)
                        index += 1
                        continue
                    break
                blocks.append(("html", "\n".join(html_lines).strip()))
                continue

            current_lines.append(line)
            index += 1

        flush_paragraph()
        return blocks

    def _looks_like_table_row(self, line: str) -> bool:
        stripped = line.strip()
        if "|" not in stripped:
            return False
        return bool(TABLE_SEPARATOR_PATTERN.match(stripped) or stripped.startswith("|") or stripped.endswith("|"))


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text.strip()) if sentence.strip()]
        if not sentences:
            return []

        chunks: list[str] = []
        for start in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = " ".join(sentences[start : start + self.max_sentences_per_chunk]).strip()
            if chunk:
                chunks.append(chunk)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        return self._split(text, list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        current_text = current_text.strip()
        if not current_text:
            return []

        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            return [
                current_text[index : index + self.chunk_size].strip()
                for index in range(0, len(current_text), self.chunk_size)
                if current_text[index : index + self.chunk_size].strip()
            ]

        separator = remaining_separators[0]
        if separator == "":
            return [
                current_text[index : index + self.chunk_size].strip()
                for index in range(0, len(current_text), self.chunk_size)
                if current_text[index : index + self.chunk_size].strip()
            ]

        if separator not in current_text:
            return self._split(current_text, remaining_separators[1:])

        pieces = [piece.strip() for piece in current_text.split(separator)]
        pieces = [piece for piece in pieces if piece]
        if not pieces:
            return []

        chunks: list[str] = []
        buffer = ""

        for piece in pieces:
            candidate = piece if not buffer else f"{buffer}{separator}{piece}"
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue

            if buffer:
                chunks.extend(self._split(buffer, remaining_separators[1:]))
                buffer = ""

            if len(piece) <= self.chunk_size:
                buffer = piece
            else:
                chunks.extend(self._split(piece, remaining_separators[1:]))

        if buffer:
            chunks.extend(self._split(buffer, remaining_separators[1:]))

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0

    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0).chunk(text),
            "by_sentences": SentenceChunker().chunk(text),
            "recursive": RecursiveChunker(chunk_size=chunk_size).chunk(text),
        }

        comparison: dict[str, dict[str, object]] = {}
        for strategy_name, chunks in strategies.items():
            count = len(chunks)
            avg_length = (sum(len(chunk) for chunk in chunks) / count) if count else 0.0
            comparison[strategy_name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }
        return comparison


def _run_cli_demo() -> None:
    default_path = Path("data/book.md")
    if default_path.exists():
        text = default_path.read_text(encoding="utf-8")
        source_label = str(default_path)
    else:
        text = (
            "# Demo\n\n"
            "## Intro\n"
            "This is a short fallback sample for chunking.\n\n"
            "- Item one\n"
            "- Item two\n\n"
            "| Col A | Col B |\n"
            "|------|------|\n"
            "| 1 | 2 |"
        )
        source_label = "inline demo text"

    print(f"[chunking.py] Source: {source_label}")

    strategies = {
        "fixed_size": FixedSizeChunker(chunk_size=2200, overlap=200),
        "by_sentences": SentenceChunker(max_sentences_per_chunk=8),
        "recursive": RecursiveChunker(chunk_size=2200),
        "document_structure": DocumentStructureChunker(chunk_size=2200),
    }

    for name, chunker in strategies.items():
        chunks = chunker.chunk(text)
        avg_len = (sum(len(chunk) for chunk in chunks) / len(chunks)) if chunks else 0.0
        print(f"\n[{name}] count={len(chunks)} avg_length={avg_len:.2f}")
        if chunks:
            preview = "\n".join(chunks[0].splitlines()[:5])
            print("Preview of first chunk:")
            print(preview)


if __name__ == "__main__":
    _run_cli_demo()
