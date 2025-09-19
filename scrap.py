from urllib.parse import urljoin
import bs4 as bs
import requests
import re

#URL de la page d'accueil du site
default_url = "http://books.toscrape.com/"

def extract_book(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = bs.BeautifulSoup(response.text, 'html.parser')

        # Sélecteurs
        title_el = soup.select_one("div.product_main h1") or soup.find("h1")
        price_el = soup.select_one("p.price_color")
        avail_el = soup.select_one("p.instock.availability")  # <-- class_ correct

        if not (title_el and price_el and avail_el):
            raise ValueError("Missing title/price/availability element")

        title = title_el.get_text(strip=True)
        price_text = price_el.get_text(strip=True)
        availability_text = avail_el.get_text(strip=True)

        # Prix : extrait les chiffres et le point
        price = float(re.sub(r'[^0-9.]+', '', price_text) or 0)

        # Disponibilité : récupère le premier nombre, sinon 0
        m = re.search(r'(\d+)', availability_text)
        availability = int(m.group(1)) if m else 0

        return {
            'title': title,
            'price': price,
            'availability': availability
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
        categories = extract_categories_url(url)  # [(name, link), ...]
        seen = set()  # éviter les doublons

        for name, link in categories:
            for book_url in extract_book_url_from_category(link):
                if book_url in seen:
                    continue
                seen.add(book_url)
                info = extract_book(book_url)
                if info:
                    info["url"] = book_url
                    info["category"] = name
                    books.append(info)
                    print(books)
        return books
        
    except Exception as e:
        print(f"Error extracting all books data: {e}")
        return []

books = extract_all_books()
print(len(books))
print(books)
#print(extract_category_book("http://books.toscrape.com/catalogue/category/books/historical-fiction_4/"))