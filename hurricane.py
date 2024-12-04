import os
import re
import json
import kml2geojson as k2g
import zipfile
import requests
import shutil
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import xml.etree.ElementTree as ET
from lxml import etree
from datetime import datetime
import subprocess
from urllib.parse import urljoin

base_directory = r"C:\Users\CrudeIntern\OneDrive - Hengli Petrochemical International Pte Ltd\Market Analysis\Current Projects\Hurricane"
# Delete all KML files in the base directory
def delete_kml_files(base_directory: str) -> None:
    file_list = os.listdir(base_directory)
    for file in file_list:
        if file.endswith('.kml'):
            os.remove(os.path.join(base_directory, file))
        if os.path.exists(os.path.join(base_directory, 'hurricane_combined.geojson_old')):
            os.remove(os.path.join(base_directory, 'hurricane_combined_old.geojson'))
def webscraping_kmz_JTWC(base_directory: str) -> None:
    file_names, kmz_file_paths = [], []
    driver = webdriver.Chrome()
    try:
        url = "https://www.metoc.navy.mil/jtwc/jtwc.html"
        driver.get(url)
        driver.implicitly_wait(5)
        try:
            kmz_link_elements = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.LINK_TEXT, "Google Earth Overlay"))
            )
        except Exception as e:
            print("No Google Earth Overlay links found.")
            print(e)
            return kmz_file_paths, file_names
        for index, kmz_link_element in enumerate(kmz_link_elements):
            kmz_url = kmz_link_element.get_attribute('href')
            print(f"KMZ File URL {index + 1}: {kmz_url}")
            file_name = kmz_url.split('/')[-1].split('.')[0]
            kmz_file = requests.get(kmz_url) 
            kmz_file_path = os.path.join(base_directory, f'{file_name}.kmz')
            kmz_file_paths.append(kmz_file_path)
            file_names.append(file_name)
            with open(kmz_file_path, 'wb') as f:
                f.write(kmz_file.content)
            print(f"KMZ file {index + 1} saved to {kmz_file_path}")
    except Exception as e:
        print("Error occurred while scraping KMZ files:", e)
    finally:
        driver.quit()
    return kmz_file_paths, file_names

def webscraping_kmz_NHC(base_directory: str) -> None:
    url = 'https://www.nhc.noaa.gov/gis/'
    save_directory = base_directory
    os.makedirs(save_directory, exist_ok=True)
    file_names, kmz_file_paths = [], []
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        forecast_rows = soup.find_all('tr')
        # Only look at the third to fifth rows (index 2, 3, 4 in zero-based index)
        for i in range(2, 5):
            row = forecast_rows[i]
            tds = row.find_all('td')[1:4]  # Look at the second to fourth <td> (index 1 to 3)
            for td in tds:
                hurricane_names = []
                if i <4:
                    element_names = td.get_text(strip=True).replace(' ', '_').split('KMZ:')
                else:
                    element_names = td.get_text(strip=True).replace(' ', '_').split('kmz')
                for element_name in element_names:
                    if ':' in element_name:
                        hurricane_name = element_name.split(':')[0].replace(' ', '_').split(']')[-1]
                        hurricane_names.append(hurricane_name)
                links = td.find_all('a')
                for link in links:
                    link_text = link.get_text(strip=True)
                    if i == 2:  # Third row (zero-indexed), find 'Cone' and 'Track'
                        if link_text == 'Cone':
                            download_NHC_file(link, f"{hurricane_names[0]}_Cone.kmz",file_names, kmz_file_paths)
                        elif link_text == 'Track':
                            download_NHC_file(link, f"{hurricane_names[0]}_Track.kmz", file_names, kmz_file_paths)
                            hurricane_names.pop(0)
                        
                    elif i == 3:  # Fourth row (zero-indexed), find 'Initial Radii'
                        if link_text == 'Initial Radii':
                            download_NHC_file(link, f"{hurricane_names[0]}_Initial_Radii.kmz", file_names, kmz_file_paths)
                            hurricane_names.pop(0)
                    elif i == 4:  # Fifth row (zero-indexed), find 'kmz'
                        if link_text == 'kmz':
                            download_NHC_file(link, f"{hurricane_names[0]}_kmz.kmz", file_names, kmz_file_paths)
                            hurricane_names.pop(0)
    else:
        print(f"Failed to retrieve page content. Status code: {response.status_code}")
    return  kmz_file_paths, file_names

