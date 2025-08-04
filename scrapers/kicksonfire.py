"""
KicksOnFire Scraper - Tracks new sneaker releases and upcoming drops
"""

import logging
import time
import random
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import html

from scrapers.base_scraper import BaseSneakerScraper, random_delay

logger = logging.getLogger("SneakerBot")

class KicksOnFireScraper(BaseSneakerScraper):
    """Scraper for KicksOnFire.com to track new and upcoming releases"""
    
    def __init__(self, site_config):
        """Initialize the scraper with site-specific configuration."""
        super().__init__(site_config)
        self.name = "KicksOnFire"
        self.base_url = site_config.get('url', 'https://www.kicksonfire.com')
        self.new_releases_url = site_config.get('new_releases_url', 'https://www.kicksonfire.com/category/new-releases/')
        self.upcoming_url = site_config.get('upcoming_url', 'https://www.kicksonfire.com/category/upcoming-releases/all/')
        
        # Configure for anti-ban measures
        self.rate_limit = site_config.get('rate_limit', 20)  # Higher rate limit to avoid bans
        self.rotate_user_agent = True
        self.use_random_delays = True
    
    def get_new_releases(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get the latest sneaker releases from KicksOnFire.
        
        Args:
            limit: Maximum number of releases to fetch
            
        Returns:
            List of release dictionaries
        """
        logger.info(f"Fetching new releases from {self.new_releases_url}")
        
        try:
            soup = self.get_page(self.new_releases_url)
            if not soup:
                logger.error("Failed to get new releases page")
                return []
            
            # Find all release articles
            release_articles = soup.select('article.post')
            logger.info(f"Found {len(release_articles)} release articles")
            
            releases = []
            for article in release_articles[:limit]:
                try:
                    # Extract release data
                    release = self._extract_release_data(article)
                    if release:
                        releases.append(release)
                        
                    # Add random delay to appear more human-like
                    if self.use_random_delays:
                        random_delay(0.5, 2.0)
                        
                except Exception as e:
                    logger.error(f"Error extracting release data: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(releases)} new releases")
            return releases
            
        except Exception as e:
            logger.error(f"Error getting new releases: {e}")
            return []
    
    def get_upcoming_releases(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get upcoming sneaker releases from KicksOnFire.
        
        Args:
            limit: Maximum number of releases to fetch
            
        Returns:
            List of release dictionaries
        """
        logger.info(f"Fetching upcoming releases from {self.upcoming_url}")
        
        try:
            soup = self.get_page(self.upcoming_url)
            if not soup:
                logger.error("Failed to get upcoming releases page")
                return []
            
            # Find all release articles
            release_articles = soup.select('article.post')
            logger.info(f"Found {len(release_articles)} upcoming release articles")
            
            releases = []
            for article in release_articles[:limit]:
                try:
                    # Extract release data
                    release = self._extract_release_data(article)
                    if release:
                        # Mark as upcoming
                        release['status'] = 'upcoming'
                        releases.append(release)
                        
                    # Add random delay to appear more human-like
                    if self.use_random_delays:
                        random_delay(0.5, 2.0)
                        
                except Exception as e:
                    logger.error(f"Error extracting upcoming release data: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(releases)} upcoming releases")
            return releases
            
        except Exception as e:
            logger.error(f"Error getting upcoming releases: {e}")
            return []
    
    def _extract_release_data(self, article) -> Optional[Dict[str, Any]]:
        """
        Extract release data from an article element.
        
        Args:
            article: BeautifulSoup article element
            
        Returns:
            Dictionary with release data
        """
        try:
            # Get title
            title_elem = article.select_one('h2.entry-title a')
            if not title_elem:
                return None
                
            title = title_elem.get_text().strip()
            url = title_elem['href'] if 'href' in title_elem.attrs else None
            
            # Get image
            img_elem = article.select_one('img.wp-post-image')
            image_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else None
            
            # Get release date from title or content
            release_date = None
            date_match = re.search(r'Release Date[:\s]*([A-Za-z]+\s+\d+[,\s]+\d{4})', article.get_text())
            if date_match:
                release_date = date_match.group(1)
            
            # Get price from title or content
            price = None
            price_match = re.search(r'(\$\d+)', article.get_text())
            if price_match:
                price = price_match.group(1)
            
            # Extract additional info from content
            content_elem = article.select_one('.entry-content')
            content = content_elem.get_text().strip() if content_elem else ""
            
            # Extract SKU/style code
            sku = None
            sku_match = re.search(r'Style(?:\s+Code)?[:\s]*([A-Za-z0-9-]+)', content)
            if sku_match:
                sku = sku_match.group(1)
            
            # Extract brand
            brand = None
            if "Nike" in title or "Air Jordan" in title:
                brand = "Nike"
            elif "Jordan" in title:
                brand = "Jordan"
            elif "adidas" in title or "Adidas" in title or "ADIDAS" in title or "Yeezy" in title:
                brand = "Adidas"
            elif "New Balance" in title:
                brand = "New Balance"
            elif "Puma" in title:
                brand = "Puma"
            elif "Reebok" in title:
                brand = "Reebok"
            elif "ASICS" in title or "Asics" in title:
                brand = "ASICS"
            elif "Converse" in title:
                brand = "Converse"
            elif "Vans" in title:
                brand = "Vans"
            else:
                brand = "Unknown"
            
            # Extract colorway
            colorway = None
            colorway_match = re.search(r'Color(?:way)?[:\s]*([A-Za-z0-9\s-/]+)', content)
            if colorway_match:
                colorway = colorway_match.group(1).strip()
            
            # Create release dictionary
            release = {
                'title': title,
                'url': url,
                'image_url': image_url,
                'release_date': release_date,
                'price': price,
                'sku': sku,
                'brand': brand,
                'colorway': colorway,
                'source': 'KicksOnFire',
                'source_url': self.new_releases_url,
                'status': 'released',
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return release
            
        except Exception as e:
            logger.error(f"Error extracting release data: {e}")
            return None
    
    def get_release_details(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific release.
        
        Args:
            url: URL of the release page
            
        Returns:
            Dictionary with detailed release information
        """
        logger.info(f"Fetching release details from {url}")
        
        try:
            soup = self.get_page(url)
            if not soup:
                logger.error("Failed to get release details page")
                return None
            
            # Get title
            title_elem = soup.select_one('h1.entry-title')
            title = title_elem.get_text().strip() if title_elem else "Unknown Release"
            
            # Get content
            content_elem = soup.select_one('.entry-content')
            content = content_elem.get_text().strip() if content_elem else ""
            
            # Get images
            image_elems = soup.select('.entry-content img')
            images = [img['src'] for img in image_elems if 'src' in img.attrs]
            
            # Extract release date
            release_date = None
            date_match = re.search(r'Release Date[:\s]*([A-Za-z]+\s+\d+[,\s]+\d{4})', content)
            if date_match:
                release_date = date_match.group(1)
            
            # Extract price
            price = None
            price_match = re.search(r'(\$\d+)', content)
            if price_match:
                price = price_match.group(1)
            
            # Extract SKU/style code
            sku = None
            sku_match = re.search(r'Style(?:\s+Code)?[:\s]*([A-Za-z0-9-]+)', content)
            if sku_match:
                sku = sku_match.group(1)
            
            # Extract colorway
            colorway = None
            colorway_match = re.search(r'Color(?:way)?[:\s]*([A-Za-z0-9\s-/]+)', content)
            if colorway_match:
                colorway = colorway_match.group(1).strip()
            
            # Extract brand
            brand = None
            if "Nike" in title or "Air Jordan" in title:
                brand = "Nike"
            elif "Jordan" in title:
                brand = "Jordan"
            elif "adidas" in title or "Adidas" in title or "ADIDAS" in title or "Yeezy" in title:
                brand = "Adidas"
            elif "New Balance" in title:
                brand = "New Balance"
            elif "Puma" in title:
                brand = "Puma"
            elif "Reebok" in title:
                brand = "Reebok"
            elif "ASICS" in title or "Asics" in title:
                brand = "ASICS"
            elif "Converse" in title:
                brand = "Converse"
            elif "Vans" in title:
                brand = "Vans"
            else:
                brand = "Unknown"
            
            # Extract purchase links
            purchase_links = []
            link_elems = soup.select('.entry-content a')
            for link in link_elems:
                if 'href' in link.attrs:
                    href = link['href']
                    # Only include likely purchase links
                    if any(domain in href for domain in ['nike.com', 'adidas.com', 'footlocker.com', 'eastbay.com', 
                                                       'finishline.com', 'stockx.com', 'goat.com', 'champssports.com',
                                                       'sneakersnstuff.com', 'undefeated.com', 'jdsports.com']):
                        purchase_links.append({
                            'url': href,
                            'text': link.get_text().strip()
                        })
            
            # Create detailed release dictionary
            release_details = {
                'title': title,
                'url': url,
                'content': content,
                'images': images,
                'release_date': release_date,
                'price': price,
                'sku': sku,
                'brand': brand,
                'colorway': colorway,
                'purchase_links': purchase_links,
                'source': 'KicksOnFire',
                'source_url': url,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return release_details
            
        except Exception as e:
            logger.error(f"Error getting release details: {e}")
            return None
    
    def search_products(self, keywords=None, category=None):
        """Search for products by keywords or category."""
        if keywords:
            # Implement search by keywords
            search_url = f"{self.base_url}/?s={'+'.join(keywords.split())}"
            logger.info(f"Searching KicksOnFire for: {keywords} at {search_url}")
            
            try:
                soup = self.get_page(search_url)
                if not soup:
                    logger.error("Failed to get search results page")
                    return []
                
                # Find all search result articles
                result_articles = soup.select('article.post')
                logger.info(f"Found {len(result_articles)} search results")
                
                results = []
                for article in result_articles:
                    try:
                        # Extract release data
                        release = self._extract_release_data(article)
                        if release:
                            results.append(release)
                    except Exception as e:
                        logger.error(f"Error extracting search result data: {e}")
                        continue
                
                logger.info(f"Successfully extracted {len(results)} search results")
                return results
                
            except Exception as e:
                logger.error(f"Error searching products: {e}")
                return []
        else:
            # Default to new releases if no keywords provided
            return self.get_new_releases()
    
    def get_product_details(self, product_url):
        """Get detailed information about a specific product."""
        return self.get_release_details(product_url)
    
    def scrape_site(self):
        """Main method to scrape the site for latest releases."""
        logger.info("Starting KicksOnFire scraper...")
        
        try:
            # Get new releases
            new_releases = self.get_new_releases()
            
            # Get upcoming releases
            upcoming_releases = self.get_upcoming_releases()
            
            # Combine all releases
            all_releases = new_releases + upcoming_releases
            
            logger.info(f"Scraped a total of {len(all_releases)} releases from KicksOnFire")
            return all_releases
            
        except Exception as e:
            logger.error(f"Error in KicksOnFire scraper: {e}")
            return []
