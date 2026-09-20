### The Compute Spec: RTX 4090 (24 GB VRAM)

**RunPod RTX 4090 instance** at ~$0.74/hour.

Do not downscale to a cheaper card or upscale to an enterprise A100/H100 for this phase. The 4090 gives you 24 GB of GDDR6X Video Random Access Memory (VRAM—high-speed dedicated memory on the graphics card used to hold model weights and intermediate tensors) and massive memory bandwidth. This gives you enough headroom to load Surya v2’s vision encoder and language decoder concurrently without memory fragmentation or aggressive context-window throttling, keeping your telemetry metrics clean and unskewed by hardware bottlenecks.

---

### The Test Corpus: The Worst-Case Stress Test

You cannot benchmark an OCR (Optical Character Recognition—the conversion of scanned or image-based text into machine-encoded text) and VLM (Vision-Language Model—a neural network that processes both visual and textual inputs) pipeline on a clean, single-column 1-page memo. That tells you nothing.

To break the parser and expose real flaws—like broken HTML table tags, overlapping columns, and misaligned bounding-box sorting—you need a structurally hostile document.

We will pull a dense, multi-column research preprint loaded with math notation, footnotes, and complex nested tables directly into our corpus directory via script.

---

### The Execution Roadmap

Lock this plan in. Here is how we execute from zero to telemetry:

```
┌─────────────────────────┐     ┌─────────────────────────     ┐
│  1. Spin Up RunPod      │ ──> │ 2. Corpus Ingestion          │
│     (RTX 4090 / PyTorch)│     │    (Pull Dense Preprint PDF) │
└─────────────────────────┘     └──────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────┐     ┌──────────────────────────────┐
│  4. Execute Harness     │ <── │ 3. Environment Bootstrap     │
│     (bench.py telemetry)│     │    (setup.sh & dependencies) │
└─────────────────────────┘     └──────────────────────────────┘

```

#### Phase 1: Infrastructure Provisioning

* Spin up the RunPod instance using the official PyTorch template.
* Ensure SSH port-forwarding and Jupyter port `8888` are exposed.

#### Phase 2: Corpus Ingestion

* Create a dedicated `corpus/` directory in your repository.
* Programmatically download a dense, multi-column preprint (e.g., a complex arXiv paper or clinical preprint) to act as your primary stress test artifact.

#### Phase 3: Environment Bootstrap (`setup.sh`)

* Write a modular shell script that checks CUDA device availability via `nvidia-smi`.
* Installs `surya-ocr` and locks down dependency versions to prevent silent breaking changes.

#### Phase 4: Telemetry Harness (`bench.py`)

* Implement the evaluation loop that tracks throughput (pages per second), tail latencies (p50, p95, p99), and peak VRAM allocation via `torch.cuda.max_memory_allocated()`.

---
