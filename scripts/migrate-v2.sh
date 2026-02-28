#!/bin/bash

# ==== USAGE ====
usage() {
  cat << EOF
Usage: $0 -a <action> [-o <output_dir>] [-i <import_dir>] [-H <host>]

Actions:
  export    Export benchmarks from xbat
  import    Import benchmarks to xbat

Options:
  -a        Action to perform (export or import) [required]
  -o        Output directory for exported data (used with export action)
  -i        Import directory for data to import (used with import action)
  -H        API host (default: demo.xbat.dev)
  -h        Show this help message

Example:
  $0 -a export -o ./exports
  $0 -a export -o ./exports -H api.xbat.dev
  $0 -a import -i ./exports

EOF
  exit 1
}

# ==== PARSE ARGUMENTS ====
ACTION=""
OUTPUT_DIR="."
IMPORT_DIR="."
API_HOST="demo.xbat.dev"

while getopts "a:o:i:H:h" opt; do
  case $opt in
    a) ACTION="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    i) IMPORT_DIR="$OPTARG" ;;
    H) API_HOST="$OPTARG" ;;
    h) usage ;;
    *) usage ;;
  esac
done

# Validate action
if [[ -z "$ACTION" ]]; then
  echo "[!] Error: Action (-a) is required."
  usage
fi

if [[ "$ACTION" != "export" && "$ACTION" != "import" ]]; then
  echo "[!] Error: Invalid action '$ACTION'. Must be 'export' or 'import'."
  usage
fi

# Validate directories
if [[ "$ACTION" == "export" && ! -d "$OUTPUT_DIR" ]]; then
  echo "[!] Error: Output directory does not exist: $OUTPUT_DIR"
  exit 1
fi

if [[ "$ACTION" == "import" && ! -d "$IMPORT_DIR" ]]; then
  echo "[!] Error: Import directory does not exist: $IMPORT_DIR"
  exit 1
fi
# ==========================

# ==== CONFIGURATION ====
API_BASE="https://$API_HOST"
TOKEN_URL="$API_BASE/oauth/token"
VALIDATE_URL="$API_BASE/api/v1/current_user"
BENCHMARKS_URL="$API_BASE/api/v1/benchmarks"
EXPORT_URL="$API_BASE/api/v1/benchmarks/export"
IMPORT_URL="$API_BASE/api/v1/benchmarks/import"
ENV_FILE=".env.xbat"

# These will be loaded from .env.xbat file
USERNAME=""
PASSWORD=""
CLIENT_ID=""

# ==== TOKEN MANAGEMENT ====

load_token() {
  if [[ -f "$ENV_FILE" ]]; then
    source "$ENV_FILE"
  fi
  
  # Validate that required credentials are present
  if [[ -z "$USERNAME" || -z "$PASSWORD" || -z "$CLIENT_ID" ]]; then
    echo "[!] Error: Missing credentials in $ENV_FILE"
    echo "[!] The file must contain: USERNAME, PASSWORD, and CLIENT_ID"
    echo ""
    echo "Example $ENV_FILE format:"
    echo "USERNAME=your_username"
    echo "PASSWORD=your_password"
    echo "CLIENT_ID=your_client_id"
    echo "ACCESS_TOKEN=your_token"
    exit 1
  fi
}

save_token() {
  cat > "$ENV_FILE" << EOF
USERNAME=$USERNAME
PASSWORD=$PASSWORD
CLIENT_ID=$CLIENT_ID
ACCESS_TOKEN=$ACCESS_TOKEN
EOF
  chmod 600 "$ENV_FILE"
}

validate_token() {
  local status
  status=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $ACCESS_TOKEN" "$VALIDATE_URL")
  [[ "$status" == "200" ]]
}

request_new_token() {
  echo "[*] Requesting new access token..."
  TOKEN_RESPONSE=$(curl -s -X POST "$TOKEN_URL" \
    -d "grant_type=password" \
    -d "username=$USERNAME" \
    -d "password=$PASSWORD" \
    -d "client_id=$CLIENT_ID")

  ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | grep -oP '"access_token"\s*:\s*"\K[^"]+')

  if [[ -z "$ACCESS_TOKEN" ]]; then
    echo "[!] Failed to get access token. Response:"
    echo "$TOKEN_RESPONSE"
    exit 1
  fi

  echo "[+] New token acquired."
  save_token
}

# Load credentials and token
load_token
if [[ -z "$ACCESS_TOKEN" ]] || ! validate_token; then
  request_new_token
else
  echo "[+] Using cached access token."
fi
# ============================


# ==== MAIN LOGIC ====
echo "[*] Action: $ACTION"
echo "[*] API Host: $API_HOST"

