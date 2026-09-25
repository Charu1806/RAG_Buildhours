# Architecture: HDFC Fund Facts FAQ (RAG Prototype)

**Source of truth:** [PRD.md](./PRD.md) for product, corpus, and RAG.  
**UI source of truth:** [Design/stitch_growchatbot_dark_ui_interface/](../Design/stitch_growchatbot_dark_ui_interface/) (Stitch). This replaces PRD §7 Streamlit.  
**Type:** Local prototype. Single demo user. No auth, no hosting, no analytics.  
**UI:** Stitch HTML/CSS chat (`code.html` + `DESIGN.md`). Not Streamlit. Not a separate ingest service.

---

## 1. System shape

Closed-corpus RAG. Five Groww URLs in. One short, cited answer out — or a refusal.

```
                    ┌─────────────────────────────────────────┐
                    │         Stitch UI (not Streamlit)       │
                    │  GrowChatBot dark chat · 3 example Qs   │
                    │  “Facts-only. No investment advice.”    │
                    └───────────────────┬─────────────────────┘
                                        │ question
                                        ▼
                    ┌─────────────────────────────────────────┐
                    │         Guardrails (pre-retrieve)       │
                    │  PII reject · advice/compare refuse     │
                    └───────────────────┬─────────────────────┘
                                        │ allowed factual Q
                                        ▼
     Phase 5                      retrieve top-k
                    ┌─────────────────────────────────────────┐
                    │  query embed (same MiniLM) → ChromaDB   │
                    │  weak hit → “not in our sources”        │
                    │  else → Mistral (chunks only)           │
                    │  ≤3 sentences · 1 URL · last-updated    │
                    └─────────────────────────────────────────┘

Offline / on-demand ingest (Phases 1–4)
  5 Groww URLs → load → chunk → MiniLM embed → ChromaDB
```

| Layer | PRD choice |
|---|---|
| Corpus | Five Groww HDFC Direct Growth pages only |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store | ChromaDB |
| LLM | Mistral API |
| UI | Stitch design — static HTML/CSS from `Design/stitch_growchatbot_dark_ui_interface/`. Not Streamlit. |

There is no other data path.

---

## UI: Stitch design (replaces Streamlit)

Implement the chat shell from the Stitch export. Do **not** use Streamlit.

| Artifact | Path |
|---|---|
| Markup / layout | `Design/stitch_growchatbot_dark_ui_interface/code.html` |
| Tokens, type, components | `Design/stitch_growchatbot_dark_ui_interface/DESIGN.md` |
| Visual target | `Design/stitch_growchatbot_dark_ui_interface/screen.png` |

**Must keep (PRD):** welcome, three example-question chips (expense ratio, ELSS lock-in, min SIP), disclaimer **“Facts-only. No investment advice.”**, chat input, session-only history, assistant envelope = answer text → one citation URL → `Last updated from sources:`.

**Must match Stitch:** dark Groww-style terminal (`#070B12` / `#0D1322`), Plus Jakarta Sans + Inter, suggested chips, amber disclaimer bar, user vs assistant bubbles, bottom-anchored input. No extra nav, no fund picker.

**Wiring:** the Stitch page sends the question to the existing retrieval backend (`answer_question`). Generation stays in Phase 6. Chat is session-only; nothing on disk; PII is not shown or stored.

---

## 2. Phase: Data loading

**Purpose:** Pull text from the five PRD URLs and nothing else.

**Allowed URLs (hard lock):**

| Fund | URL |
|---|---|
| HDFC Large Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| HDFC Flexi Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| HDFC ELSS Tax Saver Fund Direct Plan Growth | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| HDFC Small Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| HDFC Balanced Advantage Fund Direct Growth | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth |

**Do:**

- Fetch each URL’s public HTML and extract visible page text.
- Record `source_url`, `fund_name`, and `fetched_at` (this date is “Last updated from sources”).
- Fail the ingest if any of the five URLs does not load (PRD acceptance: all five must ingest).

**Do not:**

- Follow outbound links, factsheets, blogs, or other funds (v1 = pages only).
- Store PAN, Aadhaar, account numbers, OTPs, emails, phones — loaders never persist user input.
- Keep screenshots or third-party copies.

**PRD open question (stay inside the same five URLs):** if a page is JS-thin, a one-time saved HTML snapshot of **that same URL** is the only allowed fallback.

**Output contract:** five documents  
`{ fund_name, source_url, page_text, fetched_at }`

---

## 3. Phase: Chunking

**Purpose:** Split each loaded page so retrieval can hit a fact (expense ratio, SIP, exit load, lock-in, riskometer/benchmark, capital-gains statement steps).

**Do (PRD ingest rule):**

- Chunk by heading, or by fixed size with overlap if headings are weak.
- Copy parent metadata onto every chunk: `source_url`, `fund_name`, `fetched_at`.
- Keep chunks self-contained enough that one chunk can support a ≤3-sentence answer.

**Do not:**

- Merge text from two different URLs into one chunk (citation must be exactly one URL).
- Drop `source_url` — F3 depends on it.

**Output contract:** list of chunks  
`{ chunk_id, text, source_url, fund_name, fetched_at }`

---

## 4. Phase: Embedding

**Purpose:** Turn chunk text (and later the user question) into vectors with one model.

