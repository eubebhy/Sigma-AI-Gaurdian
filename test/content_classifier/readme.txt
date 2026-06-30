test/content_classifier

Structure
- `test_all_classifiers.py`: test runner for rule-based, local AI, and cloud AI flags.
- `game.txt`: inputs that should be classified as `Game`.
- `porn.txt`: inputs that should be classified as `Pornography`.
- `gore.txt`: inputs that should be classified as `Gore`.
- `safe.txt`: inputs that should be classified as `Unknown`.

Case format
- One test case per line.
- Full-line comments and inline comments use `#`.
- The parser ignores everything after `#` on each line.
- Keep active case text free of `#` characters.

Flags
- `-r`: run rule-based engine tests.
- `-l`: run local AI tests.
- `-c`: cloud AI placeholder in this harness.
- `-f` / `--show-failures`: show failed cases and failure details.
- `-m` / `--mode`: select `all`, `game`, `porn`, or `gore`.
- `-p` / `--pick-mode`: choose `sequential` or `random` case picking.
- `-n` / `--sample-size`: max cases to take from each selected theme.

Output
- Pass cases are always printed.
- Fail cases are hidden by default unless `--show-failures` is enabled.
- Final summary shows total, passed, failed, and per-theme breakdown for the sampled cases.
