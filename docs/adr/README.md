# Architecture Decision Records

ADR เป็นบันทึกเหตุผลของการตัดสินใจที่เปลี่ยนยาก ห้ามแก้ Decision ย้อนหลัง; ถ้าทิศทางเปลี่ยนให้สร้าง ADR ใหม่และระบุ superseded-by

| ADR | Title | Status | Summary | Superseded by |
|---|---|---|---|---|
| [001](001-runrecord-contract.md) | RunRecord contract | Accepted | Event log เป็น source of truth | — |
| [002](002-respawn-checkpoint.md) | Respawn checkpoint | Accepted | Respawn ที่ checkpoint แทนการจบทันที | 010 (บางส่วน) |
| [003](003-rule-based-evaluation.md) | Rule-based evaluation | Accepted | Deterministic rule-based scoring | 011 (ขยายผล) |
| [004](004-https-hmac-no-aes.md) | HTTPS + HMAC | Accepted · P2 | Sync integrity โดยไม่ซ้อน AES | — |
| [005](005-sqlite-dev-postgres-deploy.md) | Backend database split | Accepted · P2 | SQLite dev/PostgreSQL deploy | — |
| [006](006-server-authoritative-scoring.md) | Server scoring | Accepted · P2 | Server คำนวณผลจาก event log | — |
| [007](007-flask-socketio-realtime.md) | Realtime dashboard | Accepted · P2 | Flask-SocketIO dashboard | — |
| [008](008-docker-compose-backend.md) | Docker backend | Accepted · P2 | Docker Compose สำหรับ backend | — |
| [009](009-dual-meter-model.md) | Dual-meter model | Accepted | Pure heat/anger state model | — |
| [010](010-health-respawn-state-model.md) | Health/respawn model | Accepted | Hearts, respawn, permanent Game Over | — |
| [011](011-learning-evaluation-pipeline.md) | Learning evaluation | Accepted | Scoring และ DAG projection pipeline | — |
| [012](012-runresult-contract.md) | RunResult contract | Accepted | Recomputable result read model | — |
| [013](013-junction-gameplay-integration.md) | Junction integration | Accepted | Ownership boundary ของ Y-Junction | — |
| [014](014-decision-simulation-pause.md) | Decision pause | Accepted | Pause simulation แต่ render ต่อ | — |
| [015](015-respawn-grace-lifecycle.md) | Respawn grace | Accepted | RunMetrics เป็นเจ้าของ grace lifecycle | — |
| [016](ADR-016-gameplay-application-boundary.md) | Gameplay application boundary | Accepted | Controller, single writer, immutable snapshot | — |
