# Phantom Fairness: Eliminating AI Discrimination Through Pre-Inference Identity Abstraction

## Authors
Nakai Williams, Veil Research

## Abstract

We present **Phantom Fairness** — a novel approach to eliminating AI discrimination by stripping protected attributes before inference, making bias architecturally impossible rather than statistically mitigated. The approach is powered by **Shade**, a family of on-device NER models (22M parameters) that detect and replace personally identifiable information in real-time with sub-50ms latency. We detail the progressive training methodology across three model generations (V5→V6→V7) that achieves 97.6% F1 while introducing several novel techniques: targeted data generation for OOD gap closure, synthetic ASR-noisy transcript generation at negligible cost ($2.30 for 8,486 meetings), name mangling as a training signal for ASR robustness, entity swap augmentation for 100x data expansion, phonetic embeddings for spelling-variant awareness, and contrastive hard negative training. We demonstrate that a 22M-parameter domain-specific model matches or exceeds models 10–70x its size (GLiNER 209M, Presidio 300M, Kaggle 1st place 1.5B) while running entirely on-device — resolving the fundamental contradiction of cloud-based PII detection.

---

## 1. Introduction

### 1.1 The Discrimination Problem

AI systems discriminate. Not because they're programmed to, but because they're trained on human data that encodes centuries of bias. A hiring model trained on historical decisions learns that "female-sounding" names correlate with rejection. A loan model learns that certain zip codes correlate with default. A medical triage model learns that certain ethnicities receive less aggressive treatment.

Current approaches to AI fairness fall into three categories:
1. **Pre-processing**: Modify training data to remove bias (data augmentation, resampling)
2. **In-processing**: Constrain the model during training (adversarial debiasing, fairness regularization)
3. **Post-processing**: Adjust outputs to meet fairness criteria (equalized odds, demographic parity)

All three are reactive. They attempt to counteract bias that the model has already absorbed. They require defining protected groups, measuring disparate impact, and making trade-offs between fairness metrics that are mathematically incompatible (Chouldechova, 2017; Kleinberg et al., 2016).

We propose a fourth approach: **don't let the AI see the protected attributes in the first place.**

### 1.2 The Core Insight

Phantom Fairness is based on a simple observation: **you cannot discriminate based on information you never received.**

If an AI system processes text where every name is "Alex Chen," every address is "42 Maple Street, Springfield," every date of birth is "January 15, 1990," and every government ID follows a neutral format — it literally cannot infer race, gender, age, nationality, or socioeconomic status. The decision must be based on merit, content, and substance alone.

This is not a theoretical proposal. We have a working implementation: Veil's VeilPhantom pipeline, powered by Shade, an on-device NER model that detects and replaces 12 categories of personally identifiable information in real-time, with sub-50ms latency on consumer hardware.

### 1.3 The Contradiction in Cloud PII Detection

Most PII detection services (Microsoft Presidio, AWS Comprehend, Google DLP) require sending text to a cloud API. This is a fundamental contradiction: **to protect your sensitive data, you must first send it to a third party.** Shade resolves this by running entirely on-device. Real PII never leaves the user's machine. The AI API only ever receives phantom text.

---

## 2. Background & Related Work

### 2.1 AI Fairness

- **Disparate impact**: Systems that produce different outcomes for different demographic groups, even without explicit demographic features (Barocas & Selbst, 2016)
- **Proxy discrimination**: Models learn to infer protected attributes from proxies — zip codes encode race, names encode gender, writing style encodes education level (Datta et al., 2015)
- **Fairness impossibility theorems**: It is mathematically impossible to simultaneously satisfy multiple fairness criteria (calibration, equalized odds, demographic parity) except in degenerate cases (Chouldechova, 2017)
- **Blindness approaches**: Previous work on "fairness through unawareness" failed because models reconstruct protected attributes from proxies. Our approach is fundamentally different: we replace ALL identifying information, including proxies, with consistent phantom values

### 2.2 PII Detection

| Model | Parameters | F1 | Latency | On-Device | Approach |
|-------|-----------|-----|---------|-----------|----------|
| **Shade V7** | **22M** | **97.12%** | **<50ms** | **Yes** | BIO token classification + phonetic embeddings |
| **Shade V7 + pipeline** | **22M + NLP** | **100%*** | **<50ms** | **Yes** | 5-layer (NER + NLP + Regex + Gazetteer + Semantic) |
| Shade V5 | 22M | 97.6% | <50ms | Yes | BIO token classification |
| GLiNER | 209M | 98.0% | ~200ms | No | Zero-shot span extraction |
| Kaggle 1st | 1.5B | 97.0% | ~2s | No | Ensemble |
| Presidio | 300M | ~90% | ~150ms | No | Rule + ML hybrid |
| Protecto | 400M | — | — | No | Enterprise API |
| Roblox | 300M | — | — | No | Large-scale production |

