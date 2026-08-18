# The prompt

Paste into a fresh **Claude Code** session — after you've created a Google Cloud account, claimed the
**$300 trial**, added a **billing card**, and installed the **gcloud CLI** + **Python 3**.

> I want Claude Code to generate AI videos with Google **Veo 3** on **Vertex AI**, billed to my Google
> Cloud **$300 credit**. I've already created a Google Cloud account, claimed the $300 trial, and added
> a billing card. Clone `https://github.com/Itsme23476/claude-code-veo-video` into my home folder and set it up:
>
> 1. Run `./connect-vertex.sh` — I'll approve the Google sign-in in the browser (this authorizes you to
>    create my project and enable Vertex AI).
> 2. Run `./install.sh` to install the `veo-video` skill.
> 3. **Ask me whether I also want the optional Higgsfield-style web interface.** If yes, run
>    `./webapp/start.sh` (a local page to generate videos with a visual UI); if no, skip it.
>
> Then **ask me what video I want**, turn it into a vivid cinematic prompt, and generate it with
> `veo-3.1-fast-generate-001` — **tell me the rough cost first** (Veo bills per second). Save the `.mp4`
> and show me where it is.
>
> Rules: use **Vertex + my ADC login** (never an API key, never the AI Studio endpoint), and **never
> enter my payment info**. Work autonomously; pause only for the browser sign-in and my video idea.
