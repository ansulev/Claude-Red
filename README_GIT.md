# Git Workflow — ansulev/Claude-Red

## Remotes

| Remote   | URL                                        | Purpose              |
|----------|--------------------------------------------|----------------------|
| origin   | github.com/ansulev/Claude-Red              | This fork — push here |
| upstream | github.com/SnailSploit/Claude-Red          | Source — pull only   |

## Sync upstream → this fork

```bash
git fetch upstream
git merge upstream/main
python convert_skills.py       # regenerate skills-converted/ and skills-zip/
git push origin main
```

Conflicts only happen if upstream modifies `convert_skills.py`.
Your changes live in those 4 commits on top — they never touch `Skills/`.

## Your changes vs upstream

| File               | What changed                                      |
|--------------------|---------------------------------------------------|
| convert_skills.py  | Path("skills") → Path("Skills") (Linux case fix)  |
| convert_skills.py  | All Spanish strings/comments → English            |
| convert_skills.py  | Bare f-strings and unused yaml import fixed        |

Not submitted upstream — unclear if Spanish was intentional on their end.

## Day-to-day

```bash
# Push your changes
git push origin main

# Check what upstream has that you don't
git fetch upstream
git log HEAD..upstream/main --oneline

# After merging, always regenerate
python convert_skills.py
```
