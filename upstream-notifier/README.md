# Upstream notifier

`notify-skill.yml` tells `abhi245y/ola-dev-skill` when an upstream repo changes, so the skill re-syncs and releases without waiting for the 6-hourly schedule. It is a template: the lead copies it into the upstream repos.

Setup, per upstream repo (`ola-dash-sdk` and `ola-can-reference`):

1. Copy the file to `.github/workflows/notify-skill.yml`.
2. Set `EVENT_TYPE` at the top to `sdk-updated` (SDK) or `can-updated` (CAN). Keep the matching path list and delete the other.
3. Add the secret `SKILL_DISPATCH_TOKEN` (the same fine-grained PAT in both repos). See the README of the skill, "Maintainer setup".

Without the secret the job prints a notice and exits 0, and the skill still syncs on its schedule.
