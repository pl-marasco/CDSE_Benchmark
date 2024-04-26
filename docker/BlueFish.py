import datetime

import geopandas as gpd
import pandas as pd
import yaml

import requests
import glob
import os
import timeit
import numpy as np
from pandas import Timedelta

import subprocess
import re

my_globals = {}
exec("from osgeo import gdal ;gdal.UseExceptions()", my_globals)


def pingttl_server(server):
    server = server.replace("https://", "")
    p = subprocess.Popen(["ping", "-v", "-c 5", f"{server}"], stdout=subprocess.PIPE)
    res = p.communicate()[0]
    if p.returncode > 0:
        print("server error")
    else:
        pattern = re.compile("ttl=\d*")
        ttl = int(pattern.search(str(res)).group().split("=")[1])
        pattern = re.compile("time=\d*.\d*")
        ping = float(pattern.search(str(res)).group().split("=")[1])

    return [ping, ttl]


def config_reader() -> dict:
    # Read the settings file and return the dictionary
    with open("/root/testbed/settings.yml") as json_file:
        settings = yaml.safe_load(json_file)
    return settings


def gcp_reader(settings: dict) -> gpd.GeoDataFrame:
    # Read the control points file and return the GeoDataFrame
    gcp_total = gpd.read_file(
        settings["ControlPoints"]["path"],
        where=rf"q_score='{settings['ControlPoints']['q_score']}'",
    )
    return gcp_total


def gcp_selector(gcp_total: gpd.GeoDataFrame, settings: dict) -> gpd.GeoDataFrame:
    # Select random points from the control points GeoDataFrame
    random_points_gdf = gcp_total.sample(settings["Analysis"]["n_samples"])
    random_points_gdf.reset_index(drop=True, inplace=True)

    date_range = pd.date_range(
        settings["Collection"]["start_date"],
        settings["Collection"]["end_date"],
        freq="D",
    )
    date_index = pd.DataFrame(date_range, columns=["date"])
    date_subset = date_index.sample(n=settings["Analysis"]["n_samples"])
    date_subset.reset_index(drop=True, inplace=True)

    rnd = random_points_gdf.join(date_subset)

    return rnd


def cdse_path_get(df: gpd.GeoDataFrame, settings: dict) -> str:
    # Get the path of the CDSE product
    pre_path = os.path.join(
        settings["Local"]["cdse"],
        df.iloc[0]["S3Path"][8:],
        "GRANULE/*/IMG_DATA/R20m/*B07_20m.jp2",
    )
    try:
        path = glob.glob(pre_path)
        if len(path) == 0:
            print(f'No path found for {df.iloc[0]["Name"]}')
            raise IOError
    except (IOError, Exception) as e:
        print(f"Error {e}, {path}")
        return None

    return path[0]


def aws_path_get(df: gpd.GeoDataFrame, settings: dict) -> str:
    # Get the path of the AWS product
    product_name = df.iloc[0]["Name"]

    nm_component = product_name.split("_")
    yr = nm_component[2][:4]
    mm = nm_component[2][4:6]
    dd = nm_component[2][6:8]

    zone = nm_component[5][1:3]
    row = nm_component[5][3:4]
    square = nm_component[5][4:6]

    return os.path.join(
        settings["Local"]["aws"],
        f"tiles/{zone}/{row}/{square}/{yr}/{int(mm)}/{int(dd)}/1/R20m/B07.jp2",
    )


def benchmarker_info(path: str, settings: dict):
    # Get the timing information of the path
    try:
        timing = timeit.repeat(
            f"gdal.Info('{path}')",
            # setup='from osgeo import gdal',
            repeat=settings["Analysis"]["repeat_n"],
            number=settings["Analysis"]["number_n"],
            globals=my_globals,
        )

        timing = np.array(timing) / settings["Analysis"]["number_n"]
        mean = np.mean(timing).round(3)
        std = np.std(timing).round(3)
        min = np.min(timing).round(3)
        max = np.max(timing).round(3)

    except Exception as e:
        mean, std, min, max = [0] * 4

    return mean, std, min, max


