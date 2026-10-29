# SemDriftBD

**Distributed Semantic Drift Detection in Large-Scale Text Streams**

SemDriftBD detects when the meaning of text data changes over time in big-data pipelines. It introduces **WKCS** (Wasserstein–KL Composite Score), a novel metric that combines optimal transport and information-theoretic divergence to quantify semantic shift between time windows of text embeddings. When drift is detected, BERTopic-based causal attribution identifies which topics drove the change. The system runs end-to-end on Apache Spark with Kafka ingestion and a Streamlit live dashboard.

---

## Architecture

```
CC-News corpus (630,643 articles)
       │
       ▼
Kafka producer  ──►  Kafka topic (news-stream-spark)
                             │
                             ▼
              Spark Structured Streaming
              (spark-sql-kafka, micro-batches)
                             │
                             ▼
              30-day sliding windows (15-day stride)
                             │
                             ▼
              sentence-transformers embeddings
              (all-MiniLM-L6-v2, 384-dim)
                             │
                             ▼
              WKCS Drift Scoring
              ┌──────────────────────────────┐
              │  Wasserstein distance (α=0.6) │
              │  + KL divergence  (β=0.4)     │
              │  → WKCS composite score       │
              └──────────────────────────────┘
                             │
                   ┌─────────┴──────────┐
                   ▼                    ▼
         Adaptive Threshold       BERTopic Attribution
         (rolling z-score)        (per-topic WKCS, ranked)
                   │                    │
                   └─────────┬──────────┘
                             ▼
                  Streamlit Dashboard
                  (live monitor + causal drill-down)
```

---

## Key Components

### WKCS — Wasserstein–KL Composite Score

```
WKCS = α · W₂(P, Q) + β · KL(P ‖ Q)    (α=0.6, β=0.4)
```

Embeddings are projected to a shared PCA subspace before computing both distances. This combines the geometric sensitivity of Wasserstein distance with the distributional precision of KL divergence, giving a more stable score than KL divergence alone.


### BERTopic Causal Attribution

When a drift alert fires, BERTopic clusters articles in both windows into topics and computes per-topic WKCS scores. The ranked output shows which topics contributed most to the drift and by what percentage — enabling root-cause analysis in seconds.

Example — peak drift window (Pair 9, May 2017, WKCS 2.874):

| Topic keywords | Contribution | Topic WKCS |
|---|---|---|
| woman, movie, fans, adorable, film | 41.1 % | 10.23 |
| care, elderly, contact, information | 33.6 % | 8.37 |
| open, team, season, fight, league | 9.9 % | 2.46 |
| news, baseball, police, shooting, sports | 9.1 % | 2.26 |
| q1, reports, share, group, mln | 6.3 % | 1.57 |

### Adaptive Threshold Alerting

Thresholds adapt per window using a rolling baseline of the preceding N windows:

```
threshold_i = μ(WKCS_{i-N … i-1}) + z · σ(WKCS_{i-N … i-1})
```

Default: N=5, z=2.0. Alerts fire automatically when the current WKCS exceeds the threshold.

### Scalability (Spark parallel execution)

Data-size scaling (3 partitions):

| Window pairs | Tasks | Time (s) | Throughput |
|---|---|---|---|
| 5 | 15 | 4.30 | 3.5 tasks/s |
| 10 | 30 | 2.33 | 12.9 tasks/s |
| 15 | 45 | 2.46 | 18.3 tasks/s |
| 20 | 60 | 2.52 | 23.8 tasks/s |
| 25 | 75 | 2.61 | 28.8 tasks/s |
| 36 | 108 | 2.89 | **37.3 tasks/s** |

Partition scaling (36 pairs): speedup peaks at **1.46×** with 3 partitions, matching the 3 worker cores; 4 and 6 partitions are slower (0.83×, 0.86×) because scheduling overhead outweighs parallelism.

The cluster is 3 Docker containers on one physical host, so these numbers do not include real inter-machine network latency.

---

## Project Structure

```
big_data/
├── src/
│   ├── drift.py                    # WKCS metric (Wasserstein + KL)
│   ├── attribution.py              # BERTopic causal attribution
│   ├── adaptive_threshold.py       # Rolling z-score alerting
│   ├── embedder.py                 # sentence-transformers embedding
│   ├── windower.py                 # sliding window creation
│   ├── pipeline.py                 # offline batch pipeline
│   ├── compute_all_drift.py        # compute WKCS for all window pairs
│   ├── dashboard.py                # Streamlit batch dashboard
│   ├── live_dashboard.py           # Streamlit live monitor
│   ├── live_wkcs_writer.py         # real-time WKCS writer (JSON)
│   ├── kafka_producer.py           # Kafka article producer
│   ├── kafka_continuous_producer.py# continuous Kafka producer
│   ├── spark_structured_streaming.py # Spark Structured Streaming job
│   ├── spark_live_pipeline.py      # live Spark + embed + WKCS pipeline
│   ├── scalability_analysis.py     # Spark scalability benchmarks
│   ├── baselines.py                # baseline comparison methods
│   └── ...
├── data/
│   ├── drift_scores.csv            # WKCS scores for all 36 window pairs
│   ├── drift_scores_with_alerts.csv# + adaptive threshold alerts
│   ├── baseline_comparison.csv     # WKCS vs cosine/Wasserstein/KL
│   ├── scalability_results.csv     # throughput benchmarks
│   └── live_wkcs.json              # live pipeline output (runtime)
├── docker-compose.yml              # Spark cluster (1 master + 3 workers)
├── kafka-docker-compose.yml        # Kafka + Zookeeper
├── start_demo.sh                   # full demo startup script
├── requirements.txt
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.10+
- Docker Desktop
- Java 11+ (for Spark)

### Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Start infrastructure

```bash
# Spark cluster (master + 3 workers)
docker-compose up -d