def download_NHC_file(link, filename, file_names, kmz_file_paths):
    base_url = 'https://www.nhc.noaa.gov/gis/'
    file_url = urljoin(base_url, link['href'])
    file_response = requests.get(file_url)
    if file_response.status_code == 200:
        file_path = os.path.join(base_directory, filename)
        with open(file_path, 'wb') as file:
            file.write(file_response.content)
        print(f"Downloaded and saved: {filename}")
        filename = filename.split('.')[0]
        file_names.append(filename)
        kmz_file_paths.append(file_path)
    else:
        print(f"Failed to download {filename}. Status code: {file_response.status_code}")

def extract_kml(kmz_file_paths: list, file_names: list, base_directory: str) -> None:
    kml_file_paths = []
    for kmz_file_path, file_name in zip(kmz_file_paths, file_names):
        output_directory = os.path.join(base_directory, file_name)
        print('base_directory:', base_directory)
        print('file_name:', file_name)
        with zipfile.ZipFile(kmz_file_path, 'r') as zip_ref:
            print('output_directory:', output_directory)
            zip_ref.extractall(output_directory)
        print(f"KMZ file {kmz_file_path} has been extracted to {output_directory}")
        ld = os.listdir(output_directory)
        kml_file = [file for file in ld if file.endswith('.kml')]
        kml_file_path = os.path.join(output_directory, kml_file[0])
        try:
            new_kml_path = os.path.join(base_directory, f'{file_name}.kml')
            print(new_kml_path)
            os.rename(kml_file_path, new_kml_path)
            print(f"KML file has been moved and renamed to {new_kml_path}")
            kml_file_paths.append(new_kml_path)
        except Exception as e:
            print(f"Error moving KML file: {e}")
        try:
            shutil.rmtree(output_directory)
            print(f"Folder {output_directory} has been deleted.")
        except Exception as e:
            print(f"Error deleting folder {output_directory}: {e}")
        try:
            os.remove(kmz_file_path)
            print(f"KMZ file {kmz_file_path} has been deleted.")
        except Exception as e:
            print(f"Error deleting KMZ file {kmz_file_path}: {e}")
    return kml_file_paths

def parse_kml_file(kml_file):
    """
    Parse a KML file and return its root element.
    Args:
        kml_file (str): The path to the KML file.
    Returns:
        root (Element): The root element of the parsed KML file.
    """
    try:
        tree = etree.parse(kml_file)
        return tree.getroot()
    except etree.XMLSyntaxError as e:
        print(f"Error parsing file {kml_file}: {e}")
        return None

def adjust_ids(element, id_suffix):
    """
    Adjust IDs of elements to ensure uniqueness in the merged KML.
    Args:
        element (Element): The root element whose child IDs need adjustment.
        id_suffix (int): A unique suffix to append to IDs.
    """
    for elem in element.iter():
        if 'id' in elem.attrib:
            elem.attrib['id'] = f"{elem.attrib['id']}_{id_suffix}"

