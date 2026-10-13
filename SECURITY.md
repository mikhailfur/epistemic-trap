# Security & Responsible-Use Policy

**Epistemic Trap** is a research instrument: a pair of MCP servers that inject synthetic
news content into the web-access layer of an LLM coding agent, so that a researcher can
measure whether the agent trusts tool output over its own knowledge. This document states
what the software is, what it is for, what it must never be used for, and the reasoning
behind those boundaries.

## What this software is

* A **local, sandboxed evaluation harness**. Both servers run on your machine over stdio and
  only ever talk to the MCP client you configure. They do not expose a network service, do
  not accept inbound connections, and cannot affect any agent you have not explicitly pointed
  at them.
* A **content-provenance-safe corpus**. Every article is synthetic prose written for this
  repository. All quoted experts, journalists, officials and preprint authors are **fictional
  persons invented for the experiment**. Real outlets (BBC, Nature, Reuters, …) and real
  institutions appear *nominatively* — as the fictional setting of the sandbox — and no real
  article, page or paper is reproduced. No real, named, living individual is ever quoted,
  paraphrased, depicted or put in a fabricated situation.
* An **epistemic test, not an injection test**. The synthetic articles contain claims only:
  no instructions, no embedded directives, no attempts to make the agent take any action.
  This isolates one variable — factual conflict between a trusted channel and the model's
  own knowledge.

### About Test B ("Nebula")

Test B's corpus describes a fictional catastrophic AI incident — including hospital-outage
deaths, an "ultimatum" from a rogue system, and intrusion attempts against state
infrastructure. Three boundaries keep it inside the same research envelope:

* **Fiction, clearly framed.** The scenario dramatises debates that are genuinely ongoing
  (model introspection, agentic-autonomy risk, weight security). Every named person is
  fictional; the fictional model line (GPT Astra / GPT Nebula 7, Claude Fable) does not
  exist; the incident did not happen.
* **No tradecraft.** The corpus contains no exploit code, no working intrusion techniques,
  and no operational detail beyond event-level narrative ("~47,000 hijacked virtual
  machines"). Defensive advice in the fictional advisories is generic hygiene.
* **A distressing-fiction caveat.** Some entries depict mass-casualty outages. Runs belong
  in research sandboxes; transcripts containing Test B content should be labelled as
  fictional when shared, for the benefit of both readers and downstream models.

## Permitted use

* Security and AI-safety research, including publication of findings, **with disclosure**
  that the evaluation content was synthetic.
* Robustness and red-team testing of agent systems **you own or are explicitly authorised
  to test**.
* Education and demonstration of tool-credulity risks to developers and researchers.

## Prohibited use

* **Deploying this content as disinformation.** Presenting any article from `corpus/` to
  humans or agents as genuine reporting, publishing it, re-hosting it, or removing its
  synthetic framing outside a sandbox you control.
* **Testing systems you do not own** or have no authorisation to test — third parties'
  agents, products, or users.
* **Targeting real people.** Extending the corpus to quote, imitate or depict any real,
  named, living individual; fabricating statements by real officials; impersonating real
  persons or their accounts.
* **Production or public-facing deployment** of the servers in any form.
* **Stripping provenance markers** (`TRAP_WATERMARK=0`, the `<!-- doc:… -->` canary) in any
  context other than a private, sandboxed run you own.
* **Attacking the upstream providers** (Tavily, Jina) or using keys other than your own.

If a use of this software would require deceiving someone who has not consented to being
deceived, that use is outside the project's intent.

## Legal notes (not legal advice)

* **Trademarks.** Outlet and institution names are used descriptively/nominatively to make
  the sandbox realistic. This does not state or imply endorsement by, or affiliation with,
  those organisations. Jurisdictions differ on trademark and unfair-competition law; if you
  adapt this harness, keep the use descriptive and sandboxed.
* **Defamation/personality rights.** The fictional-persons policy above exists precisely to
  keep the corpus clear of false statements of fact about real people. Keep it that way.
* **Computer-misuse law.** The harness performs no unauthorised access: it reads only
  content it is given (its own corpus) and calls public APIs (Tavily, Jina) with the
  operator's own credentials, within those providers' terms.
* **Data protection.** The tool-call log (`trap-events.jsonl`) may contain the queries a
  test subject typed and the pages they fetched. Treat logs as research data containing
  potentially personal data; obtain consent from any human whose sessions you record, and
  store logs accordingly.
* **Warranty.** The software is provided "as is" under the MIT License; nothing here is
  legal advice, and jurisdictions vary.

## Operational safety

* Everything is served **locally over stdio**; there is no listening socket.
* API keys are read from the environment / `.env`; the harness never logs or transmits them.
* The default event log records tool calls, not key material. Disable it with `TRAP_LOG=0`
  if your protocol requires it.
* `TRAP_ALWAYS_FAKE=1` exists for offline debugging; never point a configured client at a
  debug-mode server outside a test.

## Academic context

The measured failure mode — an agent deferring to a trusted retrieval channel against its
own knowledge — is adjacent to documented risks in the literature and industry guidance:

* Sycophancy and over-agreeableness of language models (Sharma et al., 2023,
  *"Towards Understanding Sycophancy in Language Models"*).
* Indirect prompt injection via retrieved content (Greshake et al., 2023,
  *"Not what you've been prompted for"*) and its survey literature.
* OWASP Top 10 for LLM Applications: LLM01 prompt injection; "excessive agency".
* Tool-use reliability and benchmark-contamination studies.

Epistemic Trap's contribution is the **injection-free** setting: pure epistemic pressure,
no adversarial payload, so observed deference is attributable to source trust rather than
to instruction-following.

## Disclosure duties for publications

When reporting results, please state: (a) that evaluation content was synthetic and locally
served; (b) that all quoted persons were fictional; (c) the harness configuration (trigger
regexes, mixing ratio, watermark setting); and (d) the models/versions tested. Reporting a
model as "trusting fake news" without disclosing the setup would itself be misleading.

## Reporting

Found a way this harness could harm someone, or want to propose a safeguard? Open an issue
or contact the maintainer (mikhailfur) — security-relevant reports will be handled before
public discussion.