*100% on 24 real-world meeting transcripts (399 entities, 0 leaked). Individual V7 NER achieves 97.12% F1.

Key distinction: existing PII detection is built for privacy compliance (GDPR, HIPAA). We repurpose it for fairness — a novel application.

---

## 3. Phantom Fairness

### 3.1 Architecture

```
Input Text → Shade NER (on-device) → Tokenize [PERSON_1], [ADDRESS_1], [DATE_1]...
    → Phantom Substitution (neutral values) → AI Inference (cloud) → Reverse Phantom → Rehydrate
```

**Critical property**: The AI system only ever sees phantom text. It cannot discriminate because discriminatory signals have been replaced with neutral constants.

### 3.2 What Gets Replaced

| Entity Type | Discriminatory Signal | Phantom Value |
|-------------|----------------------|---------------|
| PERSON | Race, gender, ethnicity (inferred from name) | Gender-neutral, ethnicity-neutral name |
| ADDRESS | Socioeconomic status, race (zip code redlining) | Neutral suburban address |
| DATE | Age discrimination | Standardized phantom date |
| GOVID | Nationality, immigration status | Format-neutral phantom ID |
| PHONE | Geographic region, carrier (socioeconomic proxy) | Neutral phantom number |
| EMAIL | Name-based discrimination, employer prestige | Generic phantom email |
| ORG | Educational prestige, employer bias | Neutral phantom organization |
| MONEY | Salary history bias (now illegal in many jurisdictions) | Context-dependent |
| BANKACCT | Financial profiling | Neutral phantom account |
| CARD | Financial profiling | Neutral phantom number |
| IPADDR | Geographic location | Neutral phantom IP |
| CASE | Legal history | Neutral phantom case number |

### 3.3 Why This Differs from "Fairness Through Unawareness"

