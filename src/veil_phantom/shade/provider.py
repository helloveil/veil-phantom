"""
VeilPhantom — Shade NER provider using ONNX Runtime.
Supports Shade V7 (PhoneticDeBERTa, 22M params, 97.12% F1) and
Shade V5 (DeBERTa-v3-xsmall, 22M params, 97.6% F1) as fallback.

V7 adds Double Metaphone phonetic embeddings for cross-cultural name detection.
Same 25 BIO labels across 12 entity types.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

logger = logging.getLogger("veil_phantom")


@dataclass
class ShadeEntity:
    """A detected entity from Shade NER."""
    type: str
    value: str
    confidence: float


# ── Double Metaphone (inline implementation) ──

# Phonetic vocabulary matching production ShadeService.swift
_PHON_CHARS = "0AFHJKLMNPRSTX "
_PHON_PAD_IDX = 0
_PHON_UNK_IDX = 1
_MAX_PHON_LEN = 6
_PHON_VOCAB: dict[str, int] = {c: i + 2 for i, c in enumerate(_PHON_CHARS)}


def _double_metaphone(word: str) -> str:
    """Simplified Double Metaphone producing primary code.
    Returns uppercase phonetic code (subset of '0AFHJKLMNPRSTX ').
    """
    if not word:
        return ""

    w = word.upper()
    # Strip non-alpha
    w = "".join(c for c in w if c.isalpha())
    if not w:
        return ""

    code = []
    i = 0
    length = len(w)

    # Skip initial silent letters
    if w[:2] in ("GN", "KN", "PN", "AE", "WR"):
        i = 1

    while i < length and len(code) < 8:
        c = w[i]

        if c in "AEIOU":
            if i == 0:
                code.append("A")
            i += 1
        elif c == "B":
            code.append("P")
            i += 2 if i + 1 < length and w[i + 1] == "B" else 1
        elif c == "C":
            if i + 1 < length and w[i + 1] == "H":
                code.append("X")
                i += 2
            elif i + 1 < length and w[i + 1] in "EIY":
                code.append("S")
                i += 2
            else:
                code.append("K")
                i += 1
        elif c == "D":
            if i + 1 < length and w[i + 1] == "G" and i + 2 < length and w[i + 2] in "EIY":
                code.append("J")
                i += 3
            else:
                code.append("T")
                i += 1
        elif c == "F":
            code.append("F")
            i += 2 if i + 1 < length and w[i + 1] == "F" else 1
        elif c == "G":
            if i + 1 < length and w[i + 1] == "H":
                if i + 2 < length and w[i + 2] not in "AEIOU":
                    i += 2
                else:
                    code.append("K")
                    i += 2
            elif i + 1 < length and w[i + 1] == "N":
                i += 2
            elif i > 0 and w[i - 1] in "AEIOU" and i + 1 < length and w[i + 1] in "AEIOU":
                code.append("J")
                i += 1
            else:
                code.append("K")
                i += 2 if i + 1 < length and w[i + 1] == "G" else 1
        elif c == "H":
            if i + 1 < length and w[i + 1] in "AEIOU" and (i == 0 or w[i - 1] not in "AEIOU"):
                code.append("H")
            i += 1
        elif c == "J":
            code.append("J")
            i += 1
        elif c == "K":
            code.append("K")
            i += 2 if i > 0 and w[i - 1] == "C" else 1
        elif c == "L":
            code.append("L")
            i += 2 if i + 1 < length and w[i + 1] == "L" else 1
        elif c == "M":
            code.append("M")
            i += 2 if i + 1 < length and w[i + 1] == "M" else 1
        elif c == "N":
            code.append("N")
            i += 2 if i + 1 < length and w[i + 1] == "N" else 1
        elif c == "P":
            if i + 1 < length and w[i + 1] == "H":
                code.append("F")
                i += 2
            else:
                code.append("P")
                i += 1
        elif c == "Q":
            code.append("K")
            i += 1
        elif c == "R":
            code.append("R")
            i += 2 if i + 1 < length and w[i + 1] == "R" else 1
        elif c == "S":
            if i + 1 < length and w[i + 1] == "H":
                code.append("X")
                i += 2
            elif i + 2 < length and w[i:i + 3] in ("SIO", "SIA"):
                code.append("X")
                i += 3
            else:
                code.append("S")
                i += 2 if i + 1 < length and w[i + 1] == "S" else 1
        elif c == "T":
            if i + 1 < length and w[i + 1] == "H":
                code.append("0")  # theta
                i += 2
            elif i + 2 < length and w[i:i + 3] in ("TIO", "TIA"):
                code.append("X")
                i += 3
            else:
                code.append("T")
                i += 2 if i + 1 < length and w[i + 1] == "T" else 1
        elif c == "V":
            code.append("F")
            i += 1
        elif c == "W":
            if i + 1 < length and w[i + 1] in "AEIOU":
                code.append("A")
            i += 1
        elif c == "X":
            code.append("K")
            code.append("S")
            i += 1
        elif c == "Y":
            if i + 1 < length and w[i + 1] in "AEIOU":
                code.append("A")
            i += 1
        elif c == "Z":
            code.append("S")
            i += 1
        else:
            i += 1

    return "".join(code)


def _word_to_phon_ids(word: str) -> list[int]:
    """Convert a word to phonetic IDs using Double Metaphone.
    Returns list of length _MAX_PHON_LEN padded with PAD tokens.
    """
    code = _double_metaphone(word)[:_MAX_PHON_LEN]
    ids = [_PHON_VOCAB.get(c, _PHON_UNK_IDX) for c in code.upper()]
    while len(ids) < _MAX_PHON_LEN:
        ids.append(_PHON_PAD_IDX)
    return ids


# ── Edit Distance for Person Name Normalization ──

def _edit_distance(a: str, b: str) -> int:
    """Standard Levenshtein edit distance."""
    a_lower, b_lower = a.lower(), b.lower()
    la, lb = len(a_lower), len(b_lower)
    dp = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        dp[i][0] = i
    for j in range(lb + 1):
        dp[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a_lower[i - 1] == b_lower[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[la][lb]


_CAP_WORD_RE = re.compile(r"\b[A-Z][a-zA-Z'-]{2,}\b")
_BAD_NAME_PREFIXES = {"I", "I'm", "Oh", "And", "But", "So", "Well", "Yes", "No", "Uh", "Um", "The", "A"}


def _extract_capitalized_words(text: str) -> list[str]:
    """Extract unique capitalized words from text."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _CAP_WORD_RE.finditer(text):
        w = m.group()
        if w.lower() not in seen:
            seen.add(w.lower())
            out.append(w)
    return out