**Model (locked):** `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face).

**Do:**

- Embed `chunk.text` only. Metadata is stored beside the vector, not inside the embedding string.
- Use this same model at query time. No second embedding model.

**Do not:**

- Embed PII or raw chat logs.
- Use a different model for questions vs. chunks.

**Output contract:**  
`{ chunk_id, embedding, text, source_url, fund_name, fetched_at }`

---

## 5. Phase: Vector store

**Purpose:** Persist chunk vectors so they are queryable.

**Store (locked):** ChromaDB, local to the prototype.

**Do:**

- One collection for this corpus.
- Upsert by `chunk_id` so re-ingest of the same five URLs replaces old vectors.
- Persist metadata fields needed at answer time: `source_url` (citation), `fetched_at` (footer), `fund_name` (disambiguation).

**Do not:**

- Index any URL outside the five.
- Store session chat history (PRD: session-only in the UI, not on disk).
- Store user PII.

**Acceptance hook:** after this phase, all five source URLs must be present and queryable in ChromaDB.

---

## 6. Phase: Retrieval logic

**Purpose:** From an allowed question, fetch the right chunks and produce the PRD answer shape — or refuse / abstain.

Runs only after the Stitch UI accepts a question. Generation is in this phase because the PRD pipeline is retrieve → prompt (Mistral) → answer; there is no separate generate service.

### 6.1 Before retrieve (guards)

| Signal | Action |
|---|---|
| PAN, Aadhaar, account number, OTP, email, phone | Reject. Do not embed, retrieve, log, or store. Do not echo the value. |
| Buy / sell / switch / “should I” / portfolio allocation | Fixed polite refusal. No retrieval required. Optional one educational link from the five URLs. |
| Compare / compute returns (“which is better?”, “what will 1L become?”) | Refuse to compute or compare. Link only to the relevant page (or on-page / factsheet pointer if the question names a corpus fund). |
| Empty / gibberish | Ask for a factual question about one of the five funds. No retrieve. |

### 6.2 Retrieve

1. Embed the question with `all-MiniLM-L6-v2`.
2. Query ChromaDB for top-k chunks (k small; corpus is five pages).
3. If similarity is weak or chunks are off-question → **do not guess.** Return “not on the five pages” (F9). This covers out-of-corpus funds (e.g. SBI Bluechip) and facts not on the pages.
4. If the question is “this fund” / unnamed SIP with no usable fund in the query or top chunks → ask the user to name one of the five. Do not pick a fund for them.

### 6.3 Generate (Mistral, chunks only)

Prompt rules (PRD):

- Use only the retrieved chunk text.
- ≤3 sentences.
- Exactly one citation: `source_url` of the chunk(s) used. If chunks disagree on URL, cite the single best-matching fund page — never two.
- Append `Last updated from sources: <fetched_at>`.
- Never invent expense ratios, dates, or returns.
- Never give buy/sell advice even if the user slipped past the pre-guard.

**Answer envelope (Stitch UI):**  
`answer_text` → one citation URL → last-updated line. Render in the assistant bubble from the Stitch design (not Streamlit).

If the user named no fund and chunks are mixed, prefer the clarify path over a blended answer.

---

## 7. Phase: Retrieval testing

**Purpose:** Prove the closed corpus retrieves the right page (or correctly abstains). This is the PRD edge-case set, not a separate eval product.

Run after ChromaDB is loaded. Two layers: **retrieve-only** (chunk URL / abstain) and **full path** (guards + retrieve + Mistral + UI envelope).

### 7.1 Retrieve-only checks

| Query (PRD §10) | Must retrieve / decide |
|---|---|
| Expense ratio of HDFC Large Cap | Chunks from the Large Cap URL |
| ELSS lock-in | Chunks from the ELSS URL |
| Minimum SIP (named fund) | That fund’s URL |
| Minimum SIP (no fund named) | No silent pick — clarify |
| Expense ratio of SBI Bluechip | Weak / no in-corpus hit → abstain |
| Fact not on the five pages | Abstain |
| Ambiguous “this fund” | Clarify, do not retrieve-and-guess |

Pass: top hit `source_url` matches the expected Groww page, or the pipeline abstains/clarifies as above.

### 7.2 Full-path checks (PRD §10 + §11)

| Case | Expected |
|---|---|
| Expense ratio of HDFC Large Cap | Fact + that URL + last-updated; ≤3 sentences |
| ELSS lock-in | Lock-in from page + ELSS URL + last-updated |
| Minimum SIP (named) | Number from that fund + its URL |
| Should I buy HDFC Small Cap? | Refusal; no advice |
| Which fund is better? / Compare 3Y returns | Refuse compute/compare; link only |
| SBI Bluechip expense ratio | Out of corpus; no invented number |
| User pastes PAN / phone / email | Reject; value never on disk or in logs |
| Empty / gibberish | Ask for a factual question |
| Three UI example questions | Grounded short answer + one URL + last-updated |

**Pass bar (PRD acceptance):** five URLs queryable; example questions cited; advice/compare set refused 100%; PII never persisted.

No extra test harness, dashboards, or corpora. The checklist above is the test plan.

---

## 8. What this architecture will not include

Per PRD out of scope: other AMCs/funds, login/KYC/portfolio, calculators, advisor persona, production hosting, persisted chat history, any source that is not one of the five URLs.

---

## 9. Phase order

| Order | Phase | Done when |
|---|---|---|
| 1 | Data loading | Five documents with URL + `fetched_at` |
| 2 | Chunking | Chunks carry one `source_url` each |
| 3 | Embedding | MiniLM vectors for all chunks |
| 4 | Vector store | All five URLs queryable in ChromaDB |
| 5 | Retrieval logic | Guards + top-k + Mistral envelope |
| 6 | Retrieval testing | PRD §10 / §11 checklist green |

M0 is these six phases plus the Stitch UI shell (`code.html` / `DESIGN.md`). Streamlit is out of scope. That is the whole design.
