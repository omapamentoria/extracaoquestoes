#!/bin/bash
# Prepara uma sessão nova do Claude Code na nuvem para o Banco MAPA.
# Uso: bash ferramentas_nuvem/setup.sh
set -e
R="$(cd "$(dirname "$0")/.." && pwd)"
command -v pdftoppm >/dev/null && command -v tesseract >/dev/null || \
  (apt-get install -y -q poppler-utils tesseract-ocr >/dev/null 2>&1 || \
   (apt-get update -q >/dev/null 2>&1 && apt-get install -y -q poppler-utils tesseract-ocr >/dev/null 2>&1))
python3 -c "import pdfplumber, cv2, numpy" 2>/dev/null || {
  pip install -q --ignore-installed cffi cryptography
  pip install -q pdfplumber opencv-python-headless numpy
}
mkdir -p ~/mnt/BM ~/tmp_banco
[ -e ~/mnt/BM/_banco ] || ln -s "$R/_banco" ~/mnt/BM/_banco
cp "$R"/_banco/ferramentas/*.py "$R"/_banco/ferramentas/roda.sh ~/tmp_banco/
echo "ok: ~/mnt/BM/_banco -> $R/_banco"
