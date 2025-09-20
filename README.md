# 📚 Books Online — Suivi des prix (bêta)

Projet Python qui récupère automatiquement les infos des livres sur [Books to Scrape](http://books.toscrape.com).  
Le script parcourt toutes les catégories, enregistre les données dans des fichiers CSV et télécharge aussi les couvertures des livres.

---

## Installation

Cloner le repo et installer les dépendances dans un environnement virtuel :

```bash
git clone https://github.com/mon-projet/books-online-scraper.git
cd books-online-scraper

python -m venv .venv
source .venv/bin/activate   # sous Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Utilisation

Lancer le script principal :

```bash
python main.py
```

Le programme va :
- parcourir toutes les catégories du site,
- créer un fichier CSV par catégorie,
- télécharger les images associées.

---

## Résultats

Les données sont générées dans le dossier `data/` :

- `data/csv/<Categorie>.csv` → les infos des livres d’une catégorie  
- `data/images/<Categorie>/` → toutes les couvertures des livres  

Chaque fichier CSV contient :  
`product_page_url, upc, title, prix (TTC/HT), dispo, description, catégorie, note, image_url, chemin image locale`

---

## Notes

- Les fichiers CSV et images ne sont pas inclus dans le repo (ils sont exclus via `.gitignore`).  
- Le projet est une version **bêta** centrée sur Books to Scrape, utilisé comme bac à sable de test.  
- Code volontairement simple pour être lu, compris et réutilisé facilement.

---

✍️ Projet développé dans le cadre de Books Online par Anis Bekkouche pour un projet OpenClassrooms.
