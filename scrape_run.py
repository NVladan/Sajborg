from scrapers import scrape_ipon_products

if __name__ == "__main__":
    # Run the scraper with the Flask app context
    total_products = scrape_ipon_products()
    print(f"Scraper completed, imported {total_products} products.")