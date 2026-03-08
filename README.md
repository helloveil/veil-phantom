# VeilPhantom

Privacy-preserving PII redaction for AI pipelines. Real data never leaves your machine.

```python
from veil_phantom import VeilClient

veil = VeilClient()
result = veil.redact("John Smith sent $5M to john@acme.com")

result.sanitized   # "[PERSON_1] sent [AMOUNT_1] to [EMAIL_1]"
result.rehydrate(ai_response)  # restore originals in AI output
```

## Install

```bash
pip install veil-phantom
```

## What it detects

12 entity types with a 25-label BIO scheme:

| Type | Examples |
|------|----------|
| PERSON | Names (Western, African, Asian, South African) |
| ORG | Companies, institutions, financial firms |
| EMAIL | Standard and spoken format ("john at example dot com") |
| PHONE | International, SA, spoken digit sequences |
| MONEY | USD, ZAR, verbal ("twelve point five million dollars") |
| DATE | Formats, relative, spoken ordinals |
| ADDRESS | Street addresses, locations, URLs/domains |
| GOVID | SSN, SA ID, passport, driver's license |
| BANKACCT | Account numbers, IBAN |
| CARD | Credit/debit card numbers |
| IPADDR | IPv4 addresses |
| CASE | Legal case numbers |

## How it works

7-layer detection pipeline, each layer catching what others miss:

```
Input text
  → Layer 0: Shade V7 NER (PhoneticDeBERTa, 22M params, dual-pass inference)
  → Layer 1: Compound org gazetteers + financial institutions
  → Layer 1.5: Pre-regex critical patterns (IBAN, spoken email)
  → Layer 2: NLP entity detection with POS validation
  → Layer 3: Regex patterns (18 types) + URL/domain filtering
  → Layer 5: Contextual sensitivity (roles, situations, temporal)
  → Tokens: [PERSON_1], [ORG_1], [AMOUNT_1]
  → Send to LLM (PII never leaves your machine)
  → Rehydrate AI response with original values
```

## Powered by Shade V7

**Shade V7** (default): PhoneticDeBERTa with Double Metaphone embeddings, 22M params, 97.12% F1, <50ms inference. Dual-pass inference (phonetic + zero-phonetic) picks the best result. Segment rescue for long transcripts. Auto-downloaded from HuggingFace Hub on first use.

**Shade V5** (fallback): DeBERTa-v3-xsmall, 22M params, 97.6% F1 in-distribution, 97.3% OOD. Used automatically if V7 model is not present.

Full pipeline (all 7 layers): **100% detection** on 24 real meetings (399 entities, 0 leaked).

| Model | Parameters | F1 Score | Notes |
|-------|------------|----------|-------|
| **Shade V7** | 22M | 97.12% | Default, on-device, <50ms, phonetic embeddings |
| **Shade V5** | 22M | 97.6% / 97.3% OOD | Fallback |
| GLiNER | 209M | 98.0% | Cloud API required |
| Kaggle 1st | 1.5B | 97.0% | Ensemble, slow |

## Configuration

```python
from veil_phantom import VeilClient, VeilConfig

# All layers (default)
veil = VeilClient()

# Regex + contextual only (no model download needed)
veil = VeilClient(config=VeilConfig.regex_only())

# Maximum privacy (lower thresholds)
veil = VeilClient(config=VeilConfig.max_privacy())

# Custom whitelist
veil = VeilClient(config=VeilConfig(
    additional_whitelist={"MYCOMPANY", "MYBRAND"},
    additional_compound_orgs={"My Corp Ltd"},
))
```

## LLM Integration

```python
# Token-direct mode (recommended)
result = veil.redact(transcript)
ai_response = your_llm(result.sanitized)  # LLM sees [PERSON_1], [ORG_1]
final = result.rehydrate(ai_response)     # restore original values

# OpenAI wrapper
from veil_phantom.integrations.openai import veil_chat
response = veil_chat(client, messages, veil=veil)

# LangChain
from veil_phantom.integrations.langchain import VeilRunnable
chain = VeilRunnable(veil) | your_chain
```

## Training Data

Shade V7 was trained on 862,000 examples generated from 72 million words:

- Entity-swap augmentation: 8,606 base → 855,046 examples (100x expansion)
- Parakeet ASR corruption for speech-realistic noise
- Contrastive hard negatives for false positive reduction
- Double Metaphone phonetic embeddings for cross-cultural name robustness
- Trained on GTX 1050 Ti (accessible compute)

## License

Apache 2.0