# Kafka + Zookeeper
docker-compose -f kafka-docker-compose.yml up -d
```

Spark UI: http://localhost:8090  
Kafka: `localhost:9092`

---

## Usage

### Run the full demo (automated)

```bash
./start_demo.sh
```

This starts the cluster, runs the pipeline, streams articles to Kafka, and opens both dashboards.

### Step-by-step

**1. Embed the corpus and compute drift scores**

```bash
python3 src/pipeline.py               # embed + window
python3 src/compute_all_drift.py      # WKCS for all pairs
python3 src/adaptive_threshold.py     # compute alerts
```

**2. Launch the batch dashboard**

```bash
streamlit run src/dashboard.py
```

Open http://localhost:8501 to explore WKCS over time, compare baselines, and run BERTopic attribution on any window pair.

**3. Run the live pipeline**

```bash
# Terminal 1 — Kafka producer
python3 src/kafka_continuous_producer.py

# Terminal 2 — Spark Structured Streaming
python3 src/spark_structured_streaming.py

# Terminal 3 — Live WKCS writer
python3 src/live_wkcs_writer.py

# Terminal 4 — Live dashboard
streamlit run src/live_dashboard.py
```

Open http://localhost:8502 for real-time drift monitoring with adaptive alerts and causal attribution on click.

**4. Run scalability benchmarks**

```bash
python3 src/scalability_analysis.py
```

Results saved to `data/scalability_results.csv`.

---

## Results

**Data.** CC-News, 630,643 English articles from January 2017 to July 2018. Kafka and Spark ingest the full corpus; WKCS scoring runs on a stratified sample of 49,998 articles (proportional across months). That gives 37 sliding windows of 30 days (15-day stride), i.e. 36 window pairs, with 95–4,960 articles per window.

**Drift scores** (36 pairs, `data/drift_scores_with_alerts.csv`):

- Mean WKCS 0.622; peak 2.874 (Pair 9, May 2017); minimum 0.139 (Pair 36)
- 7 alerts at the rolling µ + 2σ threshold (w = 5)

**Detection** against 6 reference drift events, labelled independently by two authors:

| Method | Precision | Recall | F1 |
|---|---|---|---|
| Cosine distance | 0.250 | 0.167 | 0.200 |
| MMD (alibi-detect) | 0.250 | 0.167 | 0.200 |
| Wasserstein only | 0.500 | 0.333 | 0.400 |
| KL only | 0.667 | 0.667 | 0.667 |
| **WKCS (ours)** | **0.667** | **0.667** | **0.667** |

WKCS matches KL-only on detection and is far more stable: its coefficient of variation across the 36 pairs is **0.507**, against 0.799 for KL-dominant weighting, a 37% reduction (`data/weight_sensitivity.csv`). The α = 0.6, β = 0.4 weights were picked to minimise this variance, not to maximise F1.

**Throughput:** 37.3 tasks/s and a 1.46× parallel speedup on 3 Spark workers (see Scalability above).

---

## Tech Stack

| Component | Technology |
|---|---|
| Stream ingestion | Apache Kafka |
| Distributed processing | Apache Spark 3.5.3 (PySpark) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Drift metric | WKCS (custom — Wasserstein + KL) |
| Optimal transport | Python Optimal Transport (POT) |
| Topic modelling | BERTopic + HDBSCAN + UMAP |
| Storage | Delta Lake 3.2.0 |
| Dashboard | Streamlit + Plotly |

---

## Citation

If you use SemDriftBD in your research, please cite:

```bibtex
@inproceedings{bandi2026semdriftbd,
  title     = {{SemDriftBD}: Distributed Semantic Drift Detection in Large-Scale Text Streams},
  author    = {Bandi, Saivikas and Bypuneni, Chaitanya Krishna and J, Jayasurya and {Mallikharjuna Rao K}},
  booktitle = {Proceedings of the International Conference on Software, Telecommunications and Computer Networks (SoftCOM)},
  address   = {Split, Croatia},
  year      = {2026},
  publisher = {IEEE},
  note      = {To appear}
}
```

Code: https://github.com/bandisaivikas/big_data

---

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md). Report security problems privately as described in [SECURITY.md](SECURITY.md).

## License

Released under the [MIT License](LICENSE).
