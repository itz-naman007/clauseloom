# Demo walkthrough

Use a fictional sample rather than a real contract. Start the app with
`docker compose up --build -d`, wait for `/api/ready` to return 200, and open
http://localhost:8080.

For a short presentation, complete a sample review beforehand. CPU inference
can take several minutes, so allow extra time if you want to show a fresh run.

1. **Start with the contract.** Choose the rental sample and show how clause
   results arrive as processing continues. Explain that rules find supported
   patterns and the local model supplies explanations.
2. **Read a finding in context.** Open the deposit finding, follow its clause
   link and compare the explanation with the highlighted source. Show any
   rule-only label so the audience can distinguish the fallback from AI output.
3. **Explain the score.** Show the formula and key terms. The score summarizes
   matched flags; it is not a legal verdict or a guarantee of safety.
4. **Prepare a question.** Use **Copy negotiation message** to show how a finding
   becomes something the user can ask the other party. The app copies text; it
   does not send a message.
5. **Export and finish.** Download the PDF, then use **Delete my data now** to
   clear the active review. Downloaded copies remain on the user's device.

If time permits, try Hindi explanations or the freelance sample. When discussing
privacy, say where the app is hosted: processing runs on that server, which may
be a local machine or a cloud host.
