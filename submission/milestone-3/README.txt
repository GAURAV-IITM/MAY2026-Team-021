MAY2026-Team-021 - Milestone 3 Submission
==========================================

Required upload files
---------------------
1. MAY2026-Team-021-Milestone-3-Report.pdf
   Consolidated Sprint 1 report with nine API test cases, pytest function
   snapshots, one required mismatch, user feedback, quality evidence, and the
   next-sprint plan.

2. openapi.yaml
   Swagger/OpenAPI 3.1 documentation for all 74 implemented API operations.
   Each operation includes a description, user-story mapping, and documented
   error responses.

3. MAY2026-Team-021-Backend-Code.zip
   Backend application, database migrations, API tests, scripts, dependency
   manifest, example environment file, backend documentation, CI workflow,
   and the submitted API contract.

Supporting files
----------------
- MAY2026-Team-021-Milestone-3-Report.docx: editable report source copy.
- pytest-results.txt: output from the final backend test run.
- SHA256SUMS.txt: checksums for submission integrity.

Security and reproducibility
----------------------------
The backend ZIP excludes .env, virtual environments, caches, bytecode, local
databases, and secrets. Create backend/.env from backend/.env.example before
running the application. Full setup and validation commands are included in
the report and backend/README.md.

Final verification
------------------
- Backend tests: 133 passed.
- OpenAPI operations: 74.
- Missing operation descriptions: 0.
- Missing user-story mappings: 0.
- Missing documented error responses: 0.
