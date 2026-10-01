# 1. Set up Surya v2 environment
uv venv --clear .venv-v2
source .venv-v2/bin/activate
uv pip install surya-ocr
deactivate

# 2. Set up Surya v1 legacy environment
uv venv --clear .venv-v1
source .venv-v1/bin/activate
uv pip install surya-ocr==0.17.0
deactivate
