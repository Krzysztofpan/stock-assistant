#!/usr/bin/env bash
# Retry tworzenia VM.Standard.A1.Flex (Oracle Always Free) aż znajdzie capacity.
# Użycie: cp deploy/oci-retry.env.example deploy/oci-retry.env && nano deploy/oci-retry.env
#         ./deploy/oci-retry-a1.sh
# W tle:  nohup ./deploy/oci-retry-a1.sh >> deploy/oci-retry.log 2>&1 &

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${OCI_RETRY_ENV:-$SCRIPT_DIR/oci-retry.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Brak $ENV_FILE — skopiuj z oci-retry.env.example i uzupełnij OCID-y." >&2
  exit 1
fi

# shellcheck source=/dev/null
set -a && source "$ENV_FILE" && set +a

: "${COMPARTMENT_ID:?COMPARTMENT_ID wymagane w oci-retry.env}"
: "${SUBNET_ID:?SUBNET_ID wymagane w oci-retry.env}"
: "${SSH_PUBLIC_KEY_FILE:?SSH_PUBLIC_KEY_FILE wymagane w oci-retry.env}"

if ! command -v oci >/dev/null 2>&1; then
  echo "Brak oci-cli. Instalacja: https://docs.oracle.com/en-us/iaas/Content/API/SDK/docs/cliinstall.htm" >&2
  exit 1
fi

if [[ ! -f "$SSH_PUBLIC_KEY_FILE" ]]; then
  echo "Nie ma pliku klucza SSH: $SSH_PUBLIC_KEY_FILE" >&2
  exit 1
fi

INTERVAL="${RETRY_INTERVAL_SEC:-300}"
OCPUS="${OCPUS:-1}"
MEMORY_GB="${MEMORY_GB:-6}"
DISPLAY_NAME="${DISPLAY_NAME:-stock-assistant}"
BOOT_VOLUME_GB="${BOOT_VOLUME_GB:-50}"
SHAPE="VM.Standard.A1.Flex"
LOG_FILE="${OCI_RETRY_LOG:-$SCRIPT_DIR/oci-retry.log}"

read -r -a ADS <<< "${AVAILABILITY_DOMAINS:-AD-1 AD-2 AD-3}"

resolve_ad() {
  local short="$1"
  if [[ "$short" == *"-AD-"* ]]; then
    echo "$short"
    return
  fi
  oci iam availability-domain list \
    --compartment-id "$COMPARTMENT_ID" \
    --query "data[?ends_with(name, '${short}')].name | [0]" \
    --raw-output
}

if [[ -z "${IMAGE_ID:-}" ]]; then
  echo "[$(date -Iseconds)] Szukam obrazu Ubuntu 22.04 ARM..."
  IMAGE_ID="$(oci compute image list \
    --compartment-id "$COMPARTMENT_ID" \
    --operating-system "Canonical Ubuntu" \
    --operating-system-version "22.04" \
    --shape "$SHAPE" \
    --sort-by TIMECREATED \
    --sort-order DESC \
    --query 'data[0]."id"' \
    --raw-output)"
  if [[ -z "$IMAGE_ID" || "$IMAGE_ID" == "null" ]]; then
    echo "Nie znaleziono obrazu Ubuntu 22.04 dla $SHAPE. Ustaw IMAGE_ID ręcznie." >&2
    exit 1
  fi
  echo "IMAGE_ID=$IMAGE_ID"
fi

echo "[$(date -Iseconds)] Start retry: shape=$SHAPE ${OCPUS}OCPU/${MEMORY_GB}GB ADs=${ADS[*]} co ${INTERVAL}s"
echo "Log: $LOG_FILE"

attempt=0
while true; do
  for ad_short in "${ADS[@]}"; do
    ad="$(resolve_ad "$ad_short")"
    if [[ -z "$ad" || "$ad" == "null" ]]; then
      echo "[$(date -Iseconds)] Pomijam nieznany AD: $ad_short" | tee -a "$LOG_FILE"
      continue
    fi

    attempt=$((attempt + 1))
    echo "[$(date -Iseconds)] Próba #$attempt — $ad" | tee -a "$LOG_FILE"

    set +e
    result="$(oci compute instance launch \
      --compartment-id "$COMPARTMENT_ID" \
      --availability-domain "$ad" \
      --display-name "$DISPLAY_NAME" \
      --subnet-id "$SUBNET_ID" \
      --image-id "$IMAGE_ID" \
      --shape "$SHAPE" \
      --shape-config "{\"ocpus\": ${OCPUS}, \"memoryInGBs\": ${MEMORY_GB}}" \
      --assign-public-ip true \
      --ssh-authorized-keys-file "$SSH_PUBLIC_KEY_FILE" \
      --boot-volume-size-in-gbs "$BOOT_VOLUME_GB" \
      2>&1)"
    status=$?
    set -e

    if [[ $status -eq 0 ]]; then
      instance_id="$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || true)"
      echo "[$(date -Iseconds)] SUKCES! Instancja utworzona." | tee -a "$LOG_FILE"
      echo "$result" | tee -a "$LOG_FILE"
      if [[ -n "$instance_id" ]]; then
        echo "INSTANCE_ID=$instance_id" | tee -a "$LOG_FILE"
        echo "Public IP (może chwilę potrwać):" | tee -a "$LOG_FILE"
        oci compute instance list-vnics --instance-id "$instance_id" \
          --query 'data[0]."public-ip"' --raw-output 2>/dev/null | tee -a "$LOG_FILE" || true
      fi
      exit 0
    fi

    echo "$result" | tail -5 | tee -a "$LOG_FILE"
    if echo "$result" | grep -qi "Out of capacity"; then
      echo "  -> brak capacity w $ad" | tee -a "$LOG_FILE"
    fi
  done

  echo "[$(date -Iseconds)] Czekam ${INTERVAL}s..." | tee -a "$LOG_FILE"
  sleep "$INTERVAL"
done