def scene_selector(settings: dict) -> pd.DataFrame:
    # Select the scenes based on the settings
    gcp_total = gcp_reader(settings)
    gcp_selection = gcp_selector(gcp_total, settings)

    # base URL of the product catalogue
    catalogue_odata_url = settings["Catalog"]["url"]
    collection_name = settings["Collection"]["collection_name"]
    product_type = settings["Collection"]["product_type"]
    max_cloud_cover = settings["Collection"]["max_cloud_cover"]

    paths = pd.DataFrame(columns=["product_name", "CDSE_path", "AWS_path"])

    print("Waiting for the fishes...")
    for row in gcp_selection.iterrows():
        poi = row[1].get(key="geometry")
        date = row[1].get(key="date")

        dd_number = settings["Analysis"]["dd_number"]
        search_period_start = (date - Timedelta(dd_number, unit="day")).strftime(
            "%Y-%m-%dT00:00:00.000Z"
        )
        search_period_end = (date + Timedelta(dd_number, unit="day")).strftime(
            "%Y-%m-%dT00:00:00.000Z"
        )

        search_query = (
            f"{catalogue_odata_url}/Products?$"
            f"filter=Collection/Name eq '{collection_name}' "
            f"and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/Value eq '{product_type}') "
            # f"and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {max_cloud_cover})"
            f"and OData.CSC.Intersects(area=geography'SRID=4326;{poi}') "
            f"and ContentDate/Start gt {search_period_start} "
            f"and ContentDate/Start lt {search_period_end}"
            # f"&$expand=Attributes"
        )

        response = requests.get(search_query)

        if response.status_code == 200:
            response = response.json()
            result = pd.DataFrame.from_dict(response["value"])
            if result.empty:
                print(f"No results for {poi}")
                continue
            else:
                selection = result[
                    (result["ContentLength"] != 0)
                    & (result["Online"] == True)
                    & (
                        result["Name"].str.contains("_N05")
                        | result["Name"].str.contains("_N04")
                    )
                ]
                if selection.empty:
                    print(f"No results for {poi}")
                    continue
                cdse_path = cdse_path_get(selection, settings)
                aws_path = aws_path_get(selection, settings)
                if cdse_path is not None and aws_path is not None:
                    paths = pd.concat(
                        (
                            paths,
                            pd.DataFrame(
                                [[selection.iloc[0]["Name"], cdse_path, aws_path]],
                                columns=["product_name", "CDSE_path", "AWS_path"],
                            ),
                        )
                    )
                else:
                    continue

        else:
            print(f"{response.status_code}")
            continue

    return paths


def result_df():  # -> pd.DataFrame:
    # Create an empty DataFrame for the results
    return pd.DataFrame(
        {
            "product_name": pd.Series(dtype="str"),
            "mean": pd.Series(dtype="float32"),
            "min": pd.Series(dtype="float32"),
            "max": pd.Series(dtype="float32"),
            "std": pd.Series(dtype="float32"),
        }
    )


def main():
    # Main function

    print("Preparing the fishing rod...")
    settings = config_reader()
    pth_list = scene_selector(settings)

    results_CDSE = result_df()
    results_AWS = result_df()

    print("Fishing ...")
    for _, row in pth_list.iterrows():
        product_name = row.iloc[0]
        CDSE_path = row.iloc[1]
        AWS_path = row.iloc[2]

        if "cdse" in settings["Analysis"]["endpoints"]:
            mean_CDSE, std_CDSE, min_CDSE, max_CDSE = benchmarker_info(
                CDSE_path, settings
            )
            results_CDSE = pd.concat(
                (
                    results_CDSE,
                    pd.DataFrame(
                        [[product_name, mean_CDSE, min_CDSE, max_CDSE, std_CDSE]],
                        columns=["product_name", "mean", "min", "max", "std"],
                    ),
                )
            )

        if "aws" in settings["Analysis"]["endpoints"]:
            mean_AWS, std_AWS, min_AWS, max_AWS = benchmarker_info(AWS_path, settings)
            results_AWS = pd.concat(
                (
                    results_AWS,
                    pd.DataFrame(
                        [[product_name, mean_AWS, min_AWS, max_AWS, std_AWS]],
                        columns=["product_name", "mean", "min", "max", "std"],
                    ),
                )
            )

    print("Fishes are in the basket! let's go home!")
    stamp = datetime.datetime.now().strftime("_%Y%m%d_%H%M")
    if "cdse" in settings["Analysis"]["endpoints"]:
        file_name = f"CDSE{stamp}.csv"
        results_CDSE.to_csv(
            os.path.join(settings["Local"]["output"], file_name), index=False
        )
        print(f"CDSE results are saved! file name: {file_name}")

    if "aws" in settings["Analysis"]["endpoints"]:
        file_name = f"AWS{stamp}.csv"
        results_AWS.to_csv(
            os.path.join(settings["Local"]["output"], file_name), index=False
        )
        print(f"AWS results are saved! file name: {file_name}")

    print("Look behind you, a Three-Headed Monkey! ...")


if __name__ == "__main__":
    print("Welcome to the BlueFish lake!")
    main()
