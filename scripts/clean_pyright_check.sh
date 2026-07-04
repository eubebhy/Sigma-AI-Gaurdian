#!/usr/bin/env bash
set -euo pipefail

TARGET="$1"

pyright -p .. --outputjson "$TARGET" 2>/dev/null |
  jq -r '
.generalDiagnostics as $d
| if ($d|length)==0 then
    "No issues."
  else
    ($d[0].file | split("/") | last),
    (
      $d[]
      | "\(.range.start.line + 1)\t|\t\(.message)"
    )
  end
'
