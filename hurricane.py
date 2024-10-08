import os
import json
import kml2geojson as k2g
import requests
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Define paths
base_directory = r"C:\Users\CrudeIntern\Desktop\Delphine\hurricane"
# output_geojson_path = os.path.join(base_directory, 'wp1224.geojson')

def webscraping_kmz(base_directory: str) -> None:
    driver = webdriver.Chrome()
    try:
        url = "https://www.metoc.navy.mil/jtwc/jtwc.html"
        driver.get(url)
        driver.implicitly_wait(5)
        kmz_link_elements = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.LINK_TEXT, "Google Earth Overlay"))
        )
        if not kmz_link_elements:
            print("No Google Earth Overlay links found.")
            return
        file_names, kmz_file_paths = [], []
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

def extract_kml(kmz_file_paths: list, file_names: list, base_directory: str) -> None:
    for kmz_file_path, file_name in zip(kmz_file_paths, file_names):
        output_directory = os.path.join(base_directory, file_name)
        with zipfile.ZipFile(kmz_file_path, 'r') as zip_ref:
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

def combine_kml(kml_file_path: str, output_kml_path: str) -> None:
    pass

def kml_to_geojson(output_geojson_path: str) -> None:
    file = k2g.main.convert(kml_path_or_buffer=extracted_kml_path, feature_collection_name="wp1224.geojson")
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

def drag_and_drop_kml(kml_file_path: str, output_geojson_path: str) -> None:
    pass

def upload_kml(kml_file_path: str, output_geojson_path: str) -> None:
    pass

def main():
    webscraping_kmz(kmz_file_path)
    extract_kml(kmz_file_path, extracted_kml_path)
    kml_to_geojson(output_geojson_path)
    #23