def _normalize_shade_person(value: str, text: str) -> str:
    """Normalize Shade-detected person name against capitalized words in text."""
    normalized = re.sub(r"[.,;:!?]+$", "", value.strip())
    if not normalized:
        return normalized

    caps = _extract_capitalized_words(text)
    tokens = normalized.split()

    mapped = []
    for token in tokens:
        # Try exact match first
        exact = next((w for w in caps if w.lower() == token.lower()), None)
        if exact:
            mapped.append(exact)
            continue
        # Edit distance matching
        best_word, best_dist = None, 999
        for w in caps:
            dist = _edit_distance(token, w)
            if dist < best_dist:
                best_dist = dist
                best_word = w
        if best_word and (best_dist <= 2 or (len(token) >= 4 and best_word.lower().startswith(token.lower()))):
            mapped.append(best_word)
        else:
            mapped.append(token)

    normalized = " ".join(mapped)

    # Expand single-word surname to full name
    if len(mapped) == 1:
        escaped = re.escape(mapped[0])
        pat = re.compile(r"\b([A-Z][a-zA-Z'-]{2,})\s+" + escaped + r"\b")
        m = pat.search(text)
        if m and m.group(1) not in _BAD_NAME_PREFIXES:
            normalized = f"{m.group(1)} {mapped[0]}"

    return normalized


