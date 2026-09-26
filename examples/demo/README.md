# Offline fixtures — not live research

All company names, domains, documents, figures and model outputs here are synthetic.
There are no downloaded articles or paid API recordings. These original fixture texts
and data are dedicated under CC0-1.0. No claim is made about a real company.

`supported.json`: attributed company revenue, without independent corroboration.
`sparse.json`: explicit missing retention; a zero would be incorrect.
`conflicted.json`: two incompatible revenue assertions from the same company origin.
`refresh.json`: two preserved source/claim versions for different reporting years.
`search.json`: recorded demo search returning a company absent from existing fixtures.
`model.json`: exact deterministic classification response.

Evidence files include source rights, exact passages, content hashes and developer
evaluation expectations. Provider recordings use the same request/result contracts
as future live adapters, but are demo-only and never call a network service.
Unknown inputs abstain; fixture mode cannot research arbitrary companies.

Run the fixture tests from the repository root:

```sh
.venv/bin/python -m pytest -c backend/pyproject.toml backend/tests/test_fixtures.py
```

This is a contract/fixture demonstration, not the future interactive product demo.
