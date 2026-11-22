# Dossier de conception

- PDF final : `../ENSO-Monitor-dossier-de-conception.pdf`
- Source : `dossier.md` (Markdown + HTML), images et diagrammes dans `img/`.
- Régénérer le PDF : `npm install mermaid@11` dans ce dossier, puis `python3 build.py`
  (nécessite Google Chrome, `pip install markdown`, et `pdftotext`/`pdfinfo` de poppler).
  Le script fait deux passes pour numéroter le sommaire et affiche le nombre de pages
  (limite du sujet : 15, couverture comprise).
