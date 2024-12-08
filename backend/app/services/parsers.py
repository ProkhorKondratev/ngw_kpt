import re
import tempfile
import zipfile
from pathlib import Path
from typing import Callable
from xml.etree import ElementTree as ET

import geopandas as gpd
import yaml


class Parser:
    @staticmethod
    def extract_for_parsing(arc_path: str, parsing_func: Callable):
        """Создание временной директории для обработки файлов из архива"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(arc_path, "r") as archive:
                archive.extractall(tmp_dir)

            # Вызов функции обработки файлов
            parsing_func(tmp_dir)

            with zipfile.ZipFile(arc_path, "w", zipfile.ZIP_DEFLATED) as archive:
                for file in Path(tmp_dir).rglob("*"):
                    if file.is_file():
                        archive.write(file, file.relative_to(tmp_dir))

    @staticmethod
    def _load_crs_params(yaml_path: str):
        with open(yaml_path) as file:
            crs_params = yaml.safe_load(file)
        return crs_params


class XMLParser(Parser):
    @staticmethod
    def _extract_cad_region(cad_number: str) -> str:
        numbers = re.findall(r"\d+", cad_number)
        if not numbers:
            raise ValueError(f"Некорректный кадастровый номер: {cad_number}")

        first_number = numbers[0]
        if len(first_number) >= 4:  # Например: 7218:21, нужно 72
            region_code = first_number[:2]
            district_code = first_number[2:4]
        else:
            region_code = first_number[:2].zfill(2)  # Например 72:1845, нужно 18
            if len(numbers) >= 2:
                second_number = numbers[1]
                district_code = second_number[:2].zfill(2)
            else:
                district_code = "00"

        return f"{region_code}:{district_code}"

    @staticmethod
    def _fix_elem_sk(elem: ET.Element, crs_params: dict, cad_region: str):
        sk_id_elem = elem.find("sk_id")
        if sk_id_elem is None:
            print(f"XMLParser: Создание элемента 'sk_id' в '{elem.tag}'")
            sk_id_elem = ET.SubElement(elem, "sk_id")
        sk_id = None

        def swap_coords(x, y):
            return y, x

        for ordinate in elem.findall(".//ordinate"):
            y_elem = ordinate.find("y")
            x_elem = ordinate.find("x")

            if y_elem is not None and x_elem is not None:
                y_coord, x_coord = y_elem.text, x_elem.text
                y_int_part, x_int_part = y_coord.split(".")[0], x_coord.split(".")[0]

                if len(y_int_part) != 7:
                    if len(y_int_part) == 6 and len(x_int_part) == 7:
                        print("XMLParser: Замена координат местами")
                        y_elem.text, x_elem.text = swap_coords(x_coord, y_coord)
                        sk_id = sk_id or f"{cad_region[:2]}.{x_coord[:1]}"

                    elif len(y_int_part) == 6 and len(x_int_part) == 6:
                        print("XMLParser: Исправление 6-значных координат")
                        crs_id = crs_params.get(cad_region)
                        if crs_id:
                            y_elem.text = f"{crs_id[-1]}{y_coord}"
                            sk_id = sk_id or crs_id
                        else:
                            raise ValueError(f"XMLParser: Параметры CRS для региона '{cad_region}' не найдены")
                    else:
                        print("XMLParser: Обнаружена ошибка в координатах")
                        sk_id = "Ошибка в координатах"
                        break
                else:
                    sk_id = f"{cad_region[:2]}.{y_elem.text[:1]}"
                    break

        sk_id_elem.text = sk_id

    @staticmethod
    def _fix_cadastral_blocks(root: ET.Element, crs_params: dict):
        for cadastral_block_element in root.findall(".//cadastral_block"):
            cadastral_number_elem = cadastral_block_element.find("cadastral_number")
            cad_region = XMLParser._extract_cad_region(cadastral_number_elem.text)

            for entity_spatial in cadastral_block_element.findall(".//spatial_data/entity_spatial"):
                XMLParser._fix_elem_sk(entity_spatial, crs_params, cad_region)

    @staticmethod
    def _fix_records(root: ET.Element, crs_params: dict, record_name: str):
        for record_element in root.findall(f".//{record_name}"):
            cad_number_elem = record_element.find(".//cad_number")
            if cad_number_elem is None:
                cad_number_elem = record_element.find(".//reg_numb_border")

            cad_region = XMLParser._extract_cad_region(cad_number_elem.text)

            for entity_spatial in record_element.findall(".//entity_spatial"):
                XMLParser._fix_elem_sk(entity_spatial, crs_params, cad_region)

    @staticmethod
    def _fix_xml_sk(file_path: str, crs_params: dict):
        tree = ET.parse(file_path)
        root = tree.getroot()

        records = [
            "subject_boundary_record",
            "municipal_boundary_record",
            "inhabited_locality_boundary_record",
            "coastline_record",
            "zones_and_territories_record",
            "land_record",
            "build_record",
            "construction_record",
            "object_under_construction_record",
        ]

        XMLParser._fix_cadastral_blocks(root, crs_params)

        for record in records:
            XMLParser._fix_records(root, crs_params, record)

        tree.write(file_path, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def _start_fix_process(directory_path):
        report_files = [str(file.resolve()) for file in Path(directory_path).rglob("report*.xml")]
        crs_params = XMLParser._load_crs_params("app/msk_regions.yaml")

        for report_file in report_files:
            XMLParser._fix_xml_sk(report_file, crs_params)

    @staticmethod
    def fix_sk_id(arc_path):
        """Запуск проверки и исправления координат в XML файлах"""
        XMLParser.extract_for_parsing(arc_path, XMLParser._start_fix_process)


class SHPParser(Parser):
    @staticmethod
    def _get_shp_crs(gdf: gpd.GeoDataFrame):
        if "sk" in gdf.columns:
            sk = gdf["sk"].values[0]
            if sk != "Ошибка в координатах":
                return sk

        return None

    @staticmethod
    def _set_shp_crs(gdf: gpd.GeoDataFrame, crs_params, gdf_sk):
        try:
            gdf.crs = crs_params[gdf_sk]
            return gdf.to_crs(epsg=4326)
        except KeyError:
            raise ValueError(f"SHPParser: Параметры для CRS '{gdf_sk}' не найдены")

    @staticmethod
    def _start_fix_process(directory_path):
        shp_files = [str(file.resolve()) for file in Path(directory_path).rglob("*.shp")]
        crs_params = SHPParser._load_crs_params("app/msk_params.yaml")

        for shp_file in shp_files:
            print(f"Обработка SHP {shp_file}")
            gdf = gpd.read_file(shp_file)
            gdf_sk = SHPParser._get_shp_crs(gdf)

            if gdf_sk:
                print(f"Определена SK '{gdf_sk}'")
                gdf = SHPParser._set_shp_crs(gdf, crs_params, gdf_sk)
                gdf.to_file(shp_file)

    @staticmethod
    def fix_crs(arc_path):
        """Запуск проверки и установки CRS в SHP файлах"""
        SHPParser.extract_for_parsing(arc_path, SHPParser._start_fix_process)
