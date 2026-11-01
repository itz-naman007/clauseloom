# Verification record

Checked locally on 1 November 2026. The main application retains the original
React UI and FastAPI/Ollama backend.

- Backend: 98 passing tests, Python lint passed.
- Frontend: production build, type check and unit test passed.
- Runtime dependency audit: no known Python or npm dependency advisories reported
  in the audited main-app dependency sets.
- Docker: standard and single-container images built successfully.
- Bundled CPU model: rental sample streamed 11 clauses with 14 flags and 7 grounded
  AI explanations in 111.5 seconds at 2 CPUs / 4 GB. PDF export and deletion passed.
- Live PDF/DOCX/PNG/JPEG upload checks passed, including real OCR.
- Browser: original UI rendered results, search and theme controls worked,
  privacy dialog supported keyboard dismissal, PDF downloaded and review deletion
  reset the UI. A 390px mobile layout had no horizontal overflow.
- Mixed English/Hindi report glyphs were visually verified after the font fix.

The GitHub Actions workflow has not yet run on a remote repository. Container OS
advisories, anonymous-use limits, hosted proxy behavior and representative legal
accuracy still need assessment before a broad production launch. See
[deployment readiness](deployment-readiness.md) for the detailed findings and limits of this verification.
