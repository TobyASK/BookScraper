from urllib.parse import urljoin
import bs4 as bs
import requests
import re
import csv
import concurrent.futures
import os # Pour manipuler les fichiers et répertoires

default_url = "http://books.toscrape.com/"

def extract_book(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = bs.BeautifulSoup(response.text, 'html.parser')

        # Titre
        title_el = soup.select_one("div.product_main h1") or soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else ""

        # UPC
        upc = soup.find('th', string='UPC')
        upc = upc.find_next('td').text.strip() if upc else ""

        # Prix TTC & HT
        price_incl = soup.find('th', string='Price (incl. tax)')
        price_incl = price_incl.find_next('td').text.strip() if price_incl else ""
        price_excl = soup.find('th', string='Price (excl. tax)')
        price_excl = price_excl.find_next('td').text.strip() if price_excl else ""

        # Disponibilité (nombre disponible)
        avail_el = soup.select_one("p.instock.availability")
        availability_text = avail_el.get_text(strip=True) if avail_el else ""
        m = re.search(r'(\d+)', availability_text)
        number_available = int(m.group(1)) if m else 0

        # Description
        desc_tag = soup.find('div', id='product_description')
        product_description = ""
        if desc_tag:
            desc_p = desc_tag.find_next_sibling('p')
            if desc_p:
                product_description = desc_p.get_text(strip=True)

        # Catégorie
        breadcrumb = soup.select('ul.breadcrumb li a')
        category = breadcrumb[-1].find_previous('a').get_text(strip=True) if len(breadcrumb) > 2 else ""

        # Note (review_rating)
        rating_tag = soup.find('p', class_='star-rating')
        rating_text = rating_tag['class'][1] if rating_tag and len(rating_tag['class']) > 1 else 'Zero'
        rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5, 'Zero': 0}
        review_rating = rating_map.get(rating_text, 0)

        # Image URL
        img_tag = soup.find('div', class_='item active')
        img_url = ""
        if img_tag:
            img = img_tag.find('img')
            if img and img.get('src'):
                img_url = urljoin(url, img['src'])

        return {
            'product_page_url': url,
            'universal_product_code': upc,
            'title': title,
            'price_including_tax': price_incl,
            'price_excluding_tax': price_excl,
            'number_available': number_available,
            'product_description': product_description,
            'category': category,
            'review_rating': review_rating,
            'image_url': img_url
        }
    except Exception as e:
        print(f"Error extracting book data from {url}: {e}")
        return None

def extract_book_url_from_category(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = bs.BeautifulSoup(response.text, 'html.parser')
        
        url_books = []
        for book in soup.find_all('h3'):
            book_url = book.find('a')['href']
            full_url = default_url + 'catalogue/' + book_url.replace('../../../', '')
            url_books.append(full_url)
        
        next_page = soup.find('li', class_='next')
        if next_page:
            next_page_url = next_page.find('a')['href']
            next_full_url = urljoin(url, next_page_url)
            url_books.extend(extract_book_url_from_category(next_full_url))
        
        return url_books
    except Exception as e:
        print(f"Error extracting book URLs from category: {e}")
        return []

def extract_category_book(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = bs.BeautifulSoup(response.text, 'html.parser')
        
        url_books = extract_book_url_from_category(url)
        books = [extract_book(book_url) for book_url in url_books]
        return [book for book in books if book is not None]
    except Exception as e:
        print(f"Error extracting category books: {e}")
        return []

def extract_categories_url(url = default_url):
    categories_url = []
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = bs.BeautifulSoup(response.text, 'html.parser')
        
        categories = soup.select("div.side_categories ul li ul li a")

        for cat in categories:
            name = cat.get_text(strip=True)
            link = url + cat["href"]
            categories_url.append((name, link))
        
        return categories_url
    
    except Exception as e:
        print(f"Error extracting categories url: {e}")
        return []

def extract_all_book_url(url = default_url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = bs.BeautifulSoup(response.text, 'html.parser')

        categories = extract_categories_url(url)  # liste de tuples (name, link)
        all_book_urls = []
        for _, link in categories:
            all_book_urls.extend(extract_book_url_from_category(link))
        return all_book_urls
    except Exception as e:
        print(f"Error extracting all books: {e}")
        return []

def extract_all_books(url = default_url):
    try:
        books = []
        categories = extract_categories_url(url)
        seen_urls = set()
        seen_titles = set()

        # Récupère tous les liens de livres avec leur catégorie
        all_book_urls = []
        for name, link in categories:
            for book_url in extract_book_url_from_category(link):
                all_book_urls.append((book_url, name))

        def process_book(args):
            book_url, name = args
            info = extract_book(book_url)
            if info:
                title_key = (info["title"].strip().lower(), name.strip().lower())
                return (book_url, title_key, info, name)
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
            results = executor.map(process_book, all_book_urls)

        for result in results:
            if not result:
                continue
            book_url, title_key, info, name = result
            if book_url in seen_urls or title_key in seen_titles:
                continue
            seen_urls.add(book_url)
            seen_titles.add(title_key)
            books.append(info)
        return books
    except Exception as e:
        print(f"Error extracting all books data: {e}")
        return []
    
def save_books_to_csv(books, filename):
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=[
                'product_page_url',
                'universal_product_code',
                'title',
                'price_including_tax',
                'price_excluding_tax',
                'number_available',
                'product_description',
                'category',
                'review_rating',
                'image_url',
                'local_image_path'
            ])
            writer.writeheader()
            for book in books:
                writer.writerow(book)
        print(f"Books data saved to {filename}")
    except Exception as e:
        print(f"Error saving books to CSV: {e}")
    
def download_image(img_url, dest_folder, book_title):
    try:
        os.makedirs(dest_folder, exist_ok=True)
        ext = os.path.splitext(img_url)[-1]
        safe_title = "".join(c if c.isalnum() or c in " ._-" else "_" for c in book_title)
        filename = f"{safe_title}{ext}"
        filepath = os.path.join(dest_folder, filename)
        if not os.path.exists(filepath):
            resp = requests.get(img_url)
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(resp.content)
        return filepath
    except Exception as e:
        print(f"Error downloading image {img_url}: {e}")
        return ""
    
def process_all_categories():
    categories = extract_categories_url()
    for cat_name, cat_url in categories:
        print(f"Traitement catégorie : {cat_name}")
        books = extract_category_book(cat_url)
        img_folder = os.path.join("images", "".join(c if c.isalnum() or c in " ._-" else "_" for c in cat_name))
        for book in books:
            if book and book.get("image_url"):
                local_img = download_image(book["image_url"], img_folder, book["title"])
                book["local_image_path"] = local_img
        csv_filename = f"{''.join(c if c.isalnum() or c in ' ._-' else '_' for c in cat_name)}.csv"
        save_books_to_csv(books, csv_filename)

process_all_categories()
#print(extract_category_book("http://books.toscrape.com/catalogue/category/books/historical-fiction_4/"))