class ShadeNERProvider:
    """On-device PII detection using the Shade ONNX model.

    Loads Shade V7 by default (ShadeV7.onnx). Falls back to V5
    (ShadeV5.onnx) if V7 is not found in the model directory.
    Both versions share the same ONNX interface and 25 BIO labels.

    V7 uses PhoneticDeBERTa with Double Metaphone embeddings for
    improved cross-cultural name detection.
    """

    def __init__(self, model_dir: str | Path, max_length: int = 256):
        self.model_dir = Path(model_dir)
        self.max_length = max_length
        self._session = None
        self._tokenizer = None
        self._id2label: dict[int, str] = {}
        self._loaded = False
        self._model_version: str | None = None
        self._has_phonetic_input = False

    @property
    def model_version(self) -> str | None:
        """Return the loaded model version ("v7" or "v5"), or None if not loaded."""
        return self._model_version

    def _load(self) -> None:
        if self._loaded:
            return

        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer
        except ImportError as e:
            raise ImportError(
                f"Missing dependency for Shade: {e}. "
                "Install with: pip install onnxruntime tokenizers"
            )

        # Try V7 first, fall back to V5
        model_path_v7 = self.model_dir / "ShadeV7.onnx"
        model_path_v5 = self.model_dir / "ShadeV5.onnx"

        if model_path_v7.exists():
            model_path = model_path_v7
            self._model_version = "v7"
        elif model_path_v5.exists():
            model_path = model_path_v5
            self._model_version = "v5"
        else:
            raise FileNotFoundError(
                f"No Shade ONNX model found in {self.model_dir}. "
                "Expected ShadeV7.onnx or ShadeV5.onnx."
            )

        tokenizer_path = self.model_dir / "tokenizer.json"
        # V7 uses label_map.json, V5 uses shade_label_map.json
        label_map_path = self.model_dir / "label_map.json"
        if not label_map_path.exists():
            label_map_path = self.model_dir / "shade_label_map.json"

        # Load label map
        with open(label_map_path) as f:
            raw = json.load(f)
            self._id2label = {int(k): v for k, v in raw.get("id2label", raw).items()}

        # Load tokenizer
        self._tokenizer = Tokenizer.from_file(str(tokenizer_path))

        # Load ONNX session
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.intra_op_num_threads = 2
        self._session = ort.InferenceSession(str(model_path), opts)

        # Check if model accepts phonetic_ids input
        input_names = {inp.name for inp in self._session.get_inputs()}
        self._has_phonetic_input = "phonetic_ids" in input_names

        self._loaded = True
        logger.info(
            "Shade %s loaded from %s (phonetic=%s)",
            self._model_version.upper(),
            self.model_dir,
            self._has_phonetic_input,
        )

    def predict(self, text: str) -> list[ShadeEntity]:
        """Run Shade NER on text with dual-pass and segment rescue."""
        if not text or not text.strip():
            return []

        self._load()

        encoding = self._tokenizer.encode(text)
        input_ids = encoding.ids
        attention_mask = [1] * len(input_ids)

        # Ensure CLS/SEP tokens
        if input_ids and input_ids[0] != 1:
            input_ids = [1] + input_ids
            attention_mask = [1] + attention_mask
        if input_ids and input_ids[-1] != 2:
            input_ids = input_ids + [2]
            attention_mask = attention_mask + [1]

        # Dual-layout chunking: try two chunk sizes, pick best
        threshold = min(self.max_length, 96)
        if len(input_ids) <= threshold:
            entities = self._run_best_inference(input_ids, text)
        else:
            core_tokens = input_ids[1:-1]  # strip CLS/SEP for chunking
            layout_a = self._run_chunked_layout(core_tokens, text, chunk_size=min(self.max_length - 2, 126))
            layout_b = self._run_chunked_layout(core_tokens, text, chunk_size=min(self.max_length - 2, 96))
            entities = layout_b if len(layout_b) > len(layout_a) else layout_a
            if len(layout_a) != len(layout_b):
                logger.debug(
                    "Dual-layout: 126→%d, 96→%d entities (selected %s)",
                    len(layout_a), len(layout_b),
                    96 if len(layout_b) > len(layout_a) else 126,
                )

        # Segment rescue: re-run on sentence segments if low detection on long text
        word_count = len(text.split())
        if word_count > 300 and len(entities) < 2:
            rescued = self._predict_by_segments(text)
            if len(rescued) > len(entities):
                logger.info("Segment rescue: %d → %d entities", len(entities), len(rescued))
                entities = rescued

        # Normalize person names
        normalized = []
        for ent in entities:
            if ent.type == "PERSON":
                new_value = _normalize_shade_person(ent.value, text)
                if new_value and new_value != ent.value:
                    ent = ShadeEntity(type=ent.type, value=new_value, confidence=ent.confidence)
            normalized.append(ent)

        return self._deduplicate(normalized)

    def _run_best_inference(self, input_ids: list[int], text: str) -> list[ShadeEntity]:
        """Dual-pass inference: run with phonetics and without, pick best.

        Selection uses confidence gating: zero-phonetic pass is only chosen
        if it finds MORE entities AND its average confidence exceeds 0.75.
        This prevents the zero pass from winning with low-quality detections.
        """
        if not self._has_phonetic_input:
            return self._infer_chunk(input_ids, [1] * len(input_ids))

        # Pass 1: with phonetic codes
        phon_entities = self._infer_chunk(input_ids, [1] * len(input_ids), use_zero_phonetics=False)
        # Pass 2: with zero phonetics
        zero_entities = self._infer_chunk(input_ids, [1] * len(input_ids), use_zero_phonetics=True)

        # Confidence-gated selection: zero pass wins only if more entities AND high confidence
        if len(zero_entities) > len(phon_entities):
            avg_conf = sum(e.confidence for e in zero_entities) / len(zero_entities) if zero_entities else 0
            if avg_conf > 0.75:
                logger.debug("Dual-pass: phonetic=%d, zero=%d (avg_conf=%.2f) → selected zero",
                             len(phon_entities), len(zero_entities), avg_conf)
                return zero_entities
            else:
                logger.debug("Dual-pass: zero has more (%d vs %d) but low confidence (%.2f) → keeping phonetic",
                             len(zero_entities), len(phon_entities), avg_conf)
        return phon_entities

    def _run_chunked_layout(self, core_tokens: list[int], text: str, chunk_size: int) -> list[ShadeEntity]:
        """Run chunked inference with given chunk size."""
        all_entities: list[ShadeEntity] = []
        stride = chunk_size - 32

        pos = 0
        while pos < len(core_tokens):
            end = min(pos + chunk_size, len(core_tokens))
            chunk = [1] + core_tokens[pos:end] + [2]  # re-add CLS/SEP
            entities = self._run_best_inference(chunk, text)
            all_entities.extend(entities)
            if end >= len(core_tokens):
                break
            pos += stride

        return self._deduplicate(all_entities)

    def _predict_by_segments(self, text: str) -> list[ShadeEntity]:
        """Segment rescue: split text into ~70-word segments, run each separately."""
        sentences = re.split(r'[.!?]+\s+', text)
        segments: list[str] = []
        current: list[str] = []
        current_words = 0

        for sent in sentences:
            words = sent.split()
            if current_words + len(words) > 70 and current:
                segments.append(" ".join(current))
                current = [sent]
                current_words = len(words)
            else:
                current.append(sent)
                current_words += len(words)
        if current:
            segments.append(" ".join(current))

        all_entities: list[ShadeEntity] = []
        for segment in segments:
            if not segment.strip():
                continue
            encoding = self._tokenizer.encode(segment)
            ids = encoding.ids
            if ids and ids[0] != 1:
                ids = [1] + ids
            if ids and ids[-1] != 2:
                ids = ids + [2]
            entities = self._run_best_inference(ids, segment)
            all_entities.extend(entities)

        return self._deduplicate(all_entities)

    def _build_phonetic_ids(self, input_ids: list[int], use_zero: bool) -> np.ndarray:
        """Build phonetic_ids tensor for ONNX input."""
        seq_len = len(input_ids)
        if use_zero:
            return np.zeros((1, seq_len, _MAX_PHON_LEN), dtype=np.int64)

        phon_ids = []
        for tok_id in input_ids:
            # Decode single token to get the word
            word = self._tokenizer.decode([tok_id], skip_special_tokens=True).strip()
            if word and word[0].isalpha():
                phon_ids.append(_word_to_phon_ids(word))
            else:
                phon_ids.append([_PHON_PAD_IDX] * _MAX_PHON_LEN)

        return np.array([phon_ids], dtype=np.int64)

    def _infer_chunk(
        self,
        input_ids: list[int],
        attention_mask: list[int],
        use_zero_phonetics: bool = True,
    ) -> list[ShadeEntity]:
        """Run inference on a single chunk."""
        if not input_ids:
            return []

        seq_len = len(input_ids)

        ids_array = np.array([input_ids], dtype=np.int64)
        mask_array = np.array([attention_mask[:seq_len]], dtype=np.int64)

        feed = {"input_ids": ids_array, "attention_mask": mask_array}

        # Add phonetic_ids if model supports it
        if self._has_phonetic_input:
            feed["phonetic_ids"] = self._build_phonetic_ids(input_ids, use_zero_phonetics)

        outputs = self._session.run(["logits"], feed)
        logits = outputs[0][0]  # [seq_len, num_labels]

        # Softmax + argmax
        exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
        probs = exp_logits / exp_logits.sum(axis=-1, keepdims=True)

        predictions = []
        for i in range(seq_len):
            label_idx = int(np.argmax(probs[i]))
            confidence = float(probs[i][label_idx])
            label = self._id2label.get(label_idx, "O")
            predictions.append((label, confidence))

        return self._bio_to_entities(input_ids, predictions)

    def _flush_entity(
        self,
        entity_type: str,
        token_ids: list[int],
        confs: list[float],
    ) -> ShadeEntity | None:
        """Flush accumulated BIO tokens into a ShadeEntity.

        Applies minimum confidence filter and comma/semicolon prefix stripping.
        Returns None if the entity should be rejected.
        """
        text = self._decode_tokens(token_ids).strip()
        if not text:
            return None

        avg_confidence = sum(confs) / len(confs)

        # Minimum confidence filter — reject low-quality detections
        if avg_confidence < 0.5:
            return None

        # Strip leading comma/semicolon/colon (ASR artifacts)
        text = re.sub(r"^[,;:]+\s*", "", text)
        if not text:
            return None

        return ShadeEntity(type=entity_type, value=text, confidence=avg_confidence)

    def _bio_to_entities(
        self, input_ids: list[int], predictions: list[tuple[str, float]]
    ) -> list[ShadeEntity]:
        """Convert BIO predictions to entity spans with word-level aggregation."""
        entities: list[ShadeEntity] = []
        current_type: str | None = None
        current_tokens: list[int] = []
        current_confs: list[float] = []

        for i, (label, conf) in enumerate(predictions):
            if label.startswith("B-"):
                # Flush previous
                if current_type and current_tokens:
                    ent = self._flush_entity(current_type, current_tokens, current_confs)
                    if ent:
                        entities.append(ent)
                current_type = label[2:]
                current_tokens = [input_ids[i]]
                current_confs = [conf]
            elif label.startswith("I-") and current_type == label[2:]:
                current_tokens.append(input_ids[i])
                current_confs.append(conf)
            else:
                # Flush
                if current_type and current_tokens:
                    ent = self._flush_entity(current_type, current_tokens, current_confs)
                    if ent:
                        entities.append(ent)
                current_type = None
                current_tokens = []
                current_confs = []

        # Final flush
        if current_type and current_tokens:
            ent = self._flush_entity(current_type, current_tokens, current_confs)
            if ent:
                entities.append(ent)

        return entities

    def _decode_tokens(self, token_ids: list[int]) -> str:
        return self._tokenizer.decode(token_ids, skip_special_tokens=True)

    @staticmethod
    def _deduplicate(entities: list[ShadeEntity]) -> list[ShadeEntity]:
        seen: dict[str, ShadeEntity] = {}
        for ent in entities:
            # Strip trailing punctuation before dedup
            clean_value = re.sub(r"[.,;:!?]+$", "", ent.value)
            key = f"{ent.type}:{clean_value.lower()}"
            if key not in seen or ent.confidence > seen[key].confidence:
                if clean_value != ent.value:
                    ent = ShadeEntity(type=ent.type, value=clean_value, confidence=ent.confidence)
                seen[key] = ent
        return list(seen.values())
