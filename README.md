# IPCtoBNSMapping

# Install core packages
pip install fastapi uvicorn sqlalchemy beautifulsoup4 requests pdfminer.six spacy scrapy
python -m spacy download en_core_web_lg

python database.py
python ingest.py
python mapping.py
python mapping_creator.py
uvicorn api:app --reload
streamlit run ui.py
