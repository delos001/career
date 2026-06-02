---
specialty: ai-engineering
last_researched: 2026-05
---

# AI Engineering - CV Framing Rules

**Used by:** cv-targeted, axis-classifier

## Capability vocabulary

- Production ML system design and deployment
- Model training, fine-tuning (PEFT, LoRA, QLoRA, RLHF, DPO), and evaluation
- Production LLM and agent application development
- Retrieval-augmented generation (RAG) system design (vector, hybrid, agentic)
- Multi-agent system orchestration (LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, Anthropic Agent SDK)
- Tool use, function calling, and Model Context Protocol (MCP) integration
- Prompt engineering and prompt evaluation
- MLOps and LLMOps pipeline design
- Feature store implementation
- Model serving and inference architecture (vLLM, TGI, batched, streaming)
- A/B testing and online evaluation for ML systems
- Model monitoring, drift detection, and LLM observability (LangSmith, Braintrust, Langfuse)
- AI safety, evaluation, alignment, and red teaming practices
- Cross-functional AI delivery

## Terminology

- LLM, foundation model, embedding, transformer
- Fine-tuning: full fine-tuning, instruction tuning, PEFT, LoRA, QLoRA, RLHF, DPO, RLAIF
- RAG: vector retrieval, hybrid retrieval (BM25 + semantic), reranking, contextual retrieval, agentic RAG, graph RAG
- Prompt engineering, chain-of-thought, few-shot, zero-shot, structured outputs
- Agents: LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, Anthropic Agent SDK; tool use, function calling, multi-agent orchestration, Model Context Protocol (MCP)
- MLOps/LLMOps: model registry, feature store, model gateway, MLflow; observability (LangSmith, Braintrust, Langfuse, Helicone, Phoenix)
- Inference: vLLM, TGI (text-generation-inference), Triton, SGLang, Ollama; batch, real-time, streaming; optimization (quantization int4/int8/GGUF/AWQ, KV cache, prompt caching, speculative decoding)
- Vector databases: Pinecone, Weaviate, Chroma, pgvector, Qdrant, Milvus
- Evaluation: eval harness, BLEU, ROUGE, perplexity, win rate, LLM-as-judge, golden dataset
- ML frameworks: PyTorch, TensorFlow, JAX, scikit-learn, XGBoost
- AI development frameworks: HuggingFace, LangChain, LlamaIndex, DSPy
- Foundation models: Anthropic Claude, OpenAI GPT, Google Gemini, Mistral, Llama, DeepSeek
- Multi-modal: vision, audio, video, text-to-image, text-to-speech
- Drift detection, concept drift, distribution shift, hallucination, factuality

## Knowledge-transfer mode

- Training delivery, curriculum design, and adoption coaching on this specialty's capabilities, methods, tools, or artifacts, when concurrently practicing the specialty in the role.

## Adjacency

Translation signal for entries tagged with adjacent specialties:

- **data-engineering**: feature pipelines, training-data curation, and ML infrastructure work translates directly. Where AI capabilities rest on data infrastructure built or operated by the candidate, the infrastructure work reads as data-engineering depth supporting AI delivery.
- **data-science**: when applied modeling moved across the research-to-production boundary, the research/prototype layer reads as data-science depth and the production deployment layer reads as ai-engineering depth. Both often co-tag when the candidate carried the work across stages.
- **operations-strategy**: when AI strategy and platform evaluation decisions preceded or accompanied implementation, the strategy layer reads as operations-strategy depth and the build layer reads as ai-engineering depth.
- **clinical-operations**: bridge is narrow. Co-tags only when production AI/ML systems were deployed for clinical-operations purposes (anomaly detection in centralized monitoring, AI-assisted protocol or site analytics in production). Clinical-domain prototypes that stop short of production deployment do not carry.
- **quality-compliance**: when AI/ML systems the candidate built were subject to validation (CSV/CSA), model documentation per FDA AI/ML guidance, or audit-trail requirements, quality-compliance co-tags as the validation framing and ai-engineering carries the build.
- **people-leadership**: co-tags when the ai-engineering role included team management (direct or matrixed) of ML/AI engineering staff. Technical lead-without-team-management does not co-tag.

### Low or no adjacency

_(none)_

