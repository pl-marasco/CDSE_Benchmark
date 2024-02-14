import geopandas as gpd
import pandas as pd
import random

from pyparsing import results
from shapely.geometry import Point
import requests
import glob
import os
import timeit
import numpy as np
from pandas import Timedelta

my_globals = {}
exec("from osgeo import gdal", my_globals)


def path_builder(aoi, catalogue_odata_url, collection_name, product_type, max_cloud_cover, search_period_start,
                 search_period_end, root):
    search_query = f"{catalogue_odata_url}/Products?$filter=Collection/Name eq '{collection_name}' and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{product_type}') and OData.CSC.Intersects(area=geography'SRID=4326;{aoi}') and ContentDate/Start gt {search_period_start} and ContentDate/Start lt {search_period_end}"

    response = requests.get(search_query)
    if response.status_code == 200:
        response = response.json()
        result = pd.DataFrame.from_dict(response["value"])
        if result.empty:
            print(f"No results for {aoi}")
            return None, None, None
        else:
            random.seed(1492)

            if len(result) > 1:
                n = random.randint(0, result.shape[0] - 1)
            else:
                n = 0

            product_name = result.iloc[n]['Name']
            print(product_name)

            nm_component = product_name.split('_')
            yr = nm_component[2][:4]
            mm = nm_component[2][4:6]
            dd = nm_component[2][6:8]

            zone = nm_component[5][1:3]
            row = nm_component[5][3:4]
            square = nm_component[5][4:6]
            CDSE_path = glob.glob(os.path.join(root, 'CDSE',
                                               f'Sentinel-2/MSI/L2A/{yr}/{mm}/{dd}/{product_name}/GRANULE/*/IMG_DATA/R20m/*B07_20m.jp2'))[
                0]
            AWS_path = os.path.join(root, 'AWS',
                                    f'tiles/{zone}/{row}/{square}/{yr}/{int(mm)}/{int(dd)}/0/R20m/B07.jp2')
            return product_name, CDSE_path, AWS_path
    else:
        print(f'{response.status_code}')
        return None, None, None


def main():
    collection_name = "SENTINEL-2"
    product_type = "S2MSI2A"
    max_cloud_cover = 100

    results = []
    repeat_n = 10
    number_n = 3
    dd_number = 1

    root = '/home/pier/'
    samples = 2


    gcp_total = gpd.read_file(r'data/gcp.shp', where="q_score='5'")

    random_points_gdf = gcp_total.sample(samples)
    random_points_gdf.reset_index(drop=True, inplace=True)

    date_range = pd.date_range('2020-01-01', '2024-02-14')
    date_index = pd.DataFrame(date_range, columns=['date'])
    date_subset = date_index.sample(n=samples)
    date_subset.reset_index(drop=True, inplace=True)

    rnd = random_points_gdf.join(date_subset)

    # base URL of the product catalogue
    catalogue_odata_url = "https://catalogue.dataspace.copernicus.eu/odata/v1"

    for row in rnd.iterrows():
        point = row[1].get(key='geometry')
        date = row[1].get(key='date')

        search_period_start = (date - Timedelta(dd_number, unit='day')).strftime('%Y-%m-%dT00:00:00.000Z')
        search_period_end = (date + Timedelta(dd_number, unit='day')).strftime('%Y-%m-%dT00:00:00.000Z')

        product_name, CDSE_path, AWS_path = path_builder(point, catalogue_odata_url, collection_name, product_type,
                                                         max_cloud_cover, search_period_start, search_period_end, root)

        if product_name:
            timing_CDSE = timeit.repeat(f'gdal.Info(\'{CDSE_path}\')',
                                        # setup='from osgeo import gdal',
                                        repeat=repeat_n,
                                        number=number_n,
                                        globals=my_globals)
            timing_CDSE = np.array(timing_CDSE) / number_n
            mean_CDSE = np.mean(timing_CDSE).round(3)
            std_CDSE = np.std(timing_CDSE).round(3)
            min_CDSE = np.min(timing_CDSE).round(3)
            max_CDSE = np.max(timing_CDSE).round(3)

            timing_AWS = timeit.repeat(f'gdal.Info(\'{AWS_path}\')',
                                       # setup='from osgeo import gdal',
                                       repeat=repeat_n,
                                       number=number_n,
                                       globals=my_globals)
            timing_AWS = np.array(timing_AWS) / number_n
            mean_aws = np.mean(timing_AWS).round(3)
            std_aws = np.std(timing_AWS).round(3)
            min_AWS = np.min(timing_AWS).round(3)
            max_AWS = np.max(timing_AWS).round(3)

            results.append([product_name, mean_CDSE, min_CDSE, max_CDSE, std_CDSE, mean_aws, min_AWS, max_AWS, std_aws])

    results_df = pd.DataFrame(results,
                              columns=['product_name', 'mean_CDSE', 'min_CDSE', 'max_CDSE', 'std_CDSE', 'mean_AWS',
                                       'min_AWS', 'max_AWS', 'std_AWS'])

    results_df.to_csv('CDSE_AWS.csv', index=False)


if __name__ == '__main__':
    print('Fishing net thrown')
    main()
