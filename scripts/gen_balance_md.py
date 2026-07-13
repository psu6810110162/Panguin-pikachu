#!/usr/bin/env python3
"""Generate docs/BALANCE.md from balance/v1/*.json (single source of truth).

Run: python scripts/gen_balance_md.py
Balance data is authoritative; BALANCE.md is a generated human-readable mirror.
Do not edit BALANCE.md by hand — edit the JSON and re-run this script.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BALANCE = ROOT / "balance" / "v1"
OUT = ROOT / "docs" / "BALANCE.md"


def _load(name: str) -> dict:
    return json.loads((BALANCE / name).read_text(encoding="utf-8"))


def _sign(n: float) -> str:
    return f"+{n:g}" if n > 0 else f"{n:g}"


def main() -> None:
    junctions = _load("junctions.json")
    boss = _load("boss.json")
    diff = _load("difficulty.json")

    lines: list[str] = []
    lines.append("# Balance — Penguin Dash (generated)")
    lines.append("")
    lines.append(
        "> ⚙️ **ไฟล์นี้ generate อัตโนมัติจาก `balance/v1/*.json`** — อย่าแก้ด้วยมือ "
        "แก้ JSON แล้วรัน `python scripts/gen_balance_md.py`. "
        "รายละเอียดดีไซน์ดู [GAME_DESIGN.md](GAME_DESIGN.md)."
    )
    lines.append("")

    # Difficulty
    m = diff["meters"]
    h = diff["hearts"]
    s = diff["scoring"]
    lines.append("## Difficulty / Tuning")
    lines.append("")
    lines.append(
        f"- Meters: start `{m['start_heat']}` / `{m['start_capitalist_anger']}`, "
        f"range `[{m['min']}, {m['max']}]`, Game Over ที่ `{m['game_over_at']}`, "
        f"decay `{m['passive_decay_per_second']}/s`"
    )
    lines.append(
        f"- Hearts: start `{h['start']}` (cap `{h['cap']}`), ตกเหว `-{h['fall_penalty']}`, "
        f"respawn `{h['respawn_seconds']}s` (invincible `{h['invincible_seconds']}s`)"
    )
    lines.append(
        f"- Scoring: crisis เริ่ม `+{s['initial_crisis_temp_c']}°C`, systemic `{s['systemic_point_c']}°C/ข้อ` "
        f"(สูงสุด run `{s['max_run_reduction_c']}°C`), boss `{s['boss_bonus_per_wave_c']}°C/wave` "
        f"(สูงสุด `{s['max_boss_reduction_c']}°C`)"
    )
    lines.append("")
    lines.append("| Rank | ช่วง °C | ระดับ |")
    lines.append("|---|---|---|")
    for r in s["ranks"]:
        lines.append(f"| {r['rank']} | {r['min_c']}–{r['max_c']}°C | {r['label']} |")
    lines.append("")

    # Junctions
    lines.append(f"## 10 Y-Junctions (v{junctions['version']})")
    lines.append("")
    lines.append("| โซน | หมวด | ⬅️ ซ้าย (Heat/Anger) | ➡️ ขวา (Heat/Anger) | Systemic |")
    lines.append("|---|---|---|---|---|")
    for j in junctions["junctions"]:
        lft, rgt = j["left"], j["right"]
        ld, rd = lft["meter_deltas"], rgt["meter_deltas"]
        systemic = "ซ้าย" if lft["systemic"] else "ขวา"
        lines.append(
            f"| {j['zone']} | {j['category']} | {lft['label']} "
            f"({_sign(ld['heat'])}/{_sign(ld['capitalist_anger'])}) | {rgt['label']} "
            f"({_sign(rd['heat'])}/{_sign(rd['capitalist_anger'])}) | {systemic} |"
        )
    lines.append("")

    # Boss
    lines.append(f"## Boss: {boss['boss_id']} — {len(boss['waves'])} waves (armor {boss['armor']})")
    lines.append("")
    lines.append("| Wave | ธีม | ✅ ถูก | ❌ ผิด |")
    lines.append("|---|---|---|---|")
    for w in boss["waves"]:
        lines.append(f"| {w['wave']} | {w['theme']} | {w['correct_item']} | {w['wrong_item']} |")
    lines.append("")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
