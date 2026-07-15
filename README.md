# NewsScraper

Python backend for scraping news, assigning sentiment and political framing,
summarizing articles, and serving them to the `news-dashboard` frontend.

## Local refresh

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
NEWS_SUMMARY_FAST=1 NEWS_SENTIMENT_FAST=1 MAX_ARTICLES_PER_SITE=5 .venv/bin/python sentiment_analysis_pipeline.py
.venv/bin/python sentiment_api.py
```

Without `MONGO_URL`, the pipeline writes `sentiment_results.json` and the Flask API serves from that file. With `MONGO_URL`, articles are upserted into MongoDB.

## API

```bash
python sentiment_api.py
```

Endpoints:

- `GET /health`
- `GET /articles?offset=0&sort=desc&keyword=&category=`
- `GET /articles/<id>`

Each article includes a bias meter payload:

- `bias`: `left`, `centrist`, or `right`
- `bias_score`: normalized from `-1` (left) to `1` (right)
- `bias_confidence`: confidence in the designation from `0` to `1`
- `bias_method`: whether the full article or a legacy summary fallback was used
- `bias_signals`: up to five framing phrases that influenced the result

The pipeline computes the designation from the complete fetched article. Weak or
balanced evidence is marked centrist rather than forcing a directional lean.

Set `GEMINI_API_KEY` to use Gemini structured-output analysis. The production
default is `gemini-3.1-flash-lite`, chosen for reliable, low-cost scheduled
classification. Set `GEMINI_BIAS_MODEL=gemini-3.5-flash` when maximum nuance is
more important than throughput. Without a key—or when Gemini fails—the pipeline
uses the local framing scorer as a fallback.

To upgrade existing MongoDB records using their complete article text:

```bash
.venv/bin/python backfill_bias.py --dry-run --limit 10
.venv/bin/python backfill_bias.py
```

The scheduled scraper also upgrades 30 legacy records per run, staying within
the free-tier request budget while the historical archive migrates gradually.

## No-cost live setup

Recommended setup:

1. Host MongoDB on an Atlas Free cluster.
2. Host the Flask API as a small free web service, or keep the existing Render service.
3. Run the scraper on GitHub Actions with `.github/workflows/scrape-news.yml`.

Set these repository secrets/vars:

- Secret: `MONGO_URL`
- Variable: `DB_NAME` defaults to `news_scraper`
- Variable: `COLLECTION_NAME` defaults to `articles`

The scheduled workflow runs every six hours and can also be triggered manually from the Actions tab. This replaces the old Celery worker/Redis setup so there is no always-on background process to pay for.

## Full ML mode

The lightweight path can use `NEWS_SUMMARY_FAST=1` to avoid downloading a large
summarization model and `NEWS_SENTIMENT_FAST=1` to use deterministic sentiment
rules only. For stronger sentiment grouping, leave `NEWS_SENTIMENT_FAST` unset
after installing:

```bash
.venv/bin/pip install -r requirements-ml.txt
```

Then run without `NEWS_PIPELINE_FAST`. Full model mode defaults to
`cardiffnlp/twitter-roberta-base-sentiment-latest`, a three-label sentiment
model, because the old binary-only model could not naturally separate neutral
news from positive/negative news.
