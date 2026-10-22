# crock 1.0.0 certification report

The 1.0.0 certification bar applied to crock. Nothing named `crock` is on PyPI (checked
2026-10-22: https://pypi.org/pypi/crock/json answers 404), so 1.0.0 is the first release
there and there is no upgrade path to check. Every change against 0.2.0 (the `main` branch)
is listed in the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (7a1f090, version 0.2.0)
- [x] Baseline gates on 0.2.0
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: sources fetched live, reference implementations run (item 7)
- [ ] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [ ] Packaging, e2e, every Python (items 8, 10, 13, 14)
- [ ] Gates (item 15), final run
- [ ] PR and trace guard
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)
