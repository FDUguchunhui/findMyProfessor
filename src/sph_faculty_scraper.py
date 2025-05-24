from bs4 import BeautifulSoup
import requests
import json
from typing import Dict, List, Optional
from typing_extensions import override
import time
from urllib.parse import urljoin
from summarize import summarize
from faculty_scraper import FacultyScraper

class SPHFacultyScraper(FacultyScraper):
    """A class to scrape faculty information from SPH websites."""
    
    def __init__(self, base_url: str, delay: float = 0.1,
                  debug: bool = False):
        """
        Initialize the FacultyScraper.
        
        Args:
            base_url (str): Base URL of the faculty website
            delay (float): Delay between requests in seconds
        """
        super().__init__(base_url, delay, debug)
        
    
    
    def _extract_faculty_basic_info(self, faculty_div) -> Dict:
        """
        Extract basic faculty information from data attributes.
        
        Args:
            faculty_div: BeautifulSoup element containing faculty info
            
        Returns:
            Dict: Basic faculty information
        """
        return {
            'id': faculty_div.get('data-id', ''),
            'first_name': faculty_div.get('data-first', ''),
            'last_name': faculty_div.get('data-last', ''),
            'campus': faculty_div.get('data-campus', ''),
            'department': faculty_div.get('data-department', ''),
            'center': faculty_div.get('data-center', ''),
            'research_interests': faculty_div.get('data-interest', '')
        }
    
    def _extract_image_url(self, faculty_div) -> Optional[str]:
        """
        Extract faculty image URL.
        
        Args:
            faculty_div: BeautifulSoup element containing faculty info
            
        Returns:
            Optional[str]: Image URL if found, None otherwise
        """
        img_tag = faculty_div.find('img')
        if img_tag:
            img_url = img_tag.get('src', '')
            if img_url:
                return self.get_absolute_url(self.base_url, img_url)
        return None
    
    @override
    def _get_faculty_divs(self) -> List:
        faculty_divs = self.soup.find_all('div', class_='cell fac-sort')
        return faculty_divs
    

    @override
    def _extract_name(self, faculty_div) -> Dict:
        """
        Extract faculty name, title, and profile information.
        
        Args:
            faculty_div: BeautifulSoup element containing faculty info
            
        Returns:
            Dict: Name and profile information
        """
        first_name = faculty_div.get('data-first', '')
        last_name = faculty_div.get('data-last', '')
        name = f"{first_name} {last_name}"
        
        return name
    
    def _extract_profile_url(self, faculty_div) -> Dict:
        '''
        Extract the profile url from the faculty div
        '''
        profile_url = faculty_div.find('a')['href']
        profile_url = self.get_absolute_url(self.base_url, profile_url)
        return profile_url
    

def main():
    """Main function to run the faculty scraper."""
    base_url = 'https://sph.uth.edu/faculty/'
    
    # Create scraper instance and run
    scraper = SPHFacultyScraper(base_url, debug=True)
    faculty_list = scraper.scrape_faculty_list()
    # dump the faculty list as jsonl file
    with open('data/faculty_list.jsonl', 'w') as f:
        for faculty in faculty_list:
            f.write(json.dumps(faculty) + '\n')


if __name__ == "__main__":
    main() 