if [[ "$ACTION" == "export" ]]; then
  echo "[*] Output directory: $OUTPUT_DIR"
  echo "[*] Fetching benchmarks from $BENCHMARKS_URL"
  
  # Fetch benchmarks
  BENCHMARKS_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BENCHMARKS_URL" \
    -H "accept: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  
  # Extract HTTP status (last line)
  HTTP_STATUS=$(echo "$BENCHMARKS_RESPONSE" | tail -n 1)
  BENCHMARKS_JSON=$(echo "$BENCHMARKS_RESPONSE" | sed '$d')
  
  if [[ "$HTTP_STATUS" != "200" ]]; then
    echo "[!] Failed to fetch benchmarks. HTTP status: $HTTP_STATUS"
    echo "[!] Response: $BENCHMARKS_JSON"
    exit 1
  fi
  
  echo "[+] Benchmarks fetched successfully."
  
  # Parse JSON and filter by state (done or timeout)
  # Extract runNr for benchmarks with state "done" or "timeout"
  if ! command -v jq &> /dev/null; then
    echo "[!] Error: jq is not installed. Cannot extract runNr from JSON response."
    echo "[!] Please install jq to use this script."
    exit 1
  fi
  
  echo "[*] Using jq for JSON parsing"
  RUN_NRS=$(echo "$BENCHMARKS_JSON" | jq -r '.data[] | select(.state == "done" or .state == "timeout") | .runNr')
  
  if [[ -z "$RUN_NRS" ]]; then
    echo "[!] No benchmarks found with state 'done' or 'timeout'."
    exit 0
  fi
  
  echo "[+] Found benchmarks to export:"
  echo "$RUN_NRS" | while read -r run_nr; do
    echo "    - runNr: $run_nr"
  done
  
  echo ""
  echo "[*] Exporting benchmarks..."
  
  # Export each benchmark
  EXPORT_COUNT=0
  EXPORT_FAILED=0
  
  while read -r run_nr; do
    if [[ -z "$run_nr" ]]; then
      continue
    fi
    
    echo "[*] Exporting runNr: $run_nr"
    
    # Build JSON payload
    PAYLOAD="{\"runNrs\": [$run_nr], \"anonymise\": false}"
    
    # Export benchmark
    OUTPUT_FILE="$OUTPUT_DIR/exported_${run_nr}.tgz"
    
    HTTP_STATUS=$(curl -# -w "%{http_code}" -X POST "$EXPORT_URL" \
      --max-time 0 \
      --connect-timeout 30 \
      --retry 3 \
      --retry-delay 5 \
      -H "accept: application/gzip" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -d "$PAYLOAD" \
      -o "$OUTPUT_FILE")
    
    if [[ "$HTTP_STATUS" == "200" ]]; then
      echo "[+] Successfully exported to: $OUTPUT_FILE"
      ((EXPORT_COUNT++))
    else
      echo "[!] Failed to export runNr: $run_nr (HTTP status: $HTTP_STATUS)"
      rm -f "$OUTPUT_FILE"
      ((EXPORT_FAILED++))
    fi
  done <<< "$RUN_NRS"
  
  echo ""
  echo "[+] Export complete!"
  echo "[+] Successfully exported: $EXPORT_COUNT"
  if [[ $EXPORT_FAILED -gt 0 ]]; then
    echo "[!] Failed exports: $EXPORT_FAILED"
  fi
  
elif [[ "$ACTION" == "import" ]]; then
  echo "[*] Import directory: $IMPORT_DIR"
  
  # Find all exported_*.tgz files
  echo "[*] Scanning for exported benchmark files..."
  
  FILES=($(find "$IMPORT_DIR" -maxdepth 1 -name "exported_*.tgz" -type f))
  
  if [[ ${#FILES[@]} -eq 0 ]]; then
    echo "[!] No exported_*.tgz files found in $IMPORT_DIR"
    exit 1
  fi
  
  echo "[+] Found ${#FILES[@]} file(s) to import"
  
  # Extract runNrs and sort them numerically
  declare -A FILE_MAP
  RUN_NRS_TO_IMPORT=()
  
  for file in "${FILES[@]}"; do
    basename=$(basename "$file")
    # Extract runNr from exported_<runNr>.tgz
    if [[ $basename =~ exported_([0-9]+)\.tgz ]]; then
      run_nr="${BASH_REMATCH[1]}"
      FILE_MAP[$run_nr]="$file"
      RUN_NRS_TO_IMPORT+=($run_nr)
    fi
  done
  
  # Sort runNrs numerically
  IFS=$'\n' SORTED_RUN_NRS=($(sort -n <<<"${RUN_NRS_TO_IMPORT[*]}"))
  unset IFS
  
  echo "[*] Import order (by runNr):"
  for run_nr in "${SORTED_RUN_NRS[@]}"; do
    echo "    - runNr: $run_nr (${FILE_MAP[$run_nr]})"
  done
  
  echo ""
  echo "[*] Importing benchmarks..."
  
  # Import each benchmark
  IMPORT_COUNT=0
  IMPORT_FAILED=0
  
  for run_nr in "${SORTED_RUN_NRS[@]}"; do
    file="${FILE_MAP[$run_nr]}"
    echo "[*] Importing runNr: $run_nr"
    
    # Import benchmark with FormData
    IMPORT_RESPONSE=$(curl -# -w "\n%{http_code}" -X POST "$IMPORT_URL" \
      --max-time 0 \
      --connect-timeout 30 \
      --retry 3 \
      --retry-delay 5 \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -F "file=@$file" \
      -F "reassignRunNr=false" \
      -F "updateColl=false")
    
    HTTP_STATUS=$(echo "$IMPORT_RESPONSE" | tail -n 1)
    IMPORT_BODY=$(echo "$IMPORT_RESPONSE" | sed '$d')
    
    if [[ "$HTTP_STATUS" == "200" || "$HTTP_STATUS" == "201" ]]; then
      echo "[+] Successfully imported runNr: $run_nr"
      ((IMPORT_COUNT++))
    else
      echo "[!] Failed to import runNr: $run_nr (HTTP status: $HTTP_STATUS)"
      if [[ -n "$IMPORT_BODY" ]]; then
        echo "[!] Response: $IMPORT_BODY"
      fi
      ((IMPORT_FAILED++))
    fi
    echo ""
  done
  
  echo "[+] Import complete!"
  echo "[+] Successfully imported: $IMPORT_COUNT"
  if [[ $IMPORT_FAILED -gt 0 ]]; then
    echo "[!] Failed imports: $IMPORT_FAILED"
  fi
fi
# ====================

exit 0