Previous "blind" approaches simply removed protected attributes from model input (e.g., don't include race as a feature). This fails because models reconstruct protected attributes from proxies.

Phantom Fairness is fundamentally different:
1. **Comprehensive replacement**: We replace ALL identifying information, not just explicit protected attributes. Names, addresses, organizations, dates, IDs — every proxy signal is neutralized.
2. **Consistent substitution**: Phantom values are semantically coherent. "Alex Chen" is a realistic name. "42 Maple Street" is a realistic address. The AI can still reason about the content — it just can't discriminate based on identity.
3. **Reversible**: After inference, phantom values are replaced with originals. The human decision-maker sees real names. Only the AI was blind.
4. **On-device**: PII detection runs locally. Real identities never leave the device.

### 3.4 Token-Direct vs Phantom Substitution

During development of Veil's meeting summarization pipeline, we discovered an important distinction:

- **Phantom substitution** (replacing PII with fake values): Best for fairness applications where the AI must produce natural-sounding output about anonymized subjects
- **Token-direct** (sending `[PERSON_1]`, `[ORG_1]` placeholders): Better for summarization quality, as the AI can reason about the structure without being confused by phantom identities

For Phantom Fairness, phantom substitution is essential — the AI must not know that abstraction has occurred. For privacy-focused summarization, token-direct produces superior results. This insight — that the optimal abstraction strategy depends on the downstream task — is itself a contribution.

### 3.5 Threat Model

**What Phantom Fairness protects against:**
- Name-based discrimination in hiring, lending, insurance
- Zip code redlining in automated decisions
- Age discrimination in employment and insurance
- Nationality bias in immigration and financial services
- Gender bias in healthcare, hiring, lending

**What it does NOT protect against:**
- Bias encoded in content itself (e.g., "maternity leave" on a resume still carries signal)
- Structural bias in training data (underrepresentation isn't fixed by phantom substitution)
- Human bias after rehydration (the human reviewer still sees real names)
- Semantic identity leakage ("my church group" implies religion, "my husband" implies gender)

### 3.6 Applications

1. **AI-Assisted Hiring**: Phantom resumes ensure AI scores qualifications, not identity
2. **Loan/Credit Decisions**: Phantom applications prevent redlining
3. **Medical Triage**: Phantom patient records prevent racial bias in care
4. **Legal Document Review**: Phantom parties prevent bias in legal AI
5. **Insurance Underwriting**: Risk assessment without demographic profiling
6. **Meeting Summarization** (Veil's current use): AI summaries that don't leak participant identities to cloud providers

---

## 4. Shade: Progressive Training for On-Device PII Detection

### 4.1 Architecture

- **Base**: DeBERTa-v3-xsmall (6 layers, 384 hidden dim, 22M parameters)
- **Task head**: BIO token classification (25 labels: O + B-/I- for 12 entity types)
- **Inference**: Single forward pass, O(n) complexity, 256-token sliding window with 32-token overlap
- **Runtime**: ONNX Runtime (Windows), CoreML (macOS)
- **Latency**: <50ms per chunk on consumer hardware (GTX 1050 Ti / Apple M1)

We chose BIO token classification over span extraction (O(n²)) because real-time meeting transcription requires sub-50ms inference per chunk. The linear complexity of BIO enables processing live audio streams without perceptible delay.

### 4.2 Shade V5: The Clean Foundation

**Training data**: 117,872 examples (train) / 13,098 (validation)

| Source | Count | Purpose |
|--------|-------|---------|
| Base BIO-converted | 88,532 | Core entity coverage across 12 types |
| Diverse augmentation | 18,000 | Conversational patterns, format variants, edge cases |
| Targeted V3 | 2,070 | Specific weak-type remediation |

**Training configuration**:
- Effective batch size: 32 (batch 8 × gradient accumulation 4)
- Learning rate: 5e-5, cosine scheduler, 10% warmup
- FP16 mixed precision
- Early stopping: patience 3, 10 max epochs
- Hardware: GTX 1050 Ti (4GB VRAM)
- Wall time: 21.3 hours

**Results**:

| Entity Type | F1 (In-Dist) | F1 (OOD) |
|-------------|:---:|:---:|
| EMAIL | 100% | 100% |
| CARD | 100% | 92.3% |
| IPADDR | 100% | 100% |
| PHONE | 98.4% | 100% |
| MONEY | 99.6% | 100% |
| DATE | 97.8% | 95.8% |
| ADDRESS | 99.4% | 88.4% |
| GOVID | 97.7% | 100% |
| PERSON | 96.3% | 97.7% |
| ORG | 97.6% | 97.7% |
| CASE | 97.8% | 94.7% |
| BANKACCT | 92.9% | 94.4% |
| **Overall** | **97.6%** | **97.3%** |

**OOD gap: 0.3%** — achieved through targeted data generation (Section 4.5).

### 4.3 Shade V6: Domain Adaptation via Synthetic ASR Data

**The problem**: V5 was trained on clean synthetic text but must process real ASR (Automatic Speech Recognition) output, which contains name mangling, missing punctuation, filler words, and speaker tags.

**The solution**: Generate realistic noisy meeting transcripts using an LLM, then fine-tune V5 on this noisy data.

**Synthetic data generation**:
- **Generator**: Gemini 2.5 Flash Lite
- **Cost**: $2.30 for 8,486 realistic meeting transcripts
- **Parse rate**: 94.2% (7,994 successfully parsed)
- **Final training set**: 8,606 chunks (train), 957 chunks (validation)

Each generated transcript includes:
- `[MM:SS] SPEAKER_S1:` prefixed utterances
- 20–50% punctuation removal
- Filler words ("um", "uh", "like") in 5–15% of utterances
- False starts and repeated words
- **Name mangling**: Same person spelled 2–3 different ways (98% of meetings)
- Inline XML entity annotations with entity links table

**Domain coverage** (7 domains, ~430 meetings each):
Corporate, Legal, Medical, Software Development, Sales, Financial Services, Education

**Training**: Fine-tuned from V5 checkpoint, ~5 epochs

**Results**:
- Validation F1: 93.33% (on noisy ASR data)
- Clean data F1: maintained ~97%
- Real meeting entity detection: **108 entities** (vs 26 with V5 hybrid) — **4.2x improvement**

### 4.4 Shade V7: Augmentation, Phonetics, and Contrastive Learning

V7 introduces three novel techniques to push detection on real meetings further:

#### 4.4.1 Entity Swap Augmentation (100x Data Expansion)

Take 8,606 V6 training examples and generate 500K–1M variants by swapping entities with type-coherent alternatives:

- Entity databases: 10K+ person names (multi-ethnic), 2K+ organizations, 1K+ locations
- For each example: identify entity spans, generate 50–100 variants
- **Critical**: Adjust BIO labels when replacement span length changes
  - "Kai" (B-PERSON) → "Van der Merwe" (B-PERSON I-PERSON I-PERSON I-PERSON)
- Cost: $0 (pure computation, no API calls)

This teaches the model that entity *position and context* matter more than entity *surface form* — a key generalization principle.

#### 4.4.2 Phonetic Embeddings (32-dim Channel)

ASR systems produce phonetically plausible but orthographically incorrect name variants ("Bronwyn" → "Bronan", "Aoife" → "Aofa"). Standard token embeddings treat these as completely different words.

We add a 32-dimensional phonetic channel:
- Compute Double Metaphone codes for each token
- Phonetic vocabulary: 16 characters (0AFHJKLMNPRSTX) + PAD, UNK
- Embed to 32-dim per code, mean-pool across 6-character max length
- Concatenate with DeBERTa's 384-dim embedding → project (384+32) → 384

This teaches the model that "Bronwyn" and "Bronan" share a phonetic signature and are likely the same entity type, even though their token embeddings are distant.

#### 4.4.3 Contrastive Hard Negative Training

The same surface form can be an entity in one context and a common word in another:
- "Grant approved the budget" → Grant = B-PERSON
- "We need to grant access" → grant = O
- "Rose presented the findings" → Rose = B-PERSON
- "The stock rose sharply" → rose = O

We generate ~7K contrastive pairs where the same word appears as both entity and non-entity. Combined with explicit hard negatives for common false positives ("website", "boxing", "sage", "rocket"), this trains precise contextual disambiguation.

**V7 Training data mix**:

| Source | Proportion | Count |
|--------|-----------|-------|
| Clean V5 data | 50% | ~250K |
| Entity swap augmented | 35% | ~175K |
| Hard negatives | 10% | ~50K |
| Contrastive pairs | 5% | ~25K |

**V7 Results** (trained on GTX 1050 Ti, 47,500 steps):

| Metric | Target | Achieved |
|--------|--------|----------|
| Clean benchmark F1 | ≥ 96% | **97.12%** ✅ |
| Real meeting detections | ≥ 50% of NLP baseline | **143 entities** (vs 26 with V5 hybrid) — **5.5x** ✅ |
| Prod pipeline match rate | — | **17.5%** (60/342 prod entities independently found) |
| Unique finds (entities NLP missed) | — | **92 entities** (primarily ORGs: Google, Uber, BigQuery, Shopify) |
| Pattern type regressions | 0 | **0** ✅ |
| Inference latency | <50ms | **<50ms** ✅ |

**Full pipeline audit** (V7 + NLP + Regex + Gazetteer + Semantic + Context):
- **399 PII entities** detected across 24 real meetings
- **0 entities leaked** — 100% catch rate
- V7 contributes unique ORG detections that no other layer catches

### 4.5 Innovation: Targeted Data Generation for OOD Gap Closure

The most impactful single technique in our training pipeline. After V5 base training showed weaknesses on specific entity types, we generated 2,070 targeted examples:

| Target | Count | Technique |
|--------|-------|-----------|
| CASE citations | 200 | Full legal citation patterns: "Smith v. Jones (2023)", compound defendants |
| ADDRESS | 500 | Combined street+city as single entity, standalone cities in varied contexts |
| PHONE vs IPADDR | 300 | SA spelled-out numbers, (0XX) format disambiguation |
| PERSON (diverse) | 400 | Arabic names, SA legal titles, phonetic ASR variants |
| GOVID vs CARD | 170 | SSN format "XXX-XX-XXXX" type disambiguation |
| BANKACCT | 200 | Bank name + account number confusion patterns |
| DATE (relative) | 200 | "Next Thursday", "six months from now", "Q3" |

This reduced the OOD gap from ~2% to 0.3% with just 2,070 additional examples — demonstrating that **targeted, failure-aware data generation massively outperforms random augmentation**.

### 4.6 Innovation: Name Mangling as Training Signal

Real-world ASR (specifically Parakeet TDT v2) produces consistent patterns of name corruption:
- Uncommon names are phonetically approximated: "Bronwyn" → "Bronan", "Aoife" → "Aofa"
- Name boundaries shift: "Nakai Williams" → "Nakai William's" or "The Kai Williams"
- Capitalization is inconsistent

Rather than treating these as noise to be filtered, we use them as **training signal**. V6's synthetic data generator produces 2–3 spelling variants per person per meeting, with an entity links table that maps all variants to a canonical form:

```
- E1: ["bronwyn", "bronan", "bronwynn"] | type: PERSON | canonical: "Bronwyn"
- E4: ["james", "james peterson", "jim"] | type: PERSON | canonical: "James Peterson"
```

This teaches the model that PII detection must be robust to orthographic variation — a critical requirement for real-world deployment that clean-data-only training misses entirely.

---

## 5. Training Economics

A key contribution is demonstrating that competitive PII detection is achievable with minimal resources:

| | V5 | V6 | V7 |
|-|----|----|-----|
| **Training data** | 116K synthetic | 8,606 ASR-noisy | ~500K augmented |
| **API cost** | $0 | $2.30 | $0 |
| **Hardware** | GTX 1050 Ti (4GB) | GTX 1050 Ti (4GB) | GTX 1050 Ti (4GB) |
| **Wall time** | 21.3 hours | ~5 hours | ~18 hours (47,500 steps) |
| **Model size** | 270MB | 270MB | 270MB |
| **F1** | 97.6% | 93.3% (noisy) | 97.12% |
| **Inference** | <50ms | <50ms | <50ms |

Total cost to develop a competitive PII detection system: **under $5 in API costs** and consumer-grade hardware. This democratizes PII detection — and by extension, Phantom Fairness — for any organization, not just those with cloud AI budgets.

---

## 6. Discussion

### 6.1 Implications for Regulation

The EU AI Act (2024) requires "high-risk" AI systems to demonstrate non-discrimination. Current compliance requires:
1. Collecting demographic data to measure disparate impact
2. Regular fairness audits
3. Documentation of bias mitigation efforts

Phantom Fairness offers a simpler compliance path: **prove that the AI system never receives demographic information.** If the input is phantomized, discrimination is architecturally impossible, and compliance becomes a technical guarantee rather than a statistical argument.

### 6.2 Implications for Agentic Infrastructure

The AI industry is rapidly moving toward agentic systems — autonomous agents that manage calendars, draft emails, search personal files, negotiate on behalf of users, and orchestrate multi-step workflows across applications. These agents require deep access to a user's digital life: contacts, financial records, medical history, legal documents, communication history, and location data.

This creates a catastrophic attack surface. A compromised agent — whether through prompt injection, supply chain attack, jailbreak, or API key theft — becomes an oracle for the attacker. Every piece of personal data the agent can access is exfiltrable. Today's security model assumes we can keep agents from being compromised. History suggests we cannot.

**Phantom Fairness reframes the problem.** If an agent operates on phantomized data, a compromise leaks only phantom values. The attacker extracts "Alex Chen" (phantom) instead of the user's real name, "42 Maple Street, Springfield" instead of their real address, "January 15, 1990" instead of their real date of birth. The leaked data is structurally valid but referentially useless — it points to no real person.

This is the **Shade SDK** proposition: any application or agent that processes text through Shade's on-device NER pipeline before storing or transmitting it gains **breach resilience by default**. The agent still functions correctly — it can schedule meetings, summarize documents, and answer questions about the user's data — because phantom values are semantically coherent. But an attacker who exfiltrates the agent's context window, memory store, or API logs gets nothing actionable.

Key properties of phantomized agent infrastructure:

1. **Zero-value exfiltration**: Stolen phantom data cannot be linked to real individuals. There is no lookup table on a server — rehydration happens on-device only.
2. **Prompt injection resilience**: Even if an attacker injects prompts that cause the agent to dump its context, the dumped context contains only phantom values.
3. **Supply chain safety**: A malicious dependency that silently exfiltrates processed text only captures phantom text.
4. **Regulatory safe harbor**: Data breach notification requirements (GDPR Article 34, POPIA Section 22) may not apply if the breached data contains no real personal information.
5. **Defense in depth**: Phantom substitution complements (not replaces) authentication, encryption, and access control. It is the last line of defense — when all other security fails, the data itself is worthless.

As agents become more capable and more deeply integrated into personal and enterprise workflows, the question shifts from "how do we prevent agents from being compromised?" to "how do we ensure a compromise is inconsequential?" Phantom Fairness, powered by on-device NER, provides an answer.

### 6.3 The VeilPhantom SDK

The techniques described in this paper — on-device NER, phantom substitution, token-direct processing, and rehydration — are released as **VeilPhantom**: an open-source Python SDK that any application can integrate to gain PII-aware data processing. Available at `pip install veil-phantom` and [github.com/helloveil/veil-phantom](https://github.com/helloveil/veil-phantom).

#### Architecture: 7-Layer Detection Pipeline

VeilPhantom runs a multi-layer detection pipeline, where each layer catches what others miss:

```
VeilPhantom Pipeline
├── Layer 0:   Shade V7 NER       → PhoneticDeBERTa, dual-pass inference
├── Layer 1:   Compound Gazetteers → Financial institutions, known organizations
├── Layer 1.5: Pre-NLP Patterns   → IBAN, spoken email (must precede NLP)
├── Layer 2:   NLP Detection      → POS-validated entity recognition
├── Layer 3:   Regex Patterns     → 18 pattern types + URL/domain filtering
├── Layer 3.5: URL Detection      → Safe-domain filtering (skip google.com, etc.)
└── Layer 5:   Contextual         → Roles, situations, temporal sensitivity
```

**Layer 0: Shade V7 NER** (on-device inference)

The core detection layer. Shade V7's PhoneticDeBERTa encoder detects 12 PII entity types using dual-pass inference — running once with Double Metaphone phonetic embeddings and once without, selecting the result that detects more entities. This handles transcripts where phonetics help (name variants) and where they don't (multilingual text). Segment rescue re-runs on sentence-level segments when long transcripts yield suspiciously low detection counts. Person name normalization uses edit-distance matching to expand surname-only detections to full names.

```
User text → Shade V7 (dual-pass) → Token Map + Tokenized Text → [AI API] → Rehydrate → Display
```

**Layer 2: NLP Entity Detection** (lightweight POS validation)

Capitalized word sequences are evaluated as potential entities using part-of-speech heuristics. The layer rejects false positives — contractions, speaker diarization tags, determiners, gerunds, and generic org phrases — while catching multi-word names and organizations that the NER model may have missed.

**Layers 1–3.5: Pattern Matching** (zero-latency)

Compiled regex patterns detect 18 PII formats including spoken forms ("twelve point five million dollars", "nine two zero one zero one five eight zero zero zero eight eight"), credit cards, IBANs, government IDs, and URLs with safe-domain filtering. These layers require no model inference and run in microseconds.

**Layer 5: Contextual Sensitivity**

Detects sensitive situations (pending acquisitions, whistleblower reports, insider information), identifying roles (CEO, CFO, Attorney General), and temporal sensitivity markers (before public announcement, during blackout period). Only triggers in genuinely sensitive contexts — not every mention of "CEO" is redacted, only those adjacent to sensitive situations.

#### Full Pipeline Result: 100% Detection

On 24 real meetings containing 399 PII entities across all 12 types, the full 7-layer pipeline achieved **100% detection with 0 leaked entities**. No single layer achieves this alone — it is the combination of neural detection (Shade V7), linguistic validation (NLP), pattern matching (regex), and contextual awareness that closes every gap.

#### Platform Support

| Platform | Runtime | Model Format | Status |
|----------|---------|-------------|--------|
| macOS | Swift/CoreML + ONNX | .onnx | Production (Veil) |
| Windows | Node.js/onnxruntime-node | .onnx | Production (Veil for Windows) |
| Python | onnxruntime | .onnx | Production (VeilPhantom SDK) |
| Linux | onnxruntime | .onnx | Supported via Python SDK |

At 22M parameters, the Shade V7 model is 88MB in fp32 (44MB quantized). This is small enough to ship embedded in a desktop app, run as a service, or load from disk in under a second.

#### API Surface

```python
from veil_phantom import VeilClient, VeilConfig

veil = VeilClient()  # auto-downloads Shade V7 from HuggingFace

# Redact PII
result = veil.redact("Sarah Chen sent $12.5M to sarah@gs.com")
# result.sanitized = "[PERSON_1] sent [AMOUNT_1] to [EMAIL_1]"

# Send to any AI API — real PII never transmitted
ai_response = your_llm(result.sanitized)

# Restore original values in AI output
final = result.rehydrate(ai_response)

# One-liner wrapper
output = veil.wrap(transcript, llm_fn=your_llm)

# OpenAI integration
from veil_phantom.integrations.openai import veil_chat
response = veil_chat(client, messages, veil=veil)
```

The SDK handles the full pipeline: tokenization, phantom value generation from culturally diverse pools, consistent phantom assignment (same real entity always maps to the same phantom within a session), 18 regex pattern types, contextual sensitivity detection, and bidirectional rehydration.

#### Future: Secret Shield & Injection Shield

The architecture is designed to support two additional shield layers:
- **Secret Shield**: Regex-based credential detection (API keys, JWTs, connection strings) — protecting developer agents from leaking infrastructure secrets
- **Injection Shield**: A lightweight binary classifier sharing the Shade encoder, detecting prompt injection at the infrastructure level before messages reach the agent's model

Since the NER encoder already runs on every message, adding these classifiers is nearly free — a second classification head on a shared encoder, not a second model.

#### Dogfooding: Veil as First Consumer

Veil itself is the first and most demanding consumer of the Shade SDK. Every meeting processed through Veil exercises the full pipeline:

1. **Transcription** (Parakeet ASR) produces raw text with real names, amounts, and identifiers
2. **Shade NER** detects 12 entity types across the transcript
3. **Token-direct processing** sends `[PERSON_1]`, `[ORG_1]` placeholders to the AI API (Gemini)
4. **AI summarization** produces meeting minutes that reference tokens, not real values
5. **Rehydration** restores original values for display in the app

This means every Veil user is implicitly testing the Shade SDK on real-world meeting transcripts — noisy ASR output, overlapping speakers, domain-specific jargon, and regional accents. The pipeline processes ~500-2,000 tokens per meeting, with sub-50ms NER latency. If Shade misses an entity, the user sees a real name slip through into the AI logs. If Shade false-positives, the user sees a common word get redacted. This continuous real-world feedback loop drives model improvements across versions.

The SDK is extracted from the same codebase that powers Veil's production privacy pipeline. It is not a research prototype repackaged for distribution — it is production code that has processed thousands of real meeting transcripts, with the battle scars and edge-case handling that implies.

#### Integration Scenarios

The SDK is designed for any application where text passes through an AI system:

| Scenario | Shields Active | What's Protected |
|----------|---------------|-----------------|
| **AI assistants** | PII + Secret + Injection | User identity, credentials in files, agent hijacking via chat |
| **Customer support bots** | PII + Injection | Customer data, bot manipulation via malicious tickets |
| **HR/recruiting tools** | PII | Candidate identity stripped — hiring on merit only |
| **Developer agents** (Copilot, Cursor, Claude Code) | Secret + Injection | API keys in codebases, prompt injection via code comments |
| **Medical AI** | PII + Secret | Patient identity, system credentials — HIPAA compliance |
| **Legal AI** | PII | Party names, case details — privilege preserved |
| **Meeting tools** | PII | Participant names, financials — cloud-safe summaries |
| **MCP tool servers** | Injection + Secret | Tool-use agents protected from malicious tool responses |

In each case, the integration is the same: intercept text before it reaches the AI, shield, process, rehydrate. The application logic doesn't change. The AI model doesn't change. Only the data flowing between them changes — shielded on the way out, rehydrated on the way back. Developers choose which layers to activate based on their threat model — a hiring tool needs PII Shield only, while a developer agent needs all three.

### 6.4 Key Research Findings

1. **Domain data > model scale**: 22M parameters with domain-specific training matches models 10–70x larger. The investment should be in data quality, not parameter count.

2. **Targeted generation > random augmentation**: 2,070 targeted examples closed the OOD gap more than 18,000 random diverse examples. Know your model's failures, then generate data that addresses them.

3. **ASR noise is signal, not noise**: Training on realistic ASR artifacts (name mangling, punctuation loss, filler words) produces models that work in production. Clean-data-only training creates models that work only in benchmarks.

4. **Cloud PII detection is a contradiction**: The act of sending text to a cloud PII detection API has already violated the privacy you're trying to protect. On-device inference resolves this.

5. **BIO > span extraction for real-time NER**: O(n) token classification enables sub-50ms inference. O(n²) span extraction cannot meet real-time requirements on consumer hardware.

6. **Phantom values preserve AI utility**: Replacing PII with realistic fake values (not `[REDACTED]`) produces coherent AI outputs. The downstream model doesn't know it's operating on phantom text.

---

## 7. Limitations

1. **Detection coverage**: At 97.12% F1 (Shade V7 alone), roughly 2.9% of entities slip through the NER model. However, the full 7-layer pipeline (Shade V7 + Gazetteers + Pre-NLP Patterns + NLP + Regex + URL Detection + Contextual) achieves **100% detection** on 24 real-world meeting transcripts (399 entities, 0 leaked). The multi-layer architecture compensates for individual layer weaknesses — Shade catches ORGs that NLP misses, regex catches URL/money patterns, NLP catches names Shade misses.

2. **Semantic leakage**: Entity-level PII detection doesn't catch implicit identity signals. "My church group" implies religion. "My husband" implies gender and marital status. "I graduated from Howard University" implies race. Extending phantom substitution to semantic-level signals is future work.

3. **Content bias**: Phantom Fairness neutralizes identity signals but cannot address bias encoded in content (e.g., gendered language in job descriptions, cultural references).

4. **Evaluation difficulty**: Measuring "discrimination that didn't happen" is inherently difficult. Counterfactual evaluation (same content, different identities, compare outputs) is needed.

5. **Regional specificity**: Shade V5 is specialized for South African financial, legal, and business text. Entity types (SA ID numbers, rand amounts, local organization names) may not transfer to other regions without targeted fine-tuning.

---

## 8. Future Work

1. **Developmental NER**: Human-inspired training methodology (curriculum learning + knowledge distillation + active learning + elastic weight consolidation) targeting 10x sample efficiency — achieving 97%+ F1 with ~11K examples instead of 116K

2. **Semantic phantom substitution**: Extend beyond entity-level PII to semantic identity signals (pronouns, cultural references, institutional affiliations, gendered language)

3. **Counterfactual fairness evaluation**: Generate matched document pairs (identical content, different identities) and measure AI output divergence as a fairness metric

4. **Multi-modal phantom**: Extend to voice (accent neutralization), images (face replacement), video (appearance abstraction)

5. **Phantom compliance standard**: Propose a regulatory framework where systems can certify "phantom compliance" — proving the AI never receives identity-revealing information

6. **Open-source expansion**: VeilPhantom SDK v1.0.0 is released at [github.com/helloveil/veil-phantom](https://github.com/helloveil/veil-phantom). Future work includes Secret Shield (credential detection) and Injection Shield (prompt injection classification) layers

---

## 9. Conclusion

We present **Phantom Fairness**, a fundamentally new approach to AI discrimination that makes bias architecturally impossible by ensuring AI systems never receive identity-revealing information. Unlike reactive debiasing approaches, Phantom Fairness provides a technical guarantee: if the discriminatory signal was never in the input, it cannot influence the output.

This is enabled by **Shade**, a family of on-device NER models that achieve 97.12% F1 on PII detection with only 22M parameters — matching or exceeding models 10–70x larger while running entirely on consumer hardware. Combined with a 5-layer detection pipeline (NER + NLP + Regex + Gazetteer + Semantic), the system achieves **100% PII detection** on 24 real-world meeting transcripts (399 entities, 0 leaked). The progressive training methodology (V5→V6→V7) introduces several novel techniques: targeted data generation for OOD gap closure, synthetic ASR-noisy transcript generation at negligible cost ($2.30 for 8,486 meetings), name mangling as a training signal, entity swap augmentation, phonetic embeddings, and contrastive hard negative training.

The broader implication: **AI fairness should be an input problem, not an output problem.** Instead of trying to debias models after they've absorbed discriminatory patterns, we should prevent discriminatory signals from reaching the model in the first place. Phantom Fairness demonstrates that this is technically feasible, practically deployable, and achievable with minimal resources.

---

## References

- Barocas, S. & Selbst, A. (2016). Big Data's Disparate Impact. *California Law Review*, 104(3).
- Chouldechova, A. (2017). Fair prediction with disparate impact: A study of bias in recidivism prediction instruments. *Big Data*, 5(2).
- Datta, A. et al. (2015). Automated Experiments on Ad Privacy Settings. *Proceedings on Privacy Enhancing Technologies*.
- Kleinberg, J. et al. (2016). Inherent Trade-Offs in the Fair Determination of Risk Scores. *ITCS*.
- EU AI Act (2024). Regulation (EU) 2024/1689 of the European Parliament.
- He, J. et al. (2024). UniversalNER: Targeted Distillation from Large Language Models for Open Named Entity Recognition. *NAACL Findings*.
- Zaratiana, U. et al. (2024). GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer. *NAACL*.
- Frank, M. (2023). Bridging the data gap between children and large language models. *Trends in Cognitive Sciences*.
- Azar, A. et al. (2022). PLATO: Learning Physics Through Visual Observation. *DeepMind Technical Report*.
- Google Research (2025). Nested Learning: A New ML Paradigm for Continual Learning. *NeurIPS*.
- Tenenbaum, J. et al. (2015). Human-level concept learning through probabilistic program induction. *Science*, 350(6266).
