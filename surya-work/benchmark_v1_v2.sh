# Run v1
source .venv-v1/bin/activate
time surya_ocr PMC13585579_p4.pdf --results_dir results/surya-v1
deactivate

# Run v2
source .venv-v2/bin/activate
time surya PMC13585579_p4.pdf --results_dir results/surya-v2
deactivate
