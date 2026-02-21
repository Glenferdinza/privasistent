"""
Web Scraper dengan security dan rate limiting
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import Tuple, Optional
from urllib.parse import urlparse
import time
from collections import deque
import gc

logger = logging.getLogger(__name__)


class WebScraper:
    """Web scraper dengan whitelist domain dan rate limiting"""
    
    def __init__(self, allowed_domains: list, timeout: int = 5, 
                 max_requests_per_minute: int = 10):
        """
        Args:
            allowed_domains: List domain yang diizinkan
            timeout: Request timeout dalam detik
            max_requests_per_minute: Rate limit
        """
        self.allowed_domains = allowed_domains
        self.timeout = timeout
        self.max_requests = max_requests_per_minute
        
        # Rate limiting tracking
        self.request_times = deque(maxlen=max_requests_per_minute)
        
        logger.info(f"Web scraper initialized with domains: {allowed_domains}")
    
    def _is_domain_allowed(self, url: str) -> bool:
        """Check apakah domain diizinkan"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check against whitelist
            for allowed in self.allowed_domains:
                if allowed.lower() in domain or domain in allowed.lower():
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to parse URL {url}: {e}")
            return False
    
    def _check_rate_limit(self) -> Tuple[bool, str]:
        """Check rate limiting"""
        current_time = time.time()
        
        # Remove old requests (older than 1 minute)
        while self.request_times and current_time - self.request_times[0] > 60:
            self.request_times.popleft()
        
        # Check if limit exceeded
        if len(self.request_times) >= self.max_requests:
            wait_time = 60 - (current_time - self.request_times[0])
            return False, f"Rate limit tercapai. Tunggu {int(wait_time)} detik."
        
        # Add current request
        self.request_times.append(current_time)
        return True, "OK"
    
    def fetch_url(self, url: str) -> Tuple[bool, str]:
        """
        Fetch content dari URL
        
        Args:
            url: URL yang akan diakses
            
        Returns:
            Tuple (success, content_or_error)
        """
        # Validate domain
        if not self._is_domain_allowed(url):
            logger.warning(f"Domain not allowed: {url}")
            return False, "Domain tidak ada dalam whitelist yang diizinkan."
        
        # Check rate limit
        can_proceed, message = self._check_rate_limit()
        if not can_proceed:
            return False, message
        
        try:
            logger.info(f"Fetching URL: {url}")
            
            # Add headers untuk avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
            }
            
            # Make request
            response = requests.get(
                url,
                timeout=self.timeout,
                headers=headers,
                verify=True  # Validate SSL
            )
            
            response.raise_for_status()
            
            # Parse content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit text length
            max_length = 2000
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            logger.info(f"URL fetched successfully: {url}")
            return True, text
            
        except requests.Timeout:
            return False, "Timeout saat mengakses URL."
        except requests.ConnectionError:
            return False, "Tidak dapat terhubung ke server."
        except requests.HTTPError as e:
            return False, f"HTTP error: {e.response.status_code}"
        except Exception as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            return False, f"Gagal mengakses URL: {str(e)}"
        finally:
            gc.collect()
    
    def search_wikipedia(self, query: str) -> Tuple[bool, str]:
        """
        Search Wikipedia (simplified)
        
        Args:
            query: Search query
            
        Returns:
            Tuple (success, result_or_error)
        """
        # Construct Wikipedia URL
        wiki_url = f"https://id.wikipedia.org/wiki/{query.replace(' ', '_')}"
        
        success, content = self.fetch_url(wiki_url)
        
        if not success:
            # Try English Wikipedia
            wiki_url = f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
            success, content = self.fetch_url(wiki_url)
        
        return success, content


class WebScraperManager:
    """Singleton manager untuk web scraper"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'scraper'):
            from config import ALLOWED_DOMAINS, WEB_REQUEST_TIMEOUT, MAX_REQUESTS_PER_MINUTE
            self.scraper = WebScraper(
                allowed_domains=ALLOWED_DOMAINS,
                timeout=WEB_REQUEST_TIMEOUT,
                max_requests_per_minute=MAX_REQUESTS_PER_MINUTE
            )
    
    def fetch(self, url: str) -> Tuple[bool, str]:
        """Fetch URL wrapper"""
        return self.scraper.fetch_url(url)
    
    def search_wiki(self, query: str) -> Tuple[bool, str]:
        """Search Wikipedia wrapper"""
        return self.scraper.search_wikipedia(query)
