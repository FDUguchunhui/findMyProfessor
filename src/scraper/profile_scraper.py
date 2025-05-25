import requests
from bs4 import BeautifulSoup

# Headers for web scraping
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class FacultyProfileScraper:
    def __init__(self, url):
        """
        Create this FacultyProfileScraper object from the given URL, 
        specifically designed for faculty directory pages
        """
        self.url = url
        self.response = requests.get(url, headers=headers)
        self.soup = BeautifulSoup(self.response.content, 'html.parser')
        
        # Extract title
        self.title = self.soup.title.string if self.soup.title else "No title found"
        
        # Remove irrelevant elements
        self._remove_irrelevant_content(self.soup)
        
        self.text = self.soup.body.get_text(separator="\n", strip=True) if self.soup.body else "No content found"
        
        # Clean up extra whitespace and empty lines
        self.text = self._clean_text(self.text)

        self.links = self._extract_links(self.soup)
    
    def _remove_irrelevant_content(self, soup):
        """
        Remove navigation, footer, scripts, styles, and other irrelevant content
        """
        # Remove all script, style, img, input elements
        for element in soup(["script", "style", "img", "input", "noscript"]):
            element.decompose()
        
        # Remove header/navigation (usually contains masthead, navigation menus)
        for header in soup.find_all(['header', 'nav']):
            header.decompose()
        
        # Remove footer
        for footer in soup.find_all('footer'):
            footer.decompose()
        
        # Remove elements with navigation-related classes/ids
        nav_selectors = [
            'div[id*="nav"]', 'div[class*="nav"]', 'div[class*="menu"]',
            'div[id*="utility"]', 'div[class*="utility"]',
            'div[id*="masthead"]', 'div[class*="masthead"]',
            'ul[class*="menu"]', 'li[class*="mega-menu"]'
        ]
        
        for selector in nav_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Remove common unnecessary elements by class or id
        unnecessary_selectors = [
            '.skipNav', '.show-for-sr', '.hide', '.hidden',
            '[data-toggle]', '[data-reveal]', '[data-dropdown]'
        ]
        
        for selector in unnecessary_selectors:
            for element in soup.select(selector):
                element.decompose()
    
    def _clean_text(self, text):
        """
        Clean up the extracted text by removing extra whitespace and empty lines
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line:  # Only add non-empty lines
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_links(self, soup):
        """
        Extract PubMed and website links from the profile page.
        
        Returns:
            Dict: Dictionary containing PubMed and website links
        """
        links = {}
        
        # Find all links
        for link in soup.find_all('a'):
            href = link.get('href', '')
            title = link.get('title', '').lower()
            text = link.get_text().strip().lower()
            
            # Check for PubMed link
            if 'pubmed' in href.lower() or 'pubmed' in title or 'pubmed' in text:
                links['pubmed'] = href
            if 'google scholar' in href.lower() or 'google scholar' in title or 'google scholar' in text:
                links['google scholar'] = href
            # Check for website link
            elif 'website' in title or 'website' in text:
                links['website'] = href
                
        return links
    
    def get_profile_info(self):
        """
        Extract structured information about the faculty member
        """
        # Get links

        
        return {
            'url': self.url,
            'title': self.title,
            'content': self.text,
            'links': links
        }

# Usage example:
# scraper = FacultyProfileScraper("https://gsbs.uth.edu/directory/profile?id=e1034955-4e01-4cd2-8a4f-ffdca8fa5943")
# profile_info = scraper.get_profile_info()
# print(profile_info['content'])
if __name__ == "__main__":
    scraper = FacultyProfileScraper("https://sph.uth.edu/faculty/?fac=O5VHhdEYnwuzkAQcMguuOA==")
    profile_info = scraper.get_profile_info()
    print(profile_info['content'])