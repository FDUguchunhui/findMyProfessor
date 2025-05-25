from bs4 import BeautifulSoup
import requests
import json
from typing import Dict, List, Optional
from typing_extensions import override
import time
from urllib.parse import urljoin
from faculty_scraper import FacultyScraper

class GSBSFacultyScraper(FacultyScraper):
    """A class to scrape faculty information from GSBS websites."""
    
    def __init__(self, base_url: str = "https://gsbs.uth.edu/directory/", 
                 delay: float = 0.1, debug: bool = False):
        """
        Initialize the GSBS FacultyScraper.
        
        Args:
            base_url (str): Base URL of the GSBS directory website
            delay (float): Delay between requests in seconds
            debug (bool): Enable debug mode (limits to first 5 faculty)
        """
        super().__init__(base_url, delay, debug)
    
    @override
    def _get_faculty_divs(self) -> List:
        """
        Get faculty divs from the GSBS directory page.
        
        Returns:
            List: List of faculty divs
        """
        # GSBS uses <a> tags with class "cell callout grid-x" for each faculty member
        faculty_divs = self.soup.find_all('a', class_='cell callout grid-x')
        return faculty_divs
    
    @override
    def _extract_name(self, faculty_div) -> Optional[str]:
        """
        Extract faculty name from the faculty div.
        
        Args:
            faculty_div: BeautifulSoup element containing faculty info
            
        Returns:
            Optional[str]: Faculty name if found, None otherwise
        """
        # GSBS stores name in <span class="name"><strong>Name</strong></span>
        name_span = faculty_div.find('span', class_='name')
        if name_span:
            strong_tag = name_span.find('strong')
            if strong_tag:
                return strong_tag.get_text().strip()
        return None
    
    @override
    def _extract_profile_url(self, faculty_div) -> Optional[str]:
        """
        Extract the profile URL from the faculty div.
        
        Args:
            faculty_div: BeautifulSoup element containing faculty info
            
        Returns:
            Optional[str]: Profile URL if found, None otherwise
        """
        # GSBS stores the profile URL in the href attribute of the main <a> tag
        href = faculty_div.get('href')
        if href:
            return self.get_absolute_url(self.base_url, href)
        return None
    
    @override
    def _extract_image_url(self, faculty_div) -> Optional[str]:
        """
        Extract faculty image URL.
        
        Args:
            faculty_div: BeautifulSoup element containing faculty info
            
        Returns:
            Optional[str]: Image URL if found, None otherwise
        """
        # GSBS stores image in the background-style of profile__picture div
        profile_picture_div = faculty_div.find('div', class_='profile__picture')
        if profile_picture_div:
            style = profile_picture_div.get('style', '')
            if 'background:url(' in style:
                # Extract URL from style attribute
                start = style.find("background:url('") + len("background:url('")
                end = style.find("')", start)
                if start != -1 and end != -1:
                    img_url = style[start:end]
                    return self.get_absolute_url(self.base_url, img_url)
        return None
    
    def _extract_position(self, faculty_div) -> Optional[str]:
        """
        Extract faculty position/label.
        
        Args:
            faculty_div: BeautifulSoup element containing faculty info
            
        Returns:
            Optional[str]: Position if found, None otherwise
        """
        labels_span = faculty_div.find('span', class_='labels')
        if labels_span:
            return labels_span.get_text().strip()
        return None
    
    def _get_next_page_url(self) -> Optional[str]:
        """
        Get the URL for the next page if pagination exists.
        
        Returns:
            Optional[str]: Next page URL if found, None otherwise
        """
        # Look for the specific pagination structure used by GSBS
        # The next page link is in a div with class "small-4 cell" and contains an <a> with "Next Page" text
        next_link = self.soup.find('a', class_='next')
        
        if not next_link:
            # Alternative: look for link containing "Next Page" text
            next_link = self.soup.find('a', string=lambda text: text and 'Next Page' in text)
        
        if next_link and 'href' in next_link.attrs:
            href = next_link['href']
            # Convert relative URL to absolute URL
            return self.get_absolute_url(self.base_url, href)
        
        return None

    @override
    def scrape_faculty_list(self) -> List[Dict]:
        """
        Scrape faculty information from all pages of the GSBS directory.
        
        Returns:
            List[Dict]: List of dictionaries containing faculty information
        """
        faculty_list = []
        current_url = self.base_url
        page_num = 1
        
        while current_url:
            print(f"Scraping page {page_num}...")
            
            # Get page content
            response = requests.get(current_url)
            if response.status_code != 200:
                print(f"Failed to load page {page_num}: {current_url}")
                break
                
            self.soup = BeautifulSoup(response.content, 'html.parser')
            faculty_divs = self._get_faculty_divs()

            if self.debug and page_num == 1:
                faculty_divs = faculty_divs[:5]
                print(f"Debug: Only scraping first 5 faculty members from first page")
            
            # Process faculty on current page
            for i, faculty_div in enumerate(faculty_divs):
                faculty_info = {}

                # Add delay between each professor
                if len(faculty_list) > 0 or i > 0:
                    time.sleep(self.delay)
        
                # Extract image URL
                image_url = self._extract_image_url(faculty_div)
                if image_url:
                    faculty_info['image_url'] = image_url
                    
                # Extract name
                name = self._extract_name(faculty_div)
                if name:
                    faculty_info['name'] = name
                
                # Extract position/label
                position = self._extract_position(faculty_div)
                if position:
                    faculty_info['position'] = position

                # Extract profile URL and get profile summary
                profile_url = self._extract_profile_url(faculty_div)
                if profile_url:
                    profile = self._get_faculty_profile(profile_url)
                    faculty_info['profile'] = profile.text
                    faculty_info['links'] = profile.links
                    faculty_info['profile_url'] = profile_url
                
                faculty_list.append(faculty_info)
                print(f"Processed {len(faculty_list)} faculty members total")
            
            # Check for next page (unless in debug mode)
            if self.debug:
                break
                
            next_url = self._get_next_page_url()
            if next_url and next_url != current_url:
                current_url = next_url
                page_num += 1
                # Add delay between pages
                time.sleep(self.delay * 2)
            else:
                current_url = None
        
        print(f"Completed scraping {page_num} page(s), total faculty: {len(faculty_list)}")
        self.faculty_list = faculty_list


def main():
    """Main function to run the GSBS faculty scraper."""
    base_url = 'https://gsbs.uth.edu/directory/'
    
    # Create scraper instance and run
    scraper = GSBSFacultyScraper(base_url, debug=False)
    faculty_list = scraper.scrape_faculty_list()
    
    # Save the faculty list as jsonl file
    scraper.save_to_jsonl('data/gsbs_faculty_list.jsonl')


if __name__ == "__main__":
    main()
