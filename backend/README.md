# Backend — Eucharist Count

Pipeline de visão computacional para contagem de pessoas usando YOLO + DeepSORT.
Este módulo roda localmente e usa vídeo de teste para validação.

## ✅ Requisitos
- Python **3.11.15**
- (Opcional) `pyenv` configurado com `.python-version` no root do projeto
- Dependências em `backend/requirements-cpu.txt` ou `backend/requirements-gpu.txt`

## 📦 Setup
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install --no-cache-dir -r requirements-cpu.txt

cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install --no-cache-dir -r requirements-gpu.txt