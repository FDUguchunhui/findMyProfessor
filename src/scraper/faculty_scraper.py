import os
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urljoin
import profile_scraper as profile_scraper
import json


class FacultyScraper:
    def __init__(self, base_url: str, delay: float = 0.1,  debug: bool = False):
        self.base_url = base_url
        self.delay = delay
        self.debug = debug
        self.response = requests.get(self.base_url)
        self.soup = BeautifulSoup(self.response.text, 'html.parser')

    
    
    def save_to_jsonl(self, output_file: str = 'faculty_data.jsonl') -> None:
        """
        Save faculty information to a JSONL file.
        
        Args:
            output_file (str): Name of the output JSONL file
        """
        if not self.faculty_list:
            print("No faculty data to save. Please scrape data first.")
            return
        
                # remove the file if it exists
        if os.path.exists(output_file):
            os.remove(output_file)
            
        with open(output_file, 'w', encoding='utf-8') as f:
            for faculty_member in self.faculty_list:
                f.write(json.dumps(faculty_member, ensure_ascii=False) + '\n')
        print(f"Saved data for {len(self.faculty_list)} faculty members to {output_file}")


    def scrape_faculty_list(self) -> List[Dict]:
        """
        Scrape faculty information from the provided HTML content.
        
        Args:
            html_content (str): HTML content containing faculty information
            
        Returns:
            List[Dict]: List of dictionaries containing faculty information
        """

        faculty_list = []
        # Find all faculty divs with class 'cell fac-sort'
        faculty_divs = self._get_faculty_divs()

        if self.debug:
            faculty_divs = faculty_divs[:5]
            print(f"Debug: Only scraping first 5 faculty members")
            
        for i, faculty_div in enumerate(faculty_divs):
            faculty_info = {}

            # Add delay between each professor
            if i > 0:
                time.sleep(self.delay)
    
            # Extract image URL
            image_url = self._extract_image_url(faculty_div)
            if image_url:
                faculty_info['image_url'] = image_url
            # Extract name and profile information
            name = self._extract_name(faculty_div)
            if name:
                faculty_info['name'] = name

            profile_url = self._extract_profile_url(faculty_div)
            if profile_url:
                profile = self._get_faculty_profile(profile_url)
                faculty_info['profile'] = profile.text
                faculty_info['links'] = profile.links
                faculty_info['profile_url'] = profile_url
            
            faculty_list.append(faculty_info)
            print(f"Processed {i+1}/{len(faculty_divs)} faculty members")
        
        self.faculty_list = faculty_list
            
    def _get_faculty_profile(self, profile_url: str) -> str:
        """
        Get faculty profile summary using the summarize function.
        
        Args:
            profile_url (str): URL of the faculty profile
            
        Returns:
            str: Profile summary
        """
        try:
            return profile_scraper.FacultyProfileScraper(profile_url)
        except Exception as e:
            print(f"Error summarizing profile {profile_url}: {e}")
            return f"Error: Could not summarize profile"
        
    

    def _get_faculty_divs(self) -> List:
        '''
        Get the faculty divs from the soup
        '''
        pass


    def _extract_image_url(self, faculty_div) -> Optional[str]:
        '''
        Extract the image url from the faculty div
        '''
        pass

    def _extract_name(self, faculty_div) -> Dict:
        '''
        Extract the name from the faculty div
        '''
        pass

    def _extract_profile_url(self, faculty_div) -> Dict:
        pass

    def get_absolute_url(self, base_url: str, relative_url: str) -> str:
        """
        Convert a relative URL to an absolute URL.
        
        Args:
            base_url (str): The base URL of the website
            relative_url (str): The relative URL to convert
            
        Returns:
            str: The absolute URL
        """
        return urljoin(base_url, relative_url)
