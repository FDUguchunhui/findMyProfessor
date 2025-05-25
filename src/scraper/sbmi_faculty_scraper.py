from bs4 import BeautifulSoup
import requests
import json
from typing import Dict, List, Optional
from typing_extensions import override
import time
from urllib.parse import urljoin
from summarize import summarize
from src.scraper.faculty_scraper import FacultyScraper

class SBMIFacultyScraper(FacultyScraper):
    """A class to scrape faculty information from SBMI websites."""
    
    def __init__(self, base_url: str = "https://sbmi.uth.edu/faculty/", 
                 delay: float = 0.1, debug: bool = False):
        """
        Initialize the SBMI FacultyScraper.
        
        Args:
            base_url (str): Base URL of the SBMI faculty website
            delay (float): Delay between requests in seconds
            debug (bool): Enable debug mode (limits to first 5 faculty)
        """
        super().__init__(base_url, delay, debug)
    
    @override
    def _get_faculty_divs(self) -> List:
        """
        Get faculty divs from the SBMI faculty page.
        
        Returns:
            List: List of faculty divs
        """
        # Look for divs with onclick attributes that contain faculty URLs
        faculty_divs = self.soup.find_all('div', attrs={'onclick': lambda x: x and 'window.location' in x and 'faculty-and-staff' in x})
        
        # Filter out empty or invalid divs
        return [div for div in faculty_divs if div and div.get_text().strip()]
    
    @override
    def _extract_name(self, faculty_div) -> Optional[str]:
        """
        Extract faculty name from the faculty div.
        
        Args:
            faculty_div: BeautifulSoup element containing faculty info
            
        Returns:
            Optional[str]: Faculty name if found, None otherwise
        """
        # Look for the name in the fac-nam span
        name_element = faculty_div.select_one('.fac-nam strong')
        if name_element:
            name = name_element.get_text().strip()
            # Clean up common title patterns and suffixes
            name = self._clean_name(name)
            if name and len(name) > 2 and ' ' in name:  # Ensure it's a full name
                return name
                
        return None
    
    def _clean_name(self, name: str) -> str:
        """Clean and normalize faculty names."""
        if not name:
            return ""
        
        # Remove common titles and suffixes
        name = name.split(',')[0]  # Remove everything after comma
        
        # Remove common academic titles and degrees
        remove_patterns = [
            'PhD', 'MD', 'Ph.D.', 'M.D.', 'Dr.', 'Professor', 'Prof.',
            'Assistant Professor', 'Associate Professor', 'Lecturer',
            'Emeritus', 'Chair', 'Director', 'Dean'
        ]
        
        for pattern in remove_patterns:
            name = name.replace(pattern, '').strip()
        
        # Clean up extra whitespace
        name = ' '.join(name.split())
        
        return name.strip()
    
    def _extract_areas_of_expertise(self, faculty_div) -> List[str]:
        """
        Extract areas of expertise from the faculty div.
        
        Args:
            faculty_div: BeautifulSoup element containing faculty info
            
        Returns:
            List[str]: List of areas of expertise
        """
        areas = []
        # Look for text after "Areas of Expertise" and before "click for full bio"
        text_content = faculty_div.get_text()
        if "Areas of Expertise" in text_content:
            expertise_section = text_content.split("Areas of Expertise")[1].split("click for full bio")[0]
            # Split by "»" and clean up each area
            for line in expertise_section.split("»"):
                area = line.strip()
                if area and not area.startswith("click for full bio"):
                    areas.append(area.strip())
        return areas
    
    @override
    def _extract_position(self, faculty_div) -> Optional[str]:
        """
        Extract faculty position/title.
        
        Args:
            faculty_div: BeautifulSoup element containing faculty info
            
        Returns:
            Optional[str]: Position if found, None otherwise
        """
        # Look for the position in the em tag after the name
        position_element = faculty_div.select_one('.fac-nam + em')
        if position_element:
            return position_element.get_text().strip()
                
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
        # Extract URL from onclick attribute
        onclick = faculty_div.get('onclick', '')
        if 'window.location' in onclick:
            # Extract URL between quotes
            start = onclick.find("'") + 1
            end = onclick.find("'", start)
            if start != -1 and end != -1:
                url = onclick[start:end]
                if url and not url.startswith(('mailto:', 'tel:', '#', 'javascript:')):
                    return url
        
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
        # Look for img tag within the photo div
        img_tag = faculty_div.select_one('.photo img')
        if img_tag:
            src = img_tag.get('src')
            if src and not any(placeholder in src.lower() for placeholder in 
                             ['placeholder', 'default', 'no-image', 'blank', 'missing']):
                return self.get_absolute_url(self.base_url, src)
        
        return None
    
    @override
    def scrape_faculty_list(self) -> List[Dict]:
        """
        Scrape faculty information from the SBMI directory (single page).
        
        Returns:
            List[Dict]: List of dictionaries containing faculty information
        """
        faculty_list = []
        
        print(f"Scraping faculty from: {self.base_url}")
        
        # Get page content
        response = requests.get(self.base_url)
        if response.status_code != 200:
            print(f"Failed to load page: {self.base_url}")
            return faculty_list
            
        self.soup = BeautifulSoup(response.content, 'html.parser')
        faculty_divs = self._get_faculty_divs()
        
        print(f"Found {len(faculty_divs)} potential faculty elements")
        
        if self.debug:
            faculty_divs = faculty_divs[:5]
            print(f"Debug mode: Processing only first 5 faculty members")
        
        # Process each faculty member
        for i, faculty_div in enumerate(faculty_divs):
            faculty_info = {}

            # Add delay between each professor
            if i > 0:
                time.sleep(self.delay)
    
            # Extract image URL
            image_url = self._extract_image_url(faculty_div)
            if image_url:
                faculty_info['image_url'] = image_url
                
            # Extract name
            name = self._extract_name(faculty_div)
            if name:
                faculty_info['name'] = name
            
            # Extract position/title
            position = self._extract_position(faculty_div)
            if position:
                faculty_info['position'] = position

            # Extract areas of expertise
            areas = self._extract_areas_of_expertise(faculty_div)
            if areas:
                faculty_info['areas_of_expertise'] = areas

            # Extract profile URL and get profile summary
            profile_url = self._extract_profile_url(faculty_div)
            if profile_url:
                try:
                    profile_summary = self._get_faculty_profile(profile_url)
                    faculty_info['profile'] = profile_summary
                    faculty_info['profile_url'] = profile_url
                except Exception as e:
                    print(f"Error getting profile for {name}: {e}")
                    faculty_info['profile_url'] = profile_url
            
            # Only add faculty with at least a name
            if faculty_info.get('name'):
                faculty_list.append(faculty_info)
                print(f"Processed: {faculty_info['name']} ({len(faculty_list)} total)")
            else:
                print(f"Skipped faculty div {i+1} - no name found")
        
        print(f"Completed scraping, total faculty: {len(faculty_list)}")
        self.faculty_list = faculty_list
        return faculty_list


def main():
    """Main function to run the SBMI faculty scraper."""
    base_url = 'https://sbmi.uth.edu/faculty-and-staff/'
    
    # Create scraper instance and run
    scraper = SBMIFacultyScraper(base_url, debug=False)
    faculty_list = scraper.scrape_faculty_list()
    file_name = 'data/sbmi_faculty_list.jsonl'
    # Save the faculty list as jsonl file
    scraper.save_to_jsonl(file_name)


if __name__ == "__main__":
    main()
