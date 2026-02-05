# ⚖️ Legal Document Assistant Agent

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F61?style=for-the-badge&logo=databricks&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**A high-precision, agentic RAG system for contract review, legal research, and automated citation mapping.**

[Features](#-features) • [Architecture](#-architecture) • [Case Study](#-case-study-details) • [Agent Capabilities](#-agent-capabilities) • [API Reference](#-api-reference)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Case Study Details](#-case-study-details)
- [Features](#-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Agent Capabilities](#-agent-capabilities)
- [Review Workflow](#-review-workflow)
- [Compliance & Security](#-compliance--security)
- [API Reference](#-api-reference)

---

## 🎯 Overview

The **Legal Document Assistant Agent** is designed for high-stakes regulatory environments where accuracy and traceability are paramount. It orchestrates multiple agents to deconstruct complex contracts, verify claims against case law, and generate "redline" suggestions based on institutional legal guidelines.

- 🔍 **Granular RAG**: Pinpoint exact paragraphs and pages for every legal finding.
- 📑 **Contract Deconstruction**: Automatic extraction of key dates, obligations, and liabilities.
- ⚖️ **Case Law Lookup**: Autonomous research into relevant legal precedents.
- 📝 **Auto-Redlining**: Suggests edits based on a "Pre-approved Clause Library."

---

## 📚 Case Study Details

| Attribute      | Description                                                                                                      |
| -------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Objective**  | Reduce manual contract review time by 70% while improving the detection of high-risk clauses and non-compliance. |
| **Domain**     | Legal, Corporate Compliance, Risk Management                                                                     |
| **Skills**     | Advanced NLP, Document Parsing (OCR), Agentic RAG, Legal Reasoning, Knowledge Graph Integration                  |
| **Complexity** | Advanced                                                                                                         |
| **Duration**   | 8-10 weeks implementation                                                                                        |

### Problem Statement

Legal teams are overwhelmed by:

- **Review Volume**: Thousands of NDAs, Vendor Agreements, and MSAs.
- **Human Oversight**: High risk of missing critical "hidden" clauses (e.g., auto-renewals).
- **Research Latency**: Hours spent manually searching through statutes and past filings.
- **Inconsistency**: Different lawyers redlining the same terms in different ways.

### Solution

This agentic system provides:

1. **Automated Risk Scoring**: Immediate "Heatmap" of risky contract sections.
2. **Regulatory Mapping**: Links document clauses to specific federal/local laws.
3. **Drafting Consistency**: Ensures all company contracts use unified legal language.
4. **Audit Trail**: Full history of why a specific change or interpretation was suggested.

---

## ✨ Features

### Core Capabilities

| Feature                     | Description                                         |
| --------------------------- | --------------------------------------------------- |
| 🛡️ **Risk Detector**        | AI-driven identification of "Unfavorable" terms     |
| 🕵️ **Entity Extraction**    | Extracts Parties, Dates, Amounts, and Jurisdictions |
| 📖 **Citation Engine**      | Links findings to Source Page/Line Number           |
| 📉 **Comparative Analysis** | Document A vs Document B (Delta Analysis)           |
| 🏛️ **Case Research**        | Autonomous search across SEC/Legal DBs              |
| 📁 **Multi-Format Parsing** | OCR support for Scanned PDFs and Images             |

### Agent Types

1. **Intake & OCR Agent**: Handles document sanitation, OCR, and structural parsing.
2. **Contract Analysis Agent**: Expert in identifying legal risks and obligations.
3. **Research Agent**: Queries external legal databases and statutes.
4. **Redlining Agent**: Suggests edits based on the institutional style guide.
5. **Summarization Agent**: Generates executive "briefs" for decision-makers.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LEGAL DOCUMENT ASSISTANT AGENT                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      ORCHESTRATOR AGENT                          │   │
│  │  • Multi-Turn Reasoning                                           │   │
│  │  • Conflict Resolution (Legal Logic)                               │   │
│  │  • Progress Tracking                                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                    ┌───────────────┼───────────────┐                    │
│                    │               │               │                    │
│  ┌─────────────────▼──┐  ┌────────▼────────┐  ┌──▼─────────────────┐  │
│  │ ANALYSIS AGENT     │  │ RESEARCH AGENT  │  │ DRAFTING AGENT     │  │
│  │                    │  │                 │  │                    │  │
│  │ • Clause ID        │  │ • Statute Search│  │ • Redline Logic    │  │
│  │ • Risk Scoring     │  │ • Case Mapping  │  │ • Clause Library   │  │
│  │ • Deviation Detect │  │ • Citation Gen  │  │ • Tone Alignment   │  │
│  └────────────────────┘  └─────────────────┘  └────────────────────┘  │
│                                                                          │
│  ┌────────────────────┐  ┌─────────────────┐  ┌────────────────────┐  │
│  │ PARSING AGENT      │  │ DATA PRIVACY    │  │ COMPLIANCE AGENT   │  │
│  │                    │  │ AGENT           │  │                    │  │
│  │ • OCR / Layout     │  │ • PII Redaction │  │ • Regulatory Bench │  │
│  │ • Table Extract    │  │ • Privacy Risk  │  │ • GDPR/CCPA Check  │  │
│  │ • Doc Structure    │  │ • Data Mapping  │  │ • SOC2 Alignment   │  │
│  └────────────────────┘  └─────────────────┘  └────────────────────┘  │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                              DATA LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Vector Store │  │ Legal DBs    │  │ Clause Bank  │  │ Log Store  │ │
│  │ (Qdrant)     │  │ (RAG)        │  │ (Postgres)   │  │ (Audit)    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component        | Technology                          |
| ---------------- | ----------------------------------- |
| **AI Framework** | LangChain, LangGraph                |
| **LLM**          | GPT-4o-32k (Context), Claude 3 Opus |
| **OCR**          | Azure AI Document Intelligence      |
| **Vector Store** | Qdrant (Self-hosted for privacy)    |
| **Legal APIs**   | Westlaw, LexisNexis, EDGAR (SEC)    |
| **Backend**      | FastAPI, Python 3.14+               |
| **Formats**      | Unstructured.io (PDF/Word/Images)   |

---

## 🤖 Agent Capabilities

### 1. Analysis Agent

- **Risk Heatmap**: Colors code sections of a contract based on "Firm Favorability."
- **Entity Linking**: Automatically links "The Client" defined on Page 1 to subsequent obligations on Page 40.
- **Obligation Extraction**: Creates a table of deadlines and financial commitments.

### 2. Research Agent

- **Autonomous RAG**: Iteratively searches across statutory databases to verify if a clause is "Market Standard."
- **Citation Auto-Generator**: Formats legal citations in Bluebook or standard styles.

### 3. Drafting Agent

- **One-Click Redlining**: Generates a DOCX with track-changes version of the original document.
- **Variation Checker**: Identifies when a clause deviates from the company's "Standard Language" and explains why.

---

## 🔒 Compliance & Security

Due to the sensitive nature of legal data, the system implements:

- **Local LLM Option**: Support for deployment via vLLM/Ollama for highly confidential data.
- **PII Masking**: Automatic redaction of sensitive names/addresses before processing.
- **Role-Based Access**: Granular control over who can view specific reports or contracts.
- **Encryption**: AES-256 for documents at rest and TLS 1.3 for data in transit.

---

## 🔧 API Reference

### Endpoints

| Method | Endpoint                   | Description              |
| ------ | -------------------------- | ------------------------ |
| `POST` | `/api/v1/analyze/contract` | Upload and analyze doc   |
| `GET`  | `/api/v1/risks/{doc_id}`   | Get detailed risk report |
| `POST` | `/api/v1/redline/suggest`  | Get redline suggestions  |
| `GET`  | `/api/v1/research/query`   | Query the legal RAG      |
| `POST` | `/api/v1/summarize`        | Executive summary gen    |

---

<div align="center">

**Author: Gopal Saini**
_Part of the AI Agents Case Studies Collection_

</div>
