#!/usr/bin/env bash
# Generate a Synthea synthetic patient FHIR bundle for a showcase case.
#
# Usage:
#   ./scripts/generate_synthea_case.sh <case_name> [seed]
#
# Examples:
#   ./scripts/generate_synthea_case.sh sarah 3923
#   ./scripts/generate_synthea_case.sh marcus 7711
#
# Requires: java 11+, internet access for the first run.

set -euo pipefail

CASE_NAME="${1:?Usage: $0 <case_name> [seed]}"
SEED="${2:-3923}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${REPO_ROOT}/data/cases/${CASE_NAME}"
WORK_DIR="${OUT_DIR}/synthea-output"
JAR_URL="https://github.com/synthetichealth/synthea/releases/download/v3.3.0/synthea-with-dependencies.jar"

mkdir -p "${WORK_DIR}"
cd "${WORK_DIR}"

if [ ! -f synthea-with-dependencies.jar ]; then
  echo "Downloading Synthea jar..."
  curl -fL -o synthea-with-dependencies.jar "${JAR_URL}"
fi

echo "Generating patient with seed ${SEED}..."
java -jar synthea-with-dependencies.jar \
  -p 1 -s "${SEED}" \
  --exporter.fhir.export=true \
  --exporter.csv.export=false \
  --generate.only_alive_patients=true \
  --exporter.years_of_history=10 \
  Massachusetts \
  -a 60-75 -g F

# The first FHIR bundle file is the patient bundle (others are hospital/practitioner).
PATIENT_BUNDLE="$(ls output/fhir/*.json | grep -v 'hospitalInformation\|practitionerInformation' | head -1)"
if [ -z "${PATIENT_BUNDLE}" ]; then
  echo "ERROR: no patient bundle produced. Check Synthea output above." >&2
  exit 1
fi

cp "${PATIENT_BUNDLE}" "${OUT_DIR}/fhir.json"
echo "Wrote ${OUT_DIR}/fhir.json"
