# Two-minute ClauseLoom demo

Before starting: run `docker compose up --build -d`, wait for `/api/ready` to return 200, and open http://localhost:8080. Warm the model with one sample run if CPU startup is slow.

**0:00–0:20 — The problem.** “Before signing, most people need to understand the fine print. ClauseLoom explains a contract locally, without sending it to an external AI provider.” Point out the privacy strip and informational-only disclaimer.

**0:20–0:45 — Try a sample.** Click **Rental agreement**. Show clauses arriving progressively while the local small model works. Explain that rules detect flags; the model explains them. Rule-only results are visibly labeled when explanations fail validation.

**0:45–1:10 — Make the score understandable.** Show the review score, its formula, and key terms. Open the security-deposit flag. The sample deposit is three months of rent and non-refundable; thresholds vary by jurisdiction and do not establish legality.

**1:10–1:30 — Act on the information.** Click the flag's clause link to see highlighted original text beside the explanation. Click **Copy negotiation message** to prepare a concrete question. Nothing is sent to the other party.

**1:30–1:45 — Take away a report.** Download the PDF and show its source clauses, flags, questions and disclaimer. Explain that downloaded copies remain on the user's device.

**1:45–2:00 — Close the privacy loop.** Click **Delete my data now**. Show the cleared view. Mention automatic session expiry, Hindi explanations, and the freelance sample as a second use case.

CPU timing varies. If a live run takes longer than two minutes, use a warmed sample and show the evaluation honestly; do not describe rule-only output as generated AI text.
