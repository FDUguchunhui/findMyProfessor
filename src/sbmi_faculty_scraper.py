from bs4 import BeautifulSoup
import requests
import json
from typing import Dict, List, Optional
from typing_extensions import override
import time
from urllib.parse import urljoin
from summarize import summarize
from faculty_scraper import FacultyScraper

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
        # Try specific SBMI patterns first, then fallback to common patterns
        faculty_divs = (
            # SBMI-specific selectors
            self.soup.find_all('div', class_='faculty-listing-item') or
            self.soup.find_all('div', class_='faculty-member-card') or
            self.soup.find_all('article', class_='faculty-profile') or
            
            # UTHealth common patterns
            self.soup.find_all('div', class_='people-card') or
            self.soup.find_all('div', class_='person-profile') or
            
            # Generic patterns
            self.soup.find_all('div', class_='faculty-card') or
            self.soup.find_all('div', class_='faculty-member') or
            self.soup.find_all('div', class_='person-card') or
            self.soup.find_all('div', class_='cell') or
            self.soup.find_all('article', class_='faculty') or
            self.soup.find_all('div', class_='directory-entry') or
            
            # Look for any div containing faculty-related links
            self.soup.find_all('div', lambda value: value and any(
                keyword in str(value).lower() for keyword in ['faculty', 'people', 'staff', 'profile']
            ))
        )
        
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
        # Try different common selectors for names
        name_selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            '.faculty-name', '.name', '.person-name', '.full-name',
            '.title', '.entry-title', '.profile-name',
            'strong', 'b', '.font-weight-bold', '.fw-bold'
        ]
        
        for selector in name_selectors:
            name_element = faculty_div.select_one(selector)
            if name_element:
                name = name_element.get_text().strip()
                # Clean up common title patterns and suffixes
                name = self._clean_name(name)
                if name and len(name) > 2 and ' ' in name:  # Ensure it's a full name
                    return name
        
        # If no name found in structured elements, look for links with names
        links = faculty_div.find_all('a')
        for link in links:
            link_text = link.get_text().strip()
            cleaned_name = self._clean_name(link_text)
            if cleaned_name and len(cleaned_name) > 2 and ' ' in cleaned_name:
                return cleaned_name
                
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
    
    @override
    def _extract_profile_url(self, faculty_div) -> Optional[str]:
        """
        Extract the profile URL from the faculty div.
        
        Args:
            faculty_div: BeautifulSoup element containing faculty info
            
        Returns:
            Optional[str]: Profile URL if found, None otherwise
        """
        # Look for various types of links that might lead to faculty profiles
        link_selectors = [
            'a[href*="faculty/"]',
            'a[href*="/profile/"]',
            'a[href*="/people/"]',
            'a[href*="/staff/"]',
            'a[href*="sbmi.uth.edu"]',
            '.profile-link a',
            '.faculty-link a',
            'a'  # fallback to any link
        ]
        
        for selector in link_selectors:
            links = faculty_div.select(selector)
            for link in links:
                href = link.get('href')
                if href and not href.startswith(('mailto:', 'tel:', '#', 'javascript:')):
                    # Prefer links that look like faculty profiles
                    if any(keyword in href.lower() for keyword in ['faculty', 'profile', 'people']):
                        return self.get_absolute_url(self.base_url, href)
            
            # If we found any valid link, use the first one as fallback
            if links and links[0].get('href'):
                href = links[0]['href']
                if not href.startswith(('mailto:', 'tel:', '#', 'javascript:')):
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
        # Try different common patterns for faculty images
        img_tag = faculty_div.find('img')
        if img_tag:
            src = img_tag.get('src') or img_tag.get('data-src')
            if src and not any(placeholder in src.lower() for placeholder in 
                             ['placeholder', 'default', 'no-image', 'blank', 'missing']):
                return self.get_absolute_url(self.base_url, src)
        
        # Check for background images in style attributes
        elements_with_style = faculty_div.find_all(attrs={'style': True})
        for element in elements_with_style:
            style = element.get('style', '')
            if 'background-image' in style and 'url(' in style:
                start = style.find('url(') + 4
                end = style.find(')', start)
                if start != -1 and end != -1:
                    img_url = style[start:end].strip('\'"')
                    if img_url and not img_url.startswith('data:'):
                        return self.get_absolute_url(self.base_url, img_url)
        
        return None
    
    def _extract_position(self, faculty_div) -> Optional[str]:
        """
        Extract faculty position/title.
        
        Args:
            faculty_div: BeautifulSoup element containing faculty info
            
        Returns:
            Optional[str]: Position if found, None otherwise
        """
        # Try different selectors for position/title
        position_selectors = [
            '.position', '.title', '.role', '.job-title',
            '.faculty-title', '.academic-title', '.professional-title',
            '.department', '.affiliation', '.faculty-position',
            'p.title', 'span.title', 'div.title',
            '.faculty-info p', '.profile-info p'
        ]
        
        for selector in position_selectors:
            elements = faculty_div.select(selector)
            for element in elements:
                text = element.get_text().strip()
                # Filter out obvious non-position text
                if (text and len(text) > 3 and 
                    not any(skip in text.lower() for skip in 
                           ['email', 'phone', 'office', 'room', '@', 'tel:', 'mailto:'])):
                    return text
        
        # Look for text patterns that might be positions
        text_content = faculty_div.get_text()
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        for line in lines[1:4]:  # Skip first line (likely name), check next few
            if (len(line) > 5 and 
                any(keyword in line.lower() for keyword in 
                   ['professor', 'director', 'chair', 'faculty', 'researcher', 'scientist'])):
                return line
                
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
    scraper = SBMIFacultyScraper(base_url, debug=True)
    faculty_list = scraper.scrape_faculty_list()
    
    # Save the faculty list as jsonl file
    scraper.save_to_jsonl('data/sbmi_faculty_list.jsonl')


if __name__ == "__main__":
    main()
