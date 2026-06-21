Resume Integrity Checker

A Python tool that reviews a resume for internal inconsistencies and unverifiable
claims, and produces a neutral checklist of items for a human to verify. Built with
the Claude API.

It does not accuse anyone of anything. It does not score fit. It does not screen
identity documents. It surfaces "things worth confirming" — and a human decides.

What It Does


Reads a resume (PDF or text)
Asks Claude to find internal inconsistencies and unconfirmable claims, such as:

Timeline math that doesn't add up (years of experience exceeding the span since
graduation; overlapping full-time roles)
Credential or certification claims with no issuing body or identifier
Title or scope claims that are vague or unusually senior for the stated tenure



Returns a checklist: each item has a category, severity, a neutral observation,
and the concrete thing a human should verify
Writes it to a CSV for the recruiter to work through during reference checks


Why It's Built This Way

Verify, don't accuse. An LLM's judgment about whether someone is being truthful is
probabilistic and can be wrong or biased. Treating that judgment as an accusation would
be unfair and indefensible. So every output is framed as a neutral item to verify — the
tool hands a recruiter a better checklist, not a verdict.

A neutrality guard in code, not just in the prompt. The prompt forbids words like
"fraud," "lie," and "fake" — but prompts can be ignored. The test suite includes a
guard that fails if accusatory language ever appears in the output, so the neutrality
commitment is enforced, not just requested. See tests/.

Human-in-the-loop by design. Nothing is rejected, scored, or decided by the system.
It produces a checklist a person uses.

Architecture

