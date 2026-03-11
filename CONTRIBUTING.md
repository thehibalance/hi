# Contributing to HI.

Thanks for wanting to help find the HI balance. Here's how to contribute.

## Ways to Contribute

### Score a Company
Follow the [methodology spec](docs/methodology/) to score a company. Submit a PR adding the company to `human-edge/lib/seed-data.js` with all five dimension scores and notes explaining your sources.

### Add a Data Source
Write a Python pipeline that outputs JSON in the signal format used by `scoring_engine.py`. See `sec_edgar_pipeline.py` as an example. Target sources: EPA ECHO, BLS, CDP, job boards, Glassdoor.

### Improve the Extension
Bug fixes, UI improvements, accessibility, dark mode tweaks, new badge layouts. The extension is pure JavaScript — no build step, no framework.

### Report Score Issues
Found a score that seems wrong? Open an issue with:
- Company name
- Which dimension(s) seem off
- Your evidence (links to public data)

## Development Setup

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/hi.git
cd hi

# Copy config
cp config.example.py config.py
# Edit config.py with your SEC EDGAR email

# Load extension in Chrome
# chrome://extensions → Developer mode → Load unpacked → human-edge/

# Run the API (optional)
pip install flask flask-cors
cd pipeline
python api_server.py
```

## Rules

1. **The edge node stays AI-free.** No ML, no inference, no neural networks in anything under `human-edge/`. This is a core architectural and philosophical commitment.

2. **Scores must be sourced.** Every score in the seed database needs notes explaining where the data came from. No vibes-based scoring.

3. **Be balanced, not adversarial.** HI. is pro-balance, not anti-AI. Contributions should reflect this in tone and approach.

4. **Follow the spec.** Scores must conform to the HUMAN Grade Methodology Spec v1.0. If you think the spec should change, open an issue to discuss.

## Code Style

- JavaScript: no framework, no build step, vanilla JS
- Python: stdlib where possible, minimal dependencies
- Comments: explain *why*, not *what*

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (AGPL-3.0 for code, Apache 2.0 for methodology, CC BY-SA 4.0 for data).
