# ⚖️ Legal Document Assistant Agent

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.3.0+-green.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0+-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Implemented-brightgreen.svg)

**A high-precision, agentic RAG system for contract review, legal research, and automated citation mapping.**

**🌟 100% Open Source Stack: Ollama + ChromaDB + Tesseract + spaCy 🌟**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [API Reference](#-api-reference) • [Open Source Stack](#-open-source-technology-stack)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Open Source Technology Stack](#-open-source-technology-stack)
- [Quick Start](#-quick-start)
- [Features](#-features)
- [Architecture](#-architecture)
- [Agent Capabilities](#-agent-capabilities)
- [API Reference](#-api-reference)
- [Review Workflow](#-review-workflow)
- [Compliance & Security](#-compliance--security)
- [Development](#-development)

---

## 🎯 Overview

The **Legal Document Assistant Agent** is designed for high-stakes regulatory environments where accuracy and traceability are paramount. It orchestrates multiple specialized agents to deconstruct complex contracts, verify claims against case law, and generate "redline" suggestions based on institutional legal guidelines.

### Key Highlights

- 🔍 **Granular RAG**: Pinpoint exact paragraphs and pages for every legal finding
- 📑 **Contract Deconstruction**: Automatic extraction of key dates, obligations, and liabilities
- ⚖️ **Case Law Lookup**: Autonomous research into relevant legal precedents
- 📝 **Auto-Redlining**: Suggests edits based on a "Pre-approved Clause Library"
- 🔒 **Privacy-First**: Fully local LLM option with Ollama for confidential documents

---

## 🌟 Open Source Technology Stack

This implementation prioritizes **fully open source** technologies for maximum privacy and cost-effectiveness:

| Component             | Technology                                                                     | Description                            |
| --------------------- | ------------------------------------------------------------------------------ | -------------------------------------- |
| **LLM**               | [Ollama](https://ollama.ai) + Llama 4                                          | Local, privacy-preserving AI inference |
| **Vector Store**      | [ChromaDB](https://www.trychroma.com/)                                         | Open source embedding database         |
| **OCR**               | [Tesseract](https://github.com/tesseract-ocr/tesseract)                        | Industry-standard open source OCR      |
| **Document Parsing**  | pdfplumber, python-docx                                                        | Open source document processing        |
| **NLP/PII Detection** | [spaCy](https://spacy.io/) + [Presidio](https://microsoft.github.io/presidio/) | Open source NLP pipeline               |
| **Web Framework**     | [FastAPI](https://fastapi.tiangolo.com/)                                       | Modern, fast Python API framework      |
| **Embeddings**        | sentence-transformers                                                          | Open source embedding models           |
| **Orchestration**     | [LangGraph](https://langchain-ai.github.io/langgraph/)                         | Stateful multi-agent workflows         |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- Tesseract OCR installed (`brew install tesseract` on macOS)

### Installation

```bash
# Clone the repository
cd case-studies/legal-document-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_lg

# Pull Ollama model
ollama pull llama3.2

# Copy environment file
cp .env.example .env

# Start the server
python -m uvicorn src.main:app --reload
```

### Docker Compose (Recommended)

```bash
# Start the complete stack (API + Ollama + ChromaDB + Redis)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

The API will be available at `http://localhost:8000` with:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## ✨ Features

### Core Capabilities

| Feature                     | Description                                                       |
| --------------------------- | ----------------------------------------------------------------- |
| 🛡️ **Risk Detector**        | AI-driven identification of "Unfavorable" terms with risk scoring |
| 🕵️ **Entity Extraction**    | Extracts Parties, Dates, Amounts, and Jurisdictions               |
| 📖 **Citation Engine**      | Links findings to Source Page/Line Number                         |
| 📉 **Comparative Analysis** | Document A vs Document B (Delta Analysis)                         |
| 🏛️ **Case Research**        | Autonomous search with Bluebook citation generation               |
| 📁 **Multi-Format Parsing** | OCR support for Scanned PDFs and Images                           |
| 🔐 **PII Detection**        | Automatic detection and optional redaction                        |
| ✅ **Compliance Checking**  | GDPR, CCPA, HIPAA, SOC2, and more                                 |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LEGAL DOCUMENT ASSISTANT AGENT                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    ORCHESTRATOR AGENT (LangGraph)                │   │
│  │  • Multi-Turn Reasoning                                           │   │
│  │  • Conflict Resolution (Legal Logic)                               │   │
│  │  • Progress Tracking & State Management                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│       ┌────────────────────────────┼────────────────────────────┐       │
│       │                            │                            │       │
│  ┌────▼────┐  ┌─────────▼─────────┐  ┌──────▼──────┐  ┌──────▼──────┐ │
│  │ INTAKE  │  │    ANALYSIS       │  │  RESEARCH   │  │ COMPLIANCE  │ │
│  │ AGENT   │  │    AGENT          │  │  AGENT      │  │ AGENT       │ │
│  │         │  │                   │  │             │  │             │ │
│  │• OCR    │  │• Clause ID        │  │• Case Law   │  │• GDPR Check │ │
│  │• Parse  │  │• Risk Scoring     │  │• Statutes   │  │• CCPA Check │ │
│  │• PII    │  │• Obligations      │  │• Citations  │  │• HIPAA/SOC2 │ │
│  └─────────┘  └───────────────────┘  └─────────────┘  └─────────────┘ │
│       │                                                      │         │
│  ┌────▼──────────────────────────────────────────────────────▼─────┐  │
│  │                        REDLINING AGENT                          │  │
│  │  • Clause Library Comparison  • Style Guide Compliance          │  │
│  │  • Track-Changes Generation   • Negotiation Points              │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                         DATA LAYER (Open Source)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ ChromaDB     │  │ Clause       │  │ SQLite/      │  │ Audit Log  │ │
│  │ (Vectors)    │  │ Library      │  │ PostgreSQL   │  │ Store      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Multi-Agent Workflow (LangGraph)

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────────┐    ┌──────────┐
│  INTAKE  │───▶│ ANALYSIS │───▶│ RESEARCH │───▶│ COMPLIANCE │───▶│ REDLINE  │
│  (OCR)   │    │ (Risks)  │    │ (Cases)  │    │ (GDPR)     │    │ (Edits)  │
└──────────┘    └──────────┘    └──────────┘    └────────────┘    └──────────┘
                                                                        │
                                                                        ▼
                                                              ┌──────────────┐
                                                              │ FINAL REPORT │
                                                              └──────────────┘
```

---

## 🤖 Agent Capabilities

### 1. Intake & OCR Agent

- **Document Validation**: Supports PDF, DOCX, DOC, TXT, PNG, JPG
- **OCR Processing**: Tesseract-powered text extraction from scanned documents
- **Structural Parsing**: Sections, paragraphs, tables extraction
- **PII Detection**: Using Presidio for automatic PII identification
- **Document Fingerprinting**: SHA-256 hashing for deduplication

### 2. Contract Analysis Agent

- **Risk Heatmap**: Visual risk scoring by document section
- **Entity Linking**: Connects references across the document
- **Obligation Extraction**: Deadlines, financial commitments, responsibilities
- **Clause Classification**: 15+ standard clause categories
- **Deviation Detection**: Compare against standard templates

### 3. Legal Research Agent

- **Autonomous RAG**: ChromaDB-powered semantic search
- **Case Law Lookup**: Search and retrieve relevant precedents
- **Statute Research**: Find applicable regulations
- **Market Standard Verification**: Check if clauses are industry-standard
- **Citation Generation**: Bluebook-formatted legal citations

### 4. Compliance Agent

- **Multi-Framework Support**: GDPR, CCPA, HIPAA, SOC2, PCI-DSS, SOX, FERPA, GLBA
- **Gap Identification**: Find missing compliance requirements
- **Regulatory Mapping**: Map clauses to specific regulations
- **Prioritized Recommendations**: Action items by severity

### 5. Redlining Agent

- **Clause Library Comparison**: Match against pre-approved language
- **Track-Changes Generation**: Unified diff view of suggestions
- **Style Guide Compliance**: Ensure institutional standards
- **Negotiation Points**: Provide talking points for each change

---

## 🔧 API Reference

### Document Management

| Method   | Endpoint                                  | Description                      |
| -------- | ----------------------------------------- | -------------------------------- |
| `POST`   | `/api/v1/documents/upload`                | Upload a document for processing |
| `GET`    | `/api/v1/documents/`                      | List all uploaded documents      |
| `GET`    | `/api/v1/documents/{doc_id}`              | Get document details             |
| `POST`   | `/api/v1/documents/{doc_id}/full-review`  | Run complete multi-agent review  |
| `POST`   | `/api/v1/documents/{doc_id}/quick-review` | Fast initial assessment          |
| `DELETE` | `/api/v1/documents/{doc_id}`              | Delete a document                |

### Analysis

| Method | Endpoint                                | Description                  |
| ------ | --------------------------------------- | ---------------------------- |
| `POST` | `/api/v1/analysis/contract`             | Analyze contract for risks   |
| `GET`  | `/api/v1/analysis/risks/{doc_id}`       | Get detailed risk report     |
| `POST` | `/api/v1/analysis/redline/suggest`      | Generate redline suggestions |
| `POST` | `/api/v1/analysis/redline/apply`        | Apply redline suggestions    |
| `GET`  | `/api/v1/analysis/clauses/{doc_id}`     | Get identified clauses       |
| `GET`  | `/api/v1/analysis/obligations/{doc_id}` | Get extracted obligations    |

### Research

| Method | Endpoint                                   | Description                        |
| ------ | ------------------------------------------ | ---------------------------------- |
| `POST` | `/api/v1/research/query`                   | Perform legal research             |
| `GET`  | `/api/v1/research/case/{citation}`         | Look up specific case              |
| `GET`  | `/api/v1/research/statute/{ref}`           | Look up statute                    |
| `POST` | `/api/v1/research/market-standard`         | Check if clause is market standard |
| `POST` | `/api/v1/research/knowledge-base/case-law` | Add case to knowledge base         |
| `POST` | `/api/v1/research/knowledge-base/clause`   | Add pre-approved clause            |

### Compliance

| Method | Endpoint                              | Description                   |
| ------ | ------------------------------------- | ----------------------------- |
| `POST` | `/api/v1/compliance/check`            | Run compliance assessment     |
| `GET`  | `/api/v1/compliance/gaps/{doc_id}`    | Get compliance gaps           |
| `GET`  | `/api/v1/compliance/mapping/{doc_id}` | Get regulatory clause mapping |
| `GET`  | `/api/v1/compliance/frameworks`       | List supported frameworks     |
| `POST` | `/api/v1/compliance/check-regulation` | Check specific regulation     |

---

## 📊 Review Workflow

### Full Review Process

```python
import httpx

# 1. Upload document
with open("contract.pdf", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/api/v1/documents/upload",
        files={"file": f},
        data={"detect_pii": True}
    )
document_id = response.json()["document_id"]

# 2. Run full review (runs all agents in sequence)
response = httpx.post(
    f"http://localhost:8000/api/v1/documents/{document_id}/full-review"
)
report = response.json()

# 3. Access results
print(f"Risk Level: {report['risk_assessment']['risk_level']}")
print(f"Compliance Score: {report['compliance_assessment']['overall_score']}")
print(f"Suggested Changes: {report['redline_suggestions']['total_suggestions']}")
```

### Quick Review (Fast Assessment)

```python
response = httpx.post(
    f"http://localhost:8000/api/v1/documents/{document_id}/quick-review"
)
quick_report = response.json()

print(f"Risk Score: {quick_report['risk_score']}/100")
print(f"Recommendation: {quick_report['recommendation']}")
```

---

## 🔒 Compliance & Security

### Privacy Features

| Feature              | Description                                                           |
| -------------------- | --------------------------------------------------------------------- |
| 🏠 **Local LLM**     | Ollama runs entirely on-premises - no data leaves your infrastructure |
| 🔐 **PII Masking**   | Automatic detection and optional redaction of sensitive information   |
| 📝 **Audit Logging** | Complete trail of all processing steps for compliance                 |
| 🔑 **Encryption**    | AES-256 for documents at rest (when enabled)                          |

### Supported Compliance Frameworks

- **GDPR** - EU General Data Protection Regulation
- **CCPA** - California Consumer Privacy Act
- **HIPAA** - Health Insurance Portability and Accountability Act
- **SOC2** - Service Organization Control 2
- **PCI-DSS** - Payment Card Industry Data Security Standard
- **SOX** - Sarbanes-Oxley Act
- **FERPA** - Family Educational Rights and Privacy Act
- **GLBA** - Gramm-Leach-Bliley Act

---

## 💻 Development

### Project Structure

```
legal-document-assistant/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Pydantic settings
│   ├── agents/              # Multi-agent system
│   │   ├── base.py          # Base agent class
│   │   ├── intake_agent.py  # OCR & document processing
│   │   ├── analysis_agent.py # Contract analysis
│   │   ├── research_agent.py # Legal research RAG
│   │   ├── compliance_agent.py # Regulatory compliance
│   │   ├── redlining_agent.py # Redline generation
│   │   └── orchestrator.py  # LangGraph workflow
│   ├── api/                 # FastAPI routes
│   │   ├── schemas.py       # Pydantic models
│   │   └── routes/
│   │       ├── documents.py
│   │       ├── analysis.py
│   │       ├── research.py
│   │       └── compliance.py
│   └── data/
│       └── clause_library.py # Pre-approved clauses
├── tests/                   # Test suite
├── data/                    # Runtime data (gitignored)
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container definition
├── docker-compose.yml      # Full stack deployment
└── README.md
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

### Environment Variables

See `.env.example` for all configuration options. Key variables:

| Variable                   | Description                            | Default                    |
| -------------------------- | -------------------------------------- | -------------------------- |
| `LLM_PROVIDER`             | LLM provider (ollama/openai/anthropic) | `ollama`                   |
| `OLLAMA_MODEL`             | Ollama model to use                    | `llama4`                   |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB storage path                  | `./data/chroma`            |
| `PII_DETECTION_ENABLED`    | Enable PII detection                   | `true`                     |
| `TESSERACT_CMD`            | Path to Tesseract binary               | `/usr/local/bin/tesseract` |

---

## 📚 Case Study Details

| Attribute      | Description                                                                              |
| -------------- | ---------------------------------------------------------------------------------------- |
| **Objective**  | Reduce manual contract review time by 70% while improving detection of high-risk clauses |
| **Domain**     | Legal, Corporate Compliance, Risk Management                                             |
| **Skills**     | Advanced NLP, Document Parsing (OCR), Agentic RAG, Legal Reasoning                       |
| **Complexity** | Advanced                                                                                 |
| **Duration**   | 8-10 weeks implementation                                                                |

### Problem Statement

Legal teams are overwhelmed by:

- **Review Volume**: Thousands of NDAs, Vendor Agreements, and MSAs
- **Human Oversight**: High risk of missing critical "hidden" clauses
- **Research Latency**: Hours spent manually searching statutes
- **Inconsistency**: Different lawyers redlining terms differently

### Solution

This agentic system provides:

1. **Automated Risk Scoring**: Immediate "Heatmap" of risky sections
2. **Regulatory Mapping**: Links clauses to specific laws
3. **Drafting Consistency**: Unified legal language from clause library
4. **Audit Trail**: Full history of interpretations and suggestions

---

<div align="center">

**Author: Gopal Saini**  
_Part of the AI Agents Case Studies Collection_

[⬆ Back to Top](#️-legal-document-assistant-agent)

</div>