#mermaid-rh33-r1 { font-family: "Anthropic Sans", system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 16px; fill: rgb(25, 25, 25); }
#mermaid-rh33-r1 .edge-animation-slow { stroke-dashoffset: 900; animation: 50s linear 0s infinite normal none running dash; stroke-linecap: round; stroke-dasharray: 9, 5 !important; }
#mermaid-rh33-r1 .edge-animation-fast { stroke-dashoffset: 900; animation: 20s linear 0s infinite normal none running dash; stroke-linecap: round; stroke-dasharray: 9, 5 !important; }
#mermaid-rh33-r1 .error-icon { fill: rgb(204, 120, 92); }
#mermaid-rh33-r1 .error-text { fill: rgb(51, 135, 163); stroke: rgb(51, 135, 163); }
#mermaid-rh33-r1 .edge-thickness-normal { stroke-width: 1px; }
#mermaid-rh33-r1 .edge-thickness-thick { stroke-width: 3.5px; }
#mermaid-rh33-r1 .edge-pattern-solid { stroke-dasharray: 0; }
#mermaid-rh33-r1 .edge-thickness-invisible { stroke-width: 0; fill: none; }
#mermaid-rh33-r1 .edge-pattern-dashed { stroke-dasharray: 3; }
#mermaid-rh33-r1 .edge-pattern-dotted { stroke-dasharray: 2; }
#mermaid-rh33-r1 .marker { fill: rgb(145, 145, 141); stroke: rgb(145, 145, 141); }
#mermaid-rh33-r1 .marker.cross { stroke: rgb(145, 145, 141); }
#mermaid-rh33-r1 svg { font-family: "Anthropic Sans", system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 16px; }
#mermaid-rh33-r1 p { margin: 0px; }
#mermaid-rh33-r1 .label { font-family: "Anthropic Sans", system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: rgb(25, 25, 25); }
#mermaid-rh33-r1 .cluster-label text { fill: rgb(51, 135, 163); }
#mermaid-rh33-r1 .cluster-label span { color: rgb(51, 135, 163); }
#mermaid-rh33-r1 .cluster-label span p { background-color: transparent; }
#mermaid-rh33-r1 .label text, #mermaid-rh33-r1 span { fill: rgb(25, 25, 25); color: rgb(25, 25, 25); }
#mermaid-rh33-r1 .node rect, #mermaid-rh33-r1 .node circle, #mermaid-rh33-r1 .node ellipse, #mermaid-rh33-r1 .node polygon, #mermaid-rh33-r1 .node path { fill: rgb(240, 240, 235); stroke: rgb(217, 216, 213); stroke-width: 1px; }
#mermaid-rh33-r1 .rough-node .label text, #mermaid-rh33-r1 .node .label text, #mermaid-rh33-r1 .image-shape .label, #mermaid-rh33-r1 .icon-shape .label { text-anchor: middle; }
#mermaid-rh33-r1 .node .katex path { fill: rgb(0, 0, 0); stroke: rgb(0, 0, 0); stroke-width: 1px; }
#mermaid-rh33-r1 .rough-node .label, #mermaid-rh33-r1 .node .label, #mermaid-rh33-r1 .image-shape .label, #mermaid-rh33-r1 .icon-shape .label { text-align: center; }
#mermaid-rh33-r1 .node.clickable { cursor: pointer; }
#mermaid-rh33-r1 .root .anchor path { stroke-width: 0; stroke: rgb(145, 145, 141); fill: rgb(145, 145, 141) !important; }
#mermaid-rh33-r1 .arrowheadPath { fill: rgb(11, 11, 11); }
#mermaid-rh33-r1 .edgePath .path { stroke: rgb(145, 145, 141); stroke-width: 1px; }
#mermaid-rh33-r1 .flowchart-link { stroke: rgb(145, 145, 141); fill: none; }
#mermaid-rh33-r1 .edgeLabel { background-color: rgb(245, 230, 216); text-align: center; }
#mermaid-rh33-r1 .edgeLabel p { background-color: rgb(245, 230, 216); }
#mermaid-rh33-r1 .edgeLabel rect { opacity: 0.5; background-color: rgb(245, 230, 216); fill: rgb(245, 230, 216); }
#mermaid-rh33-r1 .labelBkg { background-color: rgba(245, 230, 216, 0.5); }
#mermaid-rh33-r1 .cluster rect { fill: rgb(204, 120, 92); stroke: rgb(138, 115, 107); stroke-width: 1px; }
#mermaid-rh33-r1 .cluster text { fill: rgb(51, 135, 163); }
#mermaid-rh33-r1 .cluster span { color: rgb(51, 135, 163); }
#mermaid-rh33-r1 div.mermaidTooltip { position: absolute; text-align: center; max-width: 200px; padding: 2px; font-family: "Anthropic Sans", system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 12px; background: rgb(204, 120, 92); border: 1px solid rgb(138, 115, 107); border-radius: 2px; pointer-events: none; z-index: 100; }
#mermaid-rh33-r1 .flowchartTitleText { text-anchor: middle; font-size: 18px; fill: rgb(25, 25, 25); }
#mermaid-rh33-r1 rect.text { fill: none; stroke-width: 0; }
#mermaid-rh33-r1 .icon-shape, #mermaid-rh33-r1 .image-shape { background-color: rgb(245, 230, 216); text-align: center; }
#mermaid-rh33-r1 .icon-shape p, #mermaid-rh33-r1 .image-shape p { background-color: rgb(245, 230, 216); padding: 2px; }
#mermaid-rh33-r1 .icon-shape .label rect, #mermaid-rh33-r1 .image-shape .label rect { opacity: 0.5; background-color: rgb(245, 230, 216); fill: rgb(245, 230, 216); }
#mermaid-rh33-r1 .label-icon { display: inline-block; height: 1em; overflow: visible; vertical-align: -0.125em; }
#mermaid-rh33-r1 .node .label-icon path { fill: currentcolor; stroke: revert; stroke-width: revert; }
#mermaid-rh33-r1 .node .neo-node { stroke: rgb(217, 216, 213); }
#mermaid-rh33-r1 [data-look="neo"].node rect, #mermaid-rh33-r1 [data-look="neo"].cluster rect, #mermaid-rh33-r1 [data-look="neo"].node polygon { stroke: url("#mermaid-rh33-r1-gradient"); filter: drop-shadow(rgb(185, 185, 185) 1px 2px 2px); }
#mermaid-rh33-r1 [data-look="neo"].node path { stroke: url("#mermaid-rh33-r1-gradient"); stroke-width: 1px; }
#mermaid-rh33-r1 [data-look="neo"].node .outer-path { filter: drop-shadow(rgb(185, 185, 185) 1px 2px 2px); }
#mermaid-rh33-r1 [data-look="neo"].node .neo-line path { stroke: rgb(217, 216, 213); filter: none; }
#mermaid-rh33-r1 [data-look="neo"].node circle { stroke: url("#mermaid-rh33-r1-gradient"); filter: drop-shadow(rgb(185, 185, 185) 1px 2px 2px); }
#mermaid-rh33-r1 [data-look="neo"].node circle .state-start { fill: rgb(0, 0, 0); }
#mermaid-rh33-r1 [data-look="neo"].icon-shape .icon { fill: url("#mermaid-rh33-r1-gradient"); filter: drop-shadow(rgb(185, 185, 185) 1px 2px 2px); }
#mermaid-rh33-r1 [data-look="neo"].icon-shape .icon-neo path { stroke: url("#mermaid-rh33-r1-gradient"); filter: drop-shadow(rgb(185, 185, 185) 1px 2px 2px); }
#mermaid-rh33-r1 :root { --mermaid-font-family: "Anthropic Sans",system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }ResumeIntegrity PromptClaude APIJSON ReportNeutrality GuardVerification Checklist

Setup


Clone or download this repo
Install dependencies: pip install -r requirements.txt
Copy .env.example to .env and add your Anthropic API key
Drop resumes in data/resumes/
Run: python src/integrity_checker.py


Scope and Limits

This tool flags items to verify based on what's inside a single resume. It cannot
confirm or deny any claim — only a human checking references, credentials, or records
can do that. A flag means "worth confirming," never "this is false." It is a companion
to, not a replacement for, proper background and reference checks.

Relationship to My Other Tools


AI Resume Screener — scores
candidate fit (separate concern, separate tool)
IDV Fraud Detection —
screens identity documents for manipulation (separate concern, separate tool)


Each tool does one thing well. This one builds a verification checklist.

Status

Built as a standalone tool. This public version uses synthetic example resumes; no real
candidate information is included.
