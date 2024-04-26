# CDSE S3 Testbed
***

The CDSE S3 testbed is a Python program designed to interact with a satellite imagery data catalog, specifically the Copernicus Data Space. The script performs the following tasks:

1. **Data Sampling:** It randomly selects a set of geographical points and dates from the Ground Control Points from the Sentinel 2 [Copernicus Sentinel-2 Global Reference Image (S2 GRI)](https://s2gri.csgroup.space/#/?.language=en)


2. **Data Querying:** For each selected point and date, it constructs a search query to the Copernicus Data Space catalog . The query is designed to find satellite imagery that intersects with the selected point and falls within a certain date range.


3. **Data Retrieval:** It sends the constructed query to the catalog and retrieves the corresponding satellite imagery data. The data is retrieved from two different sources: the Copernicus Data Space (CDSE) and Amazon Web Services (AWS).


4. **Performance Measurement:** It measures the time taken to retrieve the data from both sources from the pre-mounted s3 bucket. This is done multiple times for each data point to get a more accurate measure of the retrieval time.

The script is designed to be run in a Docker container, as indicated by the Docker commands below. The Docker container provides a controlled environment for the script to run in, ensuring that the performance measurements are consistent across different runs.


## Benchmarking Methodology
***
The benchmark is performed using a GDALINFO through the OSGEO module in Python. The Sentinel Band 7 has been selected out of the more common one to limit the risk of pre-caching.

GDALIFO has been selected as it is a common tool used in the geospatial community and it is able to provide a good estimation of the time needed to perform the reads of the metadata data.
Other approches could be considered, like the use of GDAL_TRANSLATE to read the data, but this would have required to take into account the performance of  
the download of the data and the time needed to perform the translation.

Object storages from the resources are automatically mounted in the docker container via S3FS. 

The cache, from the client side is disabled, to avoid any bias in the benchmark. 
As we are aware that some service provider seems to offer a cache system on the server side that cannot be disabled, a meetingation that could be taken is to test each point only once 



## Prerequisites
***
To run the CDSE S3 testbed, you need to have the following installed on your system:

- [x] A running [Docker](https://docs.docker.com/get-docker/) on your system.
- [x] A valid account on the [Copernicus Data Space](https://dataspace.copernicus.eu/) (CDSE) to access the satellite imagery data.
- [ ] A valid account on [Amazon Web Services](https://aws.amazon.com/) (AWS) to access the satellite imagery data.

Copy all the files in the `./docker` folder of your system. The `./docker` has to contain the following files:
- BlueFish.py
- credential
- Dockerfile
- environment.yml
- settings
- GCP.7z
- README.md

## Instructions
***

### 1 - Credential file

Configure the credentials for the S3 Copernicus Data and AWS sources in the `./credential` file. 
```aws_access_key_id``` and ```aws_secret_access_key``` 
have to be set for the resources to be accessed.

To get credentials, please visit [CDSE](https://documentation.dataspace.copernicus.eu/APIs/S3.html) and [AWS documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-authentication-short-term.html).

> NOTE:
> - Credentials from the CDSE are mandatory, while the AWS credentials are optional. If the AWS credentials are not provided, the script will only retrieve data from the CDSE source.
> - CREODIAS's S3 Object Storage credentials are ***NOT*** valid to get access to the CDSE resources.  


### 2 - Set the environment variables
Adequate environment variables have to be set in the `./settings` file.

```
Collection:
  collection_name: SENTINEL-2
  product_type: S2MSI2A
  max_cloud_cover: 100                  # [not activated feature] define the max cloud cover percentage 
  start_date: 2020-01-01                # define the start date
  end_date: 2024-02-29                  # define the end date
Analysis:
  benchmark: info                       # define the benchmark type (info, transform, all )
  n_samples: 60                         # define the number of samples 
  repeat_n: 1                           # define the number of repetitions
  number_n: 1                           # define the number of repetitions within the same run (1 sould be enough) 
  dd_number: 7                          # define the expation time window that has to be considerd from the randomly selected date (es.7 would create a time span like the one here reported 07/01/2024 -> 01/01/2024 - 14/01/2024)
  endpoints: ['cdse']                   # define the endpoints to be used (for both ['cdse', 'aws'])
ControlPoints:
  path: ~/testbed/data/gcp.shp          # define the path to the control points (don't change if not needed)
  q_score: 5                            # define the quality score
Catalog:
  url: "https://catalogue.dataspace.copernicus.eu/odata/v1"         # define the url of the catalog used to select the observations
  endpoint: CDSE                        # define the endpoint to be used
Local:
    aws: ~/aws                          # do not change
    cdse: ~/cdse                        # do not change
    data: ~/testbed/data                # do not change
    output: ~/testbed/output            # do not change
```

### 3 - Build the docker image
build the docker image with the following command:

``docker build . --no-cache -t testbed:latest``

### 4 - Run the docker 
run the docker image in privileged and detach mode with the following command:

``docker run --privileged -dit testbed:latest``

> NOTE: --privileged is needed to access the S3 resources. If not used, a message like the following appears: fuse: device not found, try 'modprobe fuse' first``

### 5 - Get the container ID

get the container id with the following command:

``docker ps``

example output:

|CONTAINER ID|IMAGE|COMMAND|CREATED|STATUS|PORTS| NAMES        |
|---|---|---|---|---|---|--------------|
|f3b6b3b3b4e4|testbed:latest|"/bin/bash"|3 seconds ago|Up 2 seconds|| jolly_mendel |

### 6 - Run the testbed 
``docker exec ContainerID python /root/testbed/BlueFish.py``

### 7 - Copy the output
Copy the output from the container to the host with the following command:

``docker cp f3b6b3b3b4e4:/root/testbed/output/* ~/output/`` 

### 8 - Stop the container
Stop the container with the following command:

``docker stop f3b6b3b3b4e4``

### 9 - Remove the container
Remove the container with the following command:

``docker rm f3b6b3b3b4e4``

### 10 - Remove the image
Remove the image with the following command:

``docker rmi testbed:latest`` 

### 11 - Enjoy the output

The output will be available in the `~/output` folder

Results are stored in the `~/output` folder. The output is a `csv` file with the following columns:



times are expressed in seconds 





