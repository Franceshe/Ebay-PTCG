import requests
import json
from datetime import datetime
import os

class EbayPTCGScraper:
    def __init__(self, client_id, client_secret, sandbox=True):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        # Use sandbox or production API
        self.base_url = "https://api.sandbox.ebay.com" if sandbox else "https://api.ebay.com"

    def get_access_token(self):
        """Get OAuth token for eBay API"""
        auth_url = f"{self.base_url}/identity/v1/oauth2/token"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        data = {
            'grant_type': 'client_credentials',
            'scope': 'https://api.ebay.com/oauth/api_scope'
        }

        response = requests.post(
            auth_url,
            headers=headers,
            data=data,
            auth=(self.client_id, self.client_secret)
        )

        if response.status_code == 200:
            self.access_token = response.json()['access_token']
            print("✓ Successfully authenticated with eBay API")
            return self.access_token
        else:
            raise Exception(f"Authentication failed: {response.text}")

    def search_psa_cards(self, card_name="", set_name="", psa_grade=None, limit=50):
        """
        Search for PSA graded Pokemon cards

        Args:
            card_name: Pokemon card name (e.g., "Charizard", "Pikachu")
            set_name: Set name (e.g., "Base Set", "Jungle")
            psa_grade: PSA grade number (e.g., 10, 9, 8)
            limit: Number of results to return
        """
        if not self.access_token:
            self.get_access_token()

        # Build search query
        query_parts = ["Pokemon", "PSA"]
        if card_name:
            query_parts.append(card_name)
        if set_name:
            query_parts.append(set_name)
        if psa_grade:
            query_parts.append(f"PSA {psa_grade}")

        query = " ".join(query_parts)

        # eBay Browse API endpoint
        search_url = f"{self.base_url}/buy/browse/v1/item_summary/search"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        params = {
            'q': query,
            'limit': limit,
            'category_ids': '183454',  # Sports Cards category
            'filter': 'buyingOptions:{FIXED_PRICE}',  # Only Buy It Now listings
        }

        print(f"\nSearching for: {query}")
        response = requests.get(search_url, headers=headers, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Search failed: {response.text}")

    def parse_results(self, results):
        """Parse and format search results"""
        if 'itemSummaries' not in results:
            return []

        cards = []
        for item in results['itemSummaries']:
            card_info = {
                'title': item.get('title', 'N/A'),
                'price': item.get('price', {}).get('value', 'N/A'),
                'currency': item.get('price', {}).get('currency', 'USD'),
                'condition': item.get('condition', 'N/A'),
                'item_url': item.get('itemWebUrl', 'N/A'),
                'image_url': item.get('image', {}).get('imageUrl', 'N/A'),
                'seller': item.get('seller', {}).get('username', 'N/A'),
            }
            cards.append(card_info)

        return cards

    def save_results(self, cards, filename=None):
        """Save results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'ebay_ptcg_results_{timestamp}.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cards, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Results saved to {filename}")
        return filename

    def display_results(self, cards):
        """Display results in a readable format"""
        if not cards:
            print("\nNo results found.")
            return

        print(f"\n{'='*80}")
        print(f"Found {len(cards)} PSA Graded Pokemon Cards")
        print(f"{'='*80}\n")

        for i, card in enumerate(cards, 1):
            print(f"{i}. {card['title']}")
            print(f"   Price: {card['currency']} ${card['price']}")
            print(f"   Condition: {card['condition']}")
            print(f"   Seller: {card['seller']}")
            print(f"   URL: {card['item_url']}")
            print()


def main():
    # Get eBay credentials from environment variables
    CLIENT_ID = os.getenv('EBAY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('EBAY_CLIENT_SECRET')

    if not CLIENT_ID or not CLIENT_SECRET:
        print("⚠️  Please set your eBay API credentials!")
        print("   Export them as environment variables:")
        print("      export EBAY_CLIENT_ID='your_client_id'")
        print("      export EBAY_CLIENT_SECRET='your_client_secret'")
        return

    # Use sandbox=True for testing, sandbox=False for production
    scraper = EbayPTCGScraper(CLIENT_ID, CLIENT_SECRET, sandbox=True)

    # Example searches - customize as needed

    # Search for PSA 10 Charizard cards
    print("\n" + "="*80)
    print("EXAMPLE 1: PSA 10 Charizard Cards")
    print("="*80)
    results = scraper.search_psa_cards(card_name="Charizard", psa_grade=10, limit=20)
    cards = scraper.parse_results(results)
    scraper.display_results(cards)
    scraper.save_results(cards, 'charizard_psa10.json')

    # Search for any PSA graded Pikachu
    print("\n" + "="*80)
    print("EXAMPLE 2: PSA Graded Pikachu Cards")
    print("="*80)
    results = scraper.search_psa_cards(card_name="Pikachu", limit=20)
    cards = scraper.parse_results(results)
    scraper.display_results(cards)
    scraper.save_results(cards, 'pikachu_psa.json')

    # Search for Base Set PSA cards
    print("\n" + "="*80)
    print("EXAMPLE 3: Base Set PSA Graded Cards")
    print("="*80)
    results = scraper.search_psa_cards(set_name="Base Set", limit=20)
    cards = scraper.parse_results(results)
    scraper.display_results(cards)
    scraper.save_results(cards, 'base_set_psa.json')


if __name__ == "__main__":
    main()
