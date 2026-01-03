To publish branch and open a PR:

1. Add remote (if not already present):
   git remote add origin <git-repo-url>
2. Push branch:
   git push -u origin feat/schema-confidence
3. Open a Pull Request on your Git provider (GitHub/GitLab) from `feat/schema-confidence` into your main branch.

Notes:
- CI should run pytest on PRs once a workflow is configured (`.github/workflows/ci.yml`).
- If you want, I can create a GH Actions workflow in the repo next (task 3).