def replace_second_line(kml_file):
    """
    Replace the second line of the KML file if the file ends with 'CONE.kml'.
    Args:
        kml_file (str): The path to the KML file.
    """
    if kml_file.endswith('Cone.kml'):
        with open(kml_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        if len(lines) > 1:
            lines[1] = "<kml xmlns='http://www.opengis.net/kml/2.2'>\n"

            with open(kml_file, 'w', encoding='utf-8') as file:
                file.writelines(lines)
                
        else:
            print(f"File {kml_file} does not have enough lines to modify.")

def merge_kml_files(selected_files, output_file):
    """
    Merge the selected KML files into a single KML file.
    Args:
        selected_files (list): List of KML files selected for merging.
        output_file (str): The path for the output merged KML file.
    """
    KML_NAMESPACE = "http://www.opengis.net/kml/2.2"
    NSMAP = {None: KML_NAMESPACE}
    merged_root = etree.Element('kml', nsmap=NSMAP)
    merged_document = etree.SubElement(merged_root, 'Document')
    id_counter = 0

    for kml_file in selected_files:
        # Replace the second line if it's a CONE.kml file
        replace_second_line(kml_file)
        
        root = parse_kml_file(kml_file)
        if root is not None:
            kml_namespace = root.nsmap.get(None)
            if kml_namespace is None:
                kml_namespace = root.nsmap.get('')

            ns = {'kml': kml_namespace}

            # Find the <Document> element inside each KML file
            document = root.find('kml:Document', namespaces=ns)
            if document is not None:
                adjust_ids(document, id_counter)
                id_counter += 1
                for elem in document:
                    merged_document.append(elem)
            else:
                folders = root.findall('kml:Folder', namespaces=ns)
                for folder in folders:
                    adjust_ids(folder, id_counter)
                    id_counter += 1
                    merged_document.append(folder)
        else:
            print(f"Failed to parse file {kml_file}.")

    if len(merged_document) > 0:
        with open(output_file, 'wb') as f:
            f.write(etree.tostring(merged_root, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
        print(f"Merged KML file saved as: {output_file}")
    else:
        print("No valid KML content was merged.")

def kml_to_geojson(output_geojson_path: str, output_combine_file: str) -> None:
    if os.path.exists(output_combine_file):
        file = k2g.main.convert(kml_path_or_buffer=output_combine_file, feature_collection_name='hurricane_combined.geojson')
        if os.path.exists(os.path.join(base_directory, 'hurricane_combined_old.geojson')):
            os.remove(os.path.join(base_directory, 'hurricane_combined_old.geojson'))
    else:
        print(f"File {output_combine_file} does not exist.")
        if os.path.exists(output_geojson_path):
            try:
                os.rename(output_geojson_path, os.path.join(base_directory, 'hurricane_combined_old.geojson'))
            except Exception as e:
                print(f"No Hurricane for more than one day")
        with open(output_geojson_path, 'w') as f:
            f.write('{"type": "FeatureCollection", "features": []}')
        return
    with open(output_geojson_path, 'w') as f:
        f.write(str(file[0]))
    with open(output_geojson_path, 'r') as f:
        raw_geojson_content = f.read()
    while True:
        try:
            raw_geojson_content = raw_geojson_content.replace("'", '"')
            geojson_obj = json.loads(raw_geojson_content)
            formatted_geojson_content = json.dumps(geojson_obj, indent=4)
            with open(output_geojson_path, 'w') as f:
                f.write(formatted_geojson_content)
            print("GeoJSON cleaned and saved successfully.")
            break
        except json.JSONDecodeError as e:
            print(f"Error processing the GeoJSON file: {e}")
            escape_index = e.colno - 2
            raw_geojson_content = raw_geojson_content[:escape_index] + "\\" + raw_geojson_content[escape_index:]
            for i, val in enumerate(raw_geojson_content[escape_index+2:]):
                if val == '"':
                    raw_geojson_content = raw_geojson_content[:escape_index+i+2] + "\\" + raw_geojson_content[escape_index+i+2:] 
                    break

def upload_kml(kml_file_path: str, output_geojson_path: str) -> None:
    bash_path = r"C:\Users\CrudeIntern\AppData\Local\Programs\Git\bin\bash.exe"  
    script_path = "/c/Users/CrudeIntern/OneDrive - Hengli Petrochemical International Pte Ltd/Market Analysis/Current Projects/Hurricane/auto_upload.sh"
    cmd = [bash_path, '-c', f"'{script_path}'"]
    shellscript = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, text=True)
    for line in shellscript.stdout:
        print(line.strip())
    returncode = shellscript.wait()
    print(f"Process ended with the return code of {returncode}.")

def main():
    delete_kml_files(base_directory)
    kmz_file_paths_JTWC, file_names_JTWC = webscraping_kmz_JTWC(base_directory)
    kmz_file_paths_NHC, file_names_NHC = webscraping_kmz_NHC(base_directory)
    kmz_file_paths = kmz_file_paths_JTWC + kmz_file_paths_NHC
    file_names = file_names_JTWC + file_names_NHC
    kml_file_paths = extract_kml(kmz_file_paths, file_names, base_directory)
    output_combine_file = os.path.join(base_directory, 'hurricane_combined.kml')
    merge_kml_files(kml_file_paths, output_file=output_combine_file)
    output_geojson_path = os.path.join(base_directory, 'hurricane_combined.geojson')
    output_combine_file = os.path.join(base_directory, 'hurricane_combined.kml')
    kml_to_geojson(output_geojson_path, output_combine_file)
    upload_kml(output_combine_file, output_geojson_path)

if __name__ == '__main__':
    main()