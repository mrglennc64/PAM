#!/bin/bash
C=hermes-agent-flou-hermes-agent-1

echo "=== config file paths ==="
docker exec "$C" sh -c 'find /opt/data /home /root /opt/hermes -maxdepth 6 \( -name "config.yaml" -o -name "config.toml" -o -name "config.json" -o -name ".env" \) 2>/dev/null'

echo ""
echo "=== /opt/data listing ==="
docker exec "$C" sh -c 'ls -la /opt/data 2>/dev/null; echo ---; ls -la /opt/data/.hermes 2>/dev/null'

echo ""
echo "=== config contents (yaml/json, secrets redacted) ==="
docker exec "$C" sh -c 'for f in $(find /opt/data /home /root -maxdepth 6 \( -name "config.yaml" -o -name "config.json" \) 2>/dev/null); do echo "### $f ###"; cat "$f"; echo; done' | sed -E 's/(api_key|apiKey|API_KEY|token|password)([:= ]+)[^[:space:]"'"'"']+/\1\2<redacted>/gi'

echo ""
echo "=== relevant env vars (redacted) ==="
docker exec "$C" env | grep -iE 'model|provider|api_base|base_url|openai|anthropic|gemini|ollama' | sed -E 's/(KEY|TOKEN|SECRET)=.*/\1=<redacted>/'

echo ""
echo "=== hermes config command (if it exists) ==="
docker exec "$C" sh -c 'hermes config show 2>/dev/null || hermes model --help 2>&1 | head -20'
