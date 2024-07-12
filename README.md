# CDSE S3 Testbed
***

The CDSE S3 testbed is a Python program designed to interact with a satellite imagery data catalog, specifically the Copernicus Data Space. The script performs the following tasks:

1. **Data Sampling:** It randomly selects a set of geographical points and dates from the Ground Control Points from the Sentinel 2 [Copernicus Sentinel-2 Global Reference Image (S2 GRI)](https://s2gri.csgroup.space/#/?.language=en)


2. **Data Querying:** For each selected point and date, it constructs a search query to the Copernicus Data Space catalog . The query is designed to find satellite imagery that intersects with the selected point and falls within a certain date range.


3. **Data Retrieval:** It sends the constructed query to the catalog and retrieves the corresponding satellite imagery data. The data is retrieved from two different sources: the Copernicus Data Space (CDSE) and Amazon Web Services (AWS).


4. **Performance Measurement:** It measures the time taken to retrieve the data from both sources from the pre-mounted s3 bucket. This is done multiple times for each data point to get a more accurate measure of the retrieval time.

The script is designed to be run in a Docker container, as indicated by the Docker commands below. The Docker container provides a controlled environment for the script to run in, ensuring that the performance measurements are consistent across different runs.

5. **WMS Latency Evaluation:** It measures the WMS GetCapabilities and GetMap Requests. 

## Benchmarking Methodology
***
### **BlueFish.py**

The benchmark is performed using a GDALINFO through the OSGEO module in Python. The Sentinel Band 7 has been selected out of the more common one to limit the risk of pre-caching.

GDALIFO has been selected as it is a common tool used in the geospatial community and it is able to provide a good estimation of the time needed to perform the reads of the metadata data.
Other approches could be considered, like the use of GDAL_TRANSLATE to read the data, but this would have required to take into account the performance of  
the download of the data and the time needed to perform the translation.

Object storages from the resources are automatically mounted in the docker container via S3FS. 

The cache, from the client side is disabled, to avoid any bias in the benchmark. 
As we are aware that some service provider seems to offer a cache system on the server side that cannot be disabled, a meetingation that could be taken is to test each point only once 

### **WMSLatency.py**

The benchark accepts as input a valid CDSE INSTANCE_ID, an output path for the generated reports (csv) and an integer number defining how many times (repeats) the test will be performed. 

- For each repeat the GetCapabilities request is performed and the response time is measured. Then the system sleeps for a random number of seconds (between 2 and 9). For the number of repeats the mean, median, and standrd deviation are computed
- Similarly the GetMap is measured as well. For each repeat a random layer and random respective style are selected from the available set. The test delivers the same results per layer and in total.


## Prerequisites
***
To run the CDSE S3 testbed, you need to have the following installed on your system:

- [x] A running [Docker](https://docs.docker.com/get-docker/) on your system.
- [x] A valid account on the [Copernicus Data Space](https://dataspace.copernicus.eu/) (CDSE) to access the satellite imagery data.
- [ ] A valid account on [Amazon Web Services](https://aws.amazon.com/) (AWS) to access the satellite imagery data.

Copy all the files in the `./docker` folder of your system. The `./docker` has to contain the following files:
- credential
- Dockerfile
- settings

Follow the instructions in the README file to run the CDSE S3 testbed.
