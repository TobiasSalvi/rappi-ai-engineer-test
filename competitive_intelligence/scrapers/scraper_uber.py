from playwright.sync_api import sync_playwright
import csv
from datetime import datetime
import os

UBER_EATS_URL = "https://www.ubereats.com/mx"
TARGET_PRODUCTS = ["big mac", "combo", "nuggets"]

def extract_rating(page):
    rating = None
    try:
        elements = page.locator("[data-testid='rich-text']")
        for i in range(min(elements.count(), 30)):
            text = elements.nth(i).inner_text().strip()
            try:
                value = float(text)
                if 0 <= value <= 5:
                    rating = text
                    break
            except:
                continue
    except:
        pass
    return rating

def extract_eta(page):
    eta = None
    try:
        el = page.locator("text=min")
        if el.count() > 0:
            eta = el.first.inner_text().strip()
    except:
        pass
    return eta

def extract_products(page):
    products = []

    try:
        spans = page.locator("span")

        for i in range(min(spans.count(), 400)):
            text = spans.nth(i).inner_text().lower().strip()

            if not text:
                continue

            # 🔥 FILTRO FUERTE
            if any(keyword in text for keyword in TARGET_PRODUCTS):

                # excluir basura
                if len(text) < 5 or len(text) > 80:
                    continue

                if "contenido" in text or "buscar" in text:
                    continue

                if "ciudad" in text:
                    continue

                # buscar precio cercano
                price = None
                parent_text = ""

                try:
                    parent = spans.nth(i).locator("xpath=..")
                    parent_text = parent.inner_text()

                    for word in parent_text.split():
                        if "$" in word:
                            price = word
                            break
                except:
                    pass

                products.append({
                    "product_name": text,
                    "price": price
                })

    except:
        pass

    return products


def scrape_uber_eats():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(viewport={"width":1440,"height":900}, locale="es-MX")
        page = context.new_page()

        print("Abriendo Uber Eats...")
        page.goto(UBER_EATS_URL)

        input("\n👉 PASO 1: Configurar dirección y ENTER\n")

        results = []

        for i in range(3):
            input(f"\n👉 PASO {i+2}: Entrar restaurante, scrollear y ENTER\n")

            try:
                name = page.locator("h1").first.inner_text()
                eta = extract_eta(page)
                rating = extract_rating(page)
                products = extract_products(page)

                if not products:
                    products = [{"product_name": None, "price": None}]

                for prod in products:
                    results.append({
                        "platform": "uber_eats",
                        "city": "CDMX",
                        "restaurant_name": name,
                        "rating": rating,
                        "eta": eta,
                        "product_name": prod["product_name"],
                        "price": prod["price"],
                        "url": page.url,
                        "scrape_time": datetime.now().isoformat()
                    })

                print("✔ Scrapeado:", name, "| productos:", len(products))

            except Exception as e:
                print("Error:", e)

        # Ensure directories exist
        os.makedirs("data/raw", exist_ok=True)

        raw_path = "data/raw/uber_eats_products.csv"

        with open(raw_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

        print("\nCSV guardado en:", raw_path)

        input("\nENTER para cerrar")
        browser.close()

if __name__ == "__main__":
    scrape_uber_eats()
