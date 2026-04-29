---
specialty: ai-engineering
last_researched: 2026-04
---

# AI Engineering — CV Framing Rules

**Used by:** cv_targeted, role_evaluation

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

## Adjacency

Translation signal for entries tagged with adjacent specialties:

- **data-engineering**: feature pipelines, training-data curation, and ML infrastructure work translates directly. Where AI capabilities rest on data infrastructure built or operated by the candidate, the infrastructure work reads as data-engineering depth supporting AI delivery.
