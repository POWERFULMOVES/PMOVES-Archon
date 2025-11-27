# Secrets Entry Helper (local)

If you run the credentials-entry script mentioned in onboarding, use it this way:

1) Keep your scratch values in an ignored file (e.g., `docs/notes.md`, already in `.gitignore`).
2) Run the script to prompt for/paste values; have it write to an untracked `.env.local` or `/run/secrets/*` files for local use.
3) Immediately load the same values into GitHub Secrets using `gh secret set ...` (names listed in `docs/SECRETS_ONBOARDING.md`).
4) Delete any transient output the script creates outside untracked paths.

Required secret names (align with CI and compose): `GH_PAT_PUBLISH`, `GHCR_USERNAME`, `DOCKERHUB_PAT`, `DOCKERHUB_USERNAME`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `YOUTUBE_API_KEY`, `GOOGLE_OAUTH_CLIENT_SECRET`, `DISCORD_WEBHOOK`, plus any service-specific additions.

Security note: the script must never write to tracked files or stdout logs that end up in CI artifacts. Keep outputs confined to ignored files or `/run/secrets/*`.
