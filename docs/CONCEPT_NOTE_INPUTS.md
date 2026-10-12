# Concept note inputs

- **Problem:** forged deeds, mismatched registration/mutation records, and repeat sales create citizen risk in Bangladesh. This prototype uses no real records.
- **Solution:** each synthetic deed receives a canonical hash, office signature, QR-ready verification URL, and append-only hash-chain entry.
- **Architecture:** deterministic generator, SQLite, FastAPI/Jinja UI, cryptographic service, rule-based fraud service, bilingual reports.
- **Features:** authentic/altered/not-found verification, tamper demo, double-sale/area/rapid-transfer/no-mutation flags, Plot Safety Report.
- **Rollout:** pilot one upazila, then district, then national integration after formal approvals and security/privacy work.
- **Limitations:** all statuses and rules are simulated; no legal conclusion, real government integration, or machine learning.
