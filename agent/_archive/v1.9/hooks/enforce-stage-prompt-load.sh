#!/usr/bin/env bash
# PreToolUse hook: block Write/Edit to cases/**/*_{stage}.md if the corresponding
# agent/prompts/{stage}.md was not Read in this session.
#
# Wiring: registered under hooks.PreToolUse for tools Write and Edit.
# Input: JSON on stdin with { tool_name, tool_input: { file_path, ... }, transcript_path, cwd }.
# Exit 0 = allow. Exit 2 = block (stderr surfaces to Claude).

set -euo pipefail

payload="$(cat)"

tool_name="$(printf '%s' "$payload" | /usr/bin/python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("tool_name",""))')"
file_path="$(printf '%s' "$payload" | /usr/bin/python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("tool_input",{}).get("file_path",""))')"
transcript_path="$(printf '%s' "$payload" | /usr/bin/python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("transcript_path",""))')"
cwd="$(printf '%s' "$payload" | /usr/bin/python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("cwd",""))')"

# Only care about Write/Edit
case "$tool_name" in
  Write|Edit) ;;
  *) exit 0 ;;
esac

# Only care about case report files
case "$file_path" in
  */cases/*.md) ;;
  *) exit 0 ;;
esac

basename="$(basename "$file_path")"

# Map filename suffix -> required stage prompt
required_prompt=""
case "$basename" in
  *_entity-verification.md)       required_prompt="agent/prompts/entity-verification.md" ;;
  *_stakeholder-investigation.md) required_prompt="agent/prompts/stakeholder-investigation.md" ;;
  *_industry-report.md)           required_prompt="agent/prompts/industry-analysis.md" ;;
  *_company-report.md)            required_prompt="agent/prompts/company-deep-dive.md" ;;
  *_decision-brief.md)            required_prompt="agent/prompts/decision-brief.md" ;;
  *_supplement.md)                required_prompt="agent/prompts/supplement-analysis.md" ;;
  *) exit 0 ;;
esac

# Resolve against cwd if relative
if [[ "$required_prompt" != /* ]]; then
  required_prompt="$cwd/$required_prompt"
fi

# Check transcript for a Read tool call on required_prompt
if [[ -z "$transcript_path" || ! -f "$transcript_path" ]]; then
  # Can't verify — fail closed
  echo "[stage-prompt-hook] transcript not available; cannot verify $required_prompt was Read. Please Read it first." >&2
  exit 2
fi

# JSONL transcript: look for assistant tool_use with name=Read and file_path matching
if /usr/bin/python3 - "$transcript_path" "$required_prompt" <<'PY'
import json, os, sys
transcript, target = sys.argv[1], sys.argv[2]
target_abs = os.path.realpath(target)
with open(transcript) as f:
    for line in f:
        try:
            evt = json.loads(line)
        except Exception:
            continue
        msg = evt.get("message") or {}
        for block in msg.get("content", []) or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") == "Read":
                fp = (block.get("input") or {}).get("file_path", "")
                if not fp:
                    continue
                try:
                    fp_abs = os.path.realpath(fp)
                except Exception:
                    fp_abs = fp
                if fp_abs == target_abs or fp == target:
                    sys.exit(0)
sys.exit(1)
PY
then
  exit 0
fi

# Not read — block
cat >&2 <<EOF
[stage-prompt-hook] BLOCKED: attempting to write $basename
without first loading the stage prompt.

Required: Read $required_prompt
Reason:   recon SKILL Step 4 mandates loading each stage prompt before
          producing its artifact. "I remember the structure" is not a
          substitute — the prompt file contains the checklist, required
          tables, and evidence-grade rules that make the report conform
          to past cases.

Action:   Read the required prompt file, then retry the Write/Edit.
EOF
exit 2
