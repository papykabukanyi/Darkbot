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
        self.new_releases_url = site_config.get('new_releases_url', 'https://www.kicksonfire.com/category/kicks/new-releases/')
        self.upcoming_url = site_config.get('upcoming_url', 'https://www.kicksonfire.com/category/kicks/upcoming/')
        
        # Configure for anti-ban measures
        self.rate_limit = site_config.get('rate_limit', 10)  # Reduce rate limit to avoid bans
        self.rotate_user_agent = True
        self.use_random_delays = True
    
    def get_new_releases(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get the latest sneaker releases from KicksOnFire homepage.
        
        Args:
            limit: Maximum number of releases to fetch
            
        Returns:
            List of release dictionaries
        """
        logger.info(f"Fetching new releases from {self.new_releases_url}")
        
        try:
            # Validate URL before proceeding
            if not self.validate_url(self.new_releases_url):
                logger.error(f"Invalid new releases URL: {self.new_releases_url}")
                return []
                
            soup = self.get_page(self.new_releases_url)
            if not soup:
                logger.error("Failed to get KicksOnFire homepage")
                return []
            
            # Find all release items using the proper selector structure
            release_items = []
            
            # First try the releases-container structure with the exact CSS selector provided
            releases_container = soup.select_one('#release-filter > div.releases-container')
            if releases_container:
                release_items = releases_container.select('div')
                logger.info(f"Found {len(release_items)} direct child divs in releases-container")
            
            # If nothing found, try the standard release-item-continer class anywhere
            if not release_items:
                release_items = soup.select('div.release-item-continer')
                logger.info(f"Found {len(release_items)} release items with div.release-item-continer")
            
            # Try with the specific nth-child selector approach
            if not release_items or len(release_items) < 5:  # If we found very few items
                logger.info("Trying with specific nth-child selectors")
                all_items = []
                # Try to get each numbered child div
                for i in range(1, 50):  # Try up to 50 items
                    selector = f'#release-filter > div.releases-container > div:nth-child({i})'
                    item = soup.select_one(selector)
                    if item:
                        all_items.append(item)
                
                if all_items:
                    logger.info(f"Found {len(all_items)} items using nth-child approach")
                    release_items = all_items
            
            # If still nothing, try other fallback selectors
            if not release_items:
                logger.warning("No release items found with primary selectors, trying fallbacks")
                # Try alternative selectors
                fallback_selectors = [
                    'div.release-item',
                    'div.post-item',
                    'article.post',
                    '.post',
                    'div:has(span.release-item-title)',
                    'div:has(img):has(a)'
                ]
                
                for selector in fallback_selectors:
                    release_items = soup.select(selector)
                    if release_items:
                        logger.info(f"Found {len(release_items)} release items with fallback selector: {selector}")
                        break
            
            if not release_items:
                logger.error("No release items found on the homepage with any selectors")
                # Last resort - get any divs that might be release items
                potential_items = soup.select('div:has(img)')
                if potential_items:
                    logger.warning(f"Using last resort selector, found {len(potential_items)} potential items")
                    release_items = potential_items
                else:
                    return []
            
            logger.info(f"Processing {min(len(release_items), limit)} release items")
            
            releases = []
            for item in release_items[:limit]:
                try:
                    # Extract release data
                    release = self._extract_release_data_from_homepage(item)
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
            # Validate URL before proceeding
            if not self.validate_url(self.upcoming_url):
                logger.error(f"Invalid upcoming releases URL: {self.upcoming_url}")
                return []
                
            soup = self.get_page(self.upcoming_url)
            if not soup:
                logger.error("Failed to get upcoming releases page")
                return []
            
            # Find all release items using the proper selector structure
            release_items = []
            
            # First try the releases-container structure
            releases_container = soup.select_one('#release-filter > div.releases-container')
            if releases_container:
                release_items = releases_container.select('div.release-item-continer')
                logger.info(f"Found {len(release_items)} upcoming release items in releases-container")
            
            # If nothing found, try the standard release-item-continer class anywhere
            if not release_items:
                release_items = soup.select('div.release-item-continer')
                logger.info(f"Found {len(release_items)} upcoming release items with div.release-item-continer")
            
            # If still nothing, try other fallback selectors
            if not release_items:
                logger.warning("No upcoming release items found with primary selectors, trying fallbacks")
                # Try alternative selectors
                fallback_selectors = [
                    'div.release-item',
                    'div.post-item',
                    'article.post',
                    '.post',
                    '.sneaker-container',
                    '.shoe-container',
                    '.item',
                    'div:has(span.release-item-title)',
                    'div:has(img):has(a)'
                ]
                
                for selector in fallback_selectors:
                    release_items = soup.select(selector)
                    if release_items:
                        logger.info(f"Found {len(release_items)} upcoming release items with fallback selector: {selector}")
                        break
            
            if not release_items:
                logger.error("No upcoming release items found on the page with any selectors")
                # Last resort - get any divs that might be release items
                potential_items = soup.select('div:has(img)')
                if potential_items:
                    logger.warning(f"Using last resort selector, found {len(potential_items)} potential upcoming items")
                    release_items = potential_items
                else:
                    return []
            
            logger.info(f"Processing {min(len(release_items), limit)} upcoming release items")
            
            releases = []
            for item in release_items[:limit]:
                try:
                    # Extract release data
                    release = self._extract_release_data_from_homepage(item)
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
    
    def _extract_release_data_from_homepage(self, article) -> Optional[Dict[str, Any]]:
        """
        Extract release data from KicksOnFire release item container.
        
        Args:
            article: BeautifulSoup article element
            
        Returns:
            Dictionary with release data
        """
        try:
            # First try the typical release-item-continer structure
            link_elem = article.select_one('a.release-item')
            
            # If no link element, try to find any link in the article
            if not link_elem:
                link_elem = article.select_one('a')
                
            if not link_elem:
                logger.warning("No link element found in article, skipping")
                return None
                
            # Get the URL
            url = link_elem.get('href', '')
            if url and not url.startswith('http'):
                # Make sure it's an absolute URL
                if url.startswith('/'):
                    url = f"https://www.kicksonfire.com{url}"
                else:
                    url = f"https://www.kicksonfire.com/{url}"
            
            # Get title from span.release-item-title
            title_elem = link_elem.select_one('span.release-item-title')
            
            # If no title element in the link, try in the article
            if not title_elem:
                title_elem = article.select_one('span.release-item-title')
                
            # If still no title, try to extract from any text or alt attribute
            if not title_elem:
                # Try to get from img alt attribute
                img_elem = link_elem.select_one('img') or article.select_one('img')
                if img_elem and img_elem.get('alt'):
                    title = img_elem.get('alt').strip()
                else:
                    # Last resort: use link text
                    title = link_elem.get_text().strip()
            else:
                title = title_elem.get_text().strip()
            
            # Skip items without valid titles or with generic titles
            if not title or title.lower() in ['new', 'brands', '']:
                logger.warning(f"Invalid or generic title found: {title}")
                return None
            
            # Get price from span.release-price-from
            price_elem = link_elem.select_one('span.release-price-from')
            if not price_elem:
                price_elem = article.select_one('span.release-price-from')
                
            price = None
            if price_elem:
                price_text = price_elem.get_text().strip()
                price = self._extract_price(price_text)
                logger.info(f"Found price: {price} from text: {price_text}")
            else:
                # Try to find price anywhere in the container
                price_text = None
                price_patterns = [
                    r'\$\d+(?:\.\d+)?',  # $339 or $339.99
                    r'retail[:\s]+\$?\d+(?:\.\d+)?',  # Retail: $339 or Retail: 339
                    r'price[:\s]+\$?\d+(?:\.\d+)?'    # Price: $339 or Price: 339
                ]
                
                article_text = article.get_text()
                for pattern in price_patterns:
                    match = re.search(pattern, article_text, re.IGNORECASE)
                    if match:
                        price_text = match.group(0)
                        break
                
                if price_text:
                    logger.info(f"Found alternative price text: '{price_text}' for {title}")
                    price = self._extract_price(price_text)
                    logger.info(f"Extracted alternative price: {price}")
                else:
                    logger.warning(f"No price found for release: {title}")
            
            # Get image from the img tag
            img_elem = link_elem.select_one('span.release-item-image img')
            if not img_elem:
                img_elem = link_elem.select_one('img')
            if not img_elem:
                img_elem = article.select_one('img')
                
            image_url = None
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-original')
                
                # Fix relative URLs
                if image_url and not image_url.startswith(('http://', 'https://')):
                    image_url = f"https://www.kicksonfire.com{image_url if image_url.startswith('/') else '/' + image_url}"
            
            # Extract date from title or article
            date_text = None
            
            # Look for common date formats in the title or article text
            date_patterns = [
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}',  # Aug 1
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}',  # August 1
                r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}'  # MM/DD/YYYY or DD/MM/YYYY
            ]
            
            article_text = article.get_text()
            for pattern in date_patterns:
                date_match = re.search(pattern, article_text)
                if date_match:
                    date_text = date_match.group(0)
                    break
            
            # Extract brand from title
            brand = self._extract_brand_from_title(title)
            
            # Try to extract SKU/style code from the URL or title
            sku = self._extract_sku_from_url(url) or self._extract_sku_from_title(title)
            
            # Create release object
            release = {
                'title': title.strip(),
                'brand': brand,
                'url': url,
                'image_url': image_url,
                'release_date': date_text or self._extract_date_from_title(title),
                'retail_price': price,
                'sku': sku,
                'source': 'KicksOnFire',
                'source_url': url,
                'timestamp': datetime.now().isoformat(),
                'status': 'new'
            }
            
            # If we don't have an SKU and have a URL, we'll do a detailed page fetch
            # to try to get more information (particularly the SKU)
            if not sku and url:
                try:
                    logger.info(f"Fetching additional details for {title} from {url}")
                    detail_soup = self.get_page(url)
                    if detail_soup:
                        # Look for SKU in product details
                        sku_elem = detail_soup.select_one('.product-details .sku') or detail_soup.select_one('.product-details .style-code')
                        if sku_elem:
                            sku_text = sku_elem.get_text().strip()
                            sku_match = re.search(r'(SKU|Style)[:\s]+([A-Z0-9-]+)', sku_text, re.IGNORECASE)
                            if sku_match:
                                release['sku'] = sku_match.group(2)
                                logger.info(f"Found SKU {release['sku']} from detail page")
                                
                        # If we still don't have a price, look in the details
                        if not price:
                            price_elem = detail_soup.select_one('.product-price')
                            if price_elem:
                                price_text = price_elem.get_text().strip()
                                release['retail_price'] = self._extract_price(price_text)
                except Exception as e:
                    logger.error(f"Error fetching additional details: {e}")
            
            # Generate a synthetic SKU if we still don't have one
            if not release['sku'] and brand:
                # Clean title of special characters
                clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
                # Create SKU from brand prefix + first letters of each word + date code
                words = clean_title.split()
                if len(words) >= 2:
                    brand_prefix = brand[:2].upper()
                    model_suffix = ''.join([w[0].upper() for w in words if w.lower() != brand.lower()])[:4]
                    synthetic_sku = f"{brand_prefix}{model_suffix}-{datetime.now().strftime('%m%d')}"
                    release['sku'] = synthetic_sku
                    logger.info(f"Generated synthetic SKU {synthetic_sku} for {title}")
            
            logger.info(f"Extracted release: {release['title']} (SKU: {release['sku']}, Price: {release['retail_price']})")
            return release
            
        except Exception as e:
            logger.error(f"Error extracting release data from KicksOnFire item: {e}")
            return None
            
    def _extract_brand_from_title(self, title):
        """Extract brand from title."""
        common_brands = ['Nike', 'Adidas', 'Jordan', 'Yeezy', 'New Balance', 'Reebok', 'Puma', 'Under Armour', 'Converse']
        for brand in common_brands:
            if brand.lower() in title.lower():
                return brand
        return "Unknown"
        
    def _extract_date_from_title(self, title):
        """Extract release date from title text."""
        # Look for date patterns in the title
        date_match = re.search(r'([A-Za-z]+\s+\d+(?:st|nd|rd|th)?(?:,\s+)?\d{4})', title)
        if date_match:
            return date_match.group(1)
        return None
        
    def _extract_sku_from_url(self, url):
        """Extract SKU from URL if possible."""
        try:
            # Look for SKU patterns in URL
            sku_match = re.search(r'([A-Z]{2}\d{4}-\d{3}|[A-Z0-9]{6,10})', url.upper())
            if sku_match:
                return sku_match.group(1)
        except Exception:
            pass
        return None
        
    def _extract_sku_from_title(self, title):
        """Extract SKU from title if present."""
        try:
            # Check if we have a valid title
            if not title or len(title) < 5:
                return None
                
            # Extract brand from title first
            brand = self._extract_brand_from_title(title)
            
            # Look for common SKU patterns
            sku_patterns = [
                r'([A-Z]{2}\d{4}-\d{3})',    # Nike format: AA1234-567
                r'([A-Z]{2,3}\d{4,6})',      # General alphanumeric code
                r'([A-Z0-9]{6,10}[-][0-9]{3})', # Format like CW2288-111
                r'Style[:\s]+([A-Z0-9-]+)',  # Style: ABC123
                r'SKU[:\s]+([A-Z0-9-]+)',    # SKU: ABC123
                r'#([A-Z0-9]{6,10})',        # #ABC123
                r'([A-Z]{2}[0-9]{4})'        # AJ1234 format
            ]
            
            for pattern in sku_patterns:
                match = re.search(pattern, title.upper())
                if match:
                    return match.group(1)
            
            # If we couldn't find a SKU and have a brand, generate a synthetic SKU
            # This helps with StockX lookups
            if brand:
                # Clean title of special characters
                clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
                # Create SKU from brand prefix + first letters of each word
                words = clean_title.split()
                if len(words) >= 2:
                    brand_prefix = brand[:2].upper()
                    model_suffix = ''.join([w[0].upper() for w in words if w.lower() != brand.lower()])[:4]
                    synthetic_sku = f"{brand_prefix}{model_suffix}-{datetime.now().strftime('%m%d')}"
                    logger.info(f"Generated synthetic SKU {synthetic_sku} for {title}")
                    return synthetic_sku
        except Exception as e:
            logger.error(f"Error extracting SKU from title: {e}")
        return None
        
    def _parse_date(self, date_text):
        """Parse date from various text formats."""
        try:
            # Strip ordinal indicators (st, nd, rd, th)
            date_text = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_text)
            # Try different date formats
            for fmt in ['%B %d %Y', '%b %d %Y', '%B %d, %Y', '%b %d, %Y']:
                try:
                    return datetime.strptime(date_text, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
        except Exception:
            pass
        return date_text
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
            brand = self._extract_brand_from_title(title)
            
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
    
    def _extract_price(self, price_text):
        """Extract price from text."""
        if not price_text:
            return None
            
        try:
            # Look for price pattern with the $ symbol (e.g., $339, $160.50)
            price_match = re.search(r'\$(\d+(?:\.\d+)?)', price_text)
            if price_match:
                return float(price_match.group(1))
                
            # Try with just digits (in case $ is missing)
            digit_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
            if digit_match:
                return float(digit_match.group(1))
                
            # If all else fails, try to extract any numbers
            clean_price = re.sub(r'[^0-9.]', '', price_text)
            if clean_price:
                return float(clean_price)
                
        except Exception as e:
            logger.error(f"Error extracting price from '{price_text}': {e}")
        
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
    
    def get_releases(self, limit: int = 40) -> List[Dict[str, Any]]:
        """
        Get all releases (both new and upcoming) from KicksOnFire.
        
        This method implements the abstract method from BaseSneakerScraper.
        
        Args:
            limit: Maximum number of releases to fetch (distributed between new and upcoming)
            
        Returns:
            List of release dictionaries
        """
        logger.info(f"Fetching all releases from KicksOnFire")
        
        try:
            # Calculate limit for each type to maintain the total limit
            per_type_limit = limit // 2
            
            # Get new releases
            new_releases = self.get_new_releases(limit=per_type_limit)
            
            # Add random delay between requests to mimic human behavior
            if self.use_random_delays:
                random_delay(2.0, 5.0)
                
            # Get upcoming releases
            upcoming_releases = self.get_upcoming_releases(limit=per_type_limit)
            
            # Combine all releases and remove duplicates based on title
            # This is important because some releases might appear in both new and upcoming sections
            all_releases = []
            seen_titles = set()
            
            for release in new_releases + upcoming_releases:
                title = release.get('title', '')
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_releases.append(release)
            
            logger.info(f"Successfully fetched {len(all_releases)} unique releases")
            return all_releases
            
        except Exception as e:
            logger.error(f"Error getting all releases: {e}")
            return []
            
    def get_releases_with_scrolling(self, limit: int = 40) -> List[Dict[str, Any]]:
        """
        Get releases from KicksOnFire with virtual scrolling to load more content.
        
        Args:
            limit: Maximum number of releases to fetch
            
        Returns:
            List of release dictionaries
        """
        logger.info(f"Fetching releases with scrolling from {self.new_releases_url}")
        
        try:
            # For scrolling, we need to use a headless browser, which we don't have in this code.
            # Since we can't scroll without a browser, we'll use a simulation approach:
            # 1. First try the main page
            # 2. Then try page 2, page 3, etc. by adding URL parameters
            
            all_releases = []
            seen_titles = set()
            
            # Try the main page first
            releases = self.get_new_releases(limit=limit)
            
            # Add unique releases
            for release in releases:
                title = release.get('title', '')
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_releases.append(release)
            
            # If we need more releases, try pagination
            if len(all_releases) < limit:
                remaining = limit - len(all_releases)
                page = 2
                
                while remaining > 0 and page <= 5:  # Try up to 5 pages
                    # Construct pagination URL
                    page_url = f"{self.new_releases_url}?page={page}"
                    logger.info(f"Fetching page {page} from {page_url}")
                    
                    # Configure for this request
                    self.current_url = page_url
                    
                    # Try to get the page
                    soup = self.get_page(page_url)
                    if not soup:
                        logger.error(f"Failed to get page {page}")
                        break
                    
                    # Find all release items
                    release_items = []
                    
                    # Check for releases container
                    releases_container = soup.select_one('#release-filter > div.releases-container')
                    if releases_container:
                        release_items = releases_container.select('div.release-item-continer')
                    
                    # If nothing found, try direct selection
                    if not release_items:
                        release_items = soup.select('div.release-item-continer')
                    
                    # If still nothing, try fallbacks
                    if not release_items:
                        for selector in ['div.release-item', 'div:has(span.release-item-title)', 'div:has(img):has(a)']:
                            release_items = soup.select(selector)
                            if release_items:
                                break
                    
                    if not release_items:
                        logger.warning(f"No release items found on page {page}")
                        break
                    
                    # Process items
                    page_releases = []
                    for item in release_items:
                        try:
                            release = self._extract_release_data_from_homepage(item)
                            if release:
                                page_releases.append(release)
                                
                            # Add random delay
                            if self.use_random_delays:
                                random_delay(0.5, 1.5)
                        except Exception as e:
                            logger.error(f"Error extracting release data on page {page}: {e}")
                    
                    # Add unique releases from this page
                    new_count = 0
                    for release in page_releases:
                        title = release.get('title', '')
                        if title and title not in seen_titles:
                            seen_titles.add(title)
                            all_releases.append(release)
                            new_count += 1
                            remaining -= 1
                            if remaining <= 0:
                                break
                    
                    logger.info(f"Added {new_count} new releases from page {page}")
                    
                    # If we didn't find any new releases, stop paginating
                    if new_count == 0:
                        break
                    
                    # Move to next page
                    page += 1
                    
                    # Add delay between pages to mimic human behavior
                    random_delay(3.0, 5.0)
            
            logger.info(f"Successfully fetched {len(all_releases)} releases with pagination")
            return all_releases[:limit]
            
        except Exception as e:
            logger.error(f"Error getting releases with scrolling: {e}")
            return []
    
    def get_product_details(self, product_url):
        """Get detailed information about a specific product."""
        return self.get_release_details(product_url)
    
    def get_releases_with_scrolling(self, limit=50):
        """
        Enhanced method to get releases with scrolling and pagination.
        
        Args:
            limit: Maximum number of releases to fetch
            
        Returns:
            List of release dictionaries
        """
        logger.info(f"Getting releases with scrolling (limit: {limit})")
        
        all_releases = []
        seen_titles = set()
        
        try:
            # First try the main page with specific nth-child selectors
            all_items = []
            soup = self.get_page(self.new_releases_url)
            if soup:
                logger.info("Using nth-child selectors to get release items")
                
                # Try to get each numbered child div
                for i in range(1, 100):  # Try up to 100 items
                    selector = f'#release-filter > div.releases-container > div:nth-child({i})'
                    item = soup.select_one(selector)
                    if item:
                        all_items.append(item)
                
                logger.info(f"Found {len(all_items)} items using nth-child approach")
                
                # Process items
                for item in all_items[:limit]:
                    try:
                        release = self._extract_release_data_from_homepage(item)
                        if release:
                            title = release.get('title', '')
                            if title and title not in seen_titles:
                                seen_titles.add(title)
                                all_releases.append(release)
                                
                        # Add delay between processing items
                        if self.use_random_delays:
                            random_delay(0.3, 0.7)
                            
                    except Exception as e:
                        logger.error(f"Error extracting release data: {e}")
                        continue
            
            # If we found no releases, try standard methods
            if not all_releases:
                logger.info("No releases found with nth-child approach, trying standard methods")
                standard_releases = self.get_releases(limit=limit)
                all_releases = standard_releases
            
            # Limit the total number of releases
            logger.info(f"Found {len(all_releases)} total releases with scrolling")
            return all_releases[:limit]
            
        except Exception as e:
            logger.error(f"Error getting releases with scrolling: {e}")
            # Fall back to standard method
            try:
                standard_releases = self.get_releases(limit=limit)
                return standard_releases
            except Exception:
                return []
    
    def scrape_site(self):
        """Main method to scrape the site for latest releases."""
        logger.info("Starting KicksOnFire scraper...")
        
        try:
            # Use the improved method that simulates scrolling with pagination
            all_releases = self.get_releases_with_scrolling(limit=50)
            
            logger.info(f"Scraped a total of {len(all_releases)} releases from KicksOnFire")
            return all_releases
            
        except Exception as e:
            logger.error(f"Error in KicksOnFire scraper: {e}")
            return []
