import numpy as np, os, random, requests, sys, time, xml.etree.ElementTree as ET
from osgeo import ogr
ogr.DontUseExceptions()

class WMSLatencyEvaluation(object):
    def __init__(self, instanceId, validMaskFile, outPath):
        self._instanceId = instanceId
        self._baseURL = "https://sh.dataspace.copernicus.eu/ogc/wms/{0}".format(instanceId)
        self._outPath = outPath
        self._layers = {}
        self._epsg3857 = {
            "minX": -20037508.34,
            "minY": -20048966.1,
            "maxX": 20037508.34,
            "maxY": 20048966.1
        }
        inDt = ogr.Open(validMaskFile)
        inLayer = inDt.GetLayer()
        self._ft = inLayer.GetNextFeature()

    def __getLayers(self, xmlString):
        data = ET.fromstring(xmlString)
        for layer in data.findall(".//{http://www.opengis.net/wms}Layer[@queryable=\'1\']"):
            namesAndStyles = layer.findall(".//{http://www.opengis.net/wms}Name")
            self._layers[namesAndStyles[0].text] = []
            for i in range(1, len(namesAndStyles)):
                self._layers[namesAndStyles[0].text].append(namesAndStyles[i].text)


    def testGetCapabilities(self, repeats=100):
        params = {
            "REQUEST": "GetCapabilities",
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
        }

        timeMean = 0
        timeStDev = 0
        median = list(range(repeats))
        response = None
        for i in range(repeats):
            response = requests.get(self._baseURL, params=params)
            tm = response.elapsed.total_seconds()
            median[i] = tm
            timeMean += tm/repeats
            timeStDev += tm*tm/repeats
            secondsToWait = random.randint(2,9)
            print("GetCapabilities completed in: {0}, next try in {1} seconds".format( tm, secondsToWait))
            if (repeats > 1):
                time.sleep(secondsToWait)

        median.sort()
        md = median[int(np.floor(repeats/2))]
        timeStDev = np.sqrt(timeStDev - timeMean*timeMean)

        #csv output file
        outFl = open(os.path.join(self._outPath,"GetCapabilitiesEvaluation.csv"), "w")
        outFl.write("Repeats,Mean (s),Median (s),Standard Deviation (s)\n")
        outFl.write("{0},{1},{2},{3}\n".format(repeats,timeMean,md, timeStDev))
        outFl.close()
        
        self.__getLayers(response.text)

    def testGetMap(self, repeats=100, width = 1237, height=589):
        layerKeys = list(self._layers.keys())

        timeMean = 0
        timeStDev = 0
        median = list(range(repeats))
        response = None

        layerMean = {}
        layerStdev = {}
        layerMedian = {}

        for key in layerKeys:
            layerMean[key] = 0
            layerStdev[key] = 0
            layerMedian[key] = []

        for i in range(repeats):
            #getting an origin within the valid mask
            inMask = False
            minX = 0
            minY = 0
            while (not inMask):
                minX = random.uniform(self._epsg3857["minX"], self._epsg3857["maxX"])
                minY = random.uniform(self._epsg3857["minY"], self._epsg3857["maxY"])

                pnt = ogr.Geometry(ogr.wkbPoint)
                pnt.SetPoint_2D(0, minX, minY)
                inMask = self._ft.GetGeometryRef().Intersects(pnt)

            maxX = minX + width*19.2720933430599
            maxY = minY + height*19.2720933430599

            layerId = random.randint(0,len(self._layers)-1)
            layerName = layerKeys[layerId]
            styleId = random.randint(0, len(self._layers[layerName])-1)
            style  = self._layers[layerName][styleId]

            params = {
                "REQUEST": "GetMap",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "LAYERS": layerName,
                "STYLE": style,
                "FORMAT": "image/png",
                "DPI":96,
                "MAP_RESOLUTION":96,
                "BBOX":"{0},{1},{2},{3}".format(minX, minY, maxX, maxY),
                "WIDTH":width,
                "HEIGHT":height,
            }
            response = requests.get(self._baseURL, params=params)
            #print(response.url)

            tm = response.elapsed.total_seconds()
            median[i] = tm
            timeMean += tm / repeats
            timeStDev += tm * tm / repeats
            secondsToWait = random.randint(2, 9)

            layerMean[layerName] += tm
            layerStdev[layerName] += tm * tm
            layerMedian[layerName].append(tm)

            print("GetMap Reqeuest for Layer: {0}, Style: {1}, Completed in {2}s, next try in {3}s".
                  format(layerName, style, tm, secondsToWait))

            if (repeats > 1):
                time.sleep(secondsToWait)

        median.sort()
        timeStDev = np.sqrt(timeStDev - timeMean * timeMean)
        #per layer stats

        # csv output file
        outFl = open(os.path.join(self._outPath,"GetMapEvaluation.csv"), "w")
        outFl.write("Layer,Repeats,Mean (s),Median (s),Standard Deviation (s)\n")

        for layerName in layerKeys:
            layerrepeats = len(layerMedian[layerName])
            if layerrepeats > 0:
                layerMean[layerName] /= layerrepeats
                layerStdev[layerName] = np.sqrt(layerStdev[layerName]/layerrepeats - layerMean[layerName]*layerMean[layerName])
                layerMedian[layerName].sort()
                md = layerMedian[layerName][int(np.floor(layerrepeats / 2))]
                outFl.write("{0},{1},{2},{3},{4}\n".format(layerName, layerrepeats, layerMean[layerName], md,
                          layerStdev[layerName]))


        outFl.write("Total,{0},{1},{2},{3}\n".format(repeats, timeMean,median[int(np.floor(repeats / 2))],
                                                                                    timeStDev))
        outFl.close()


def main():
    if len(sys.argv) < 4:
        print("usage: python wms_latency_evaluation.py cdse_instance_id valid_mask_file output_report_path repeats")
        return 1

    obj = WMSLatencyEvaluation(sys.argv[1], sys.argv[2], sys.argv[3])
    obj.testGetCapabilities(int(sys.argv[4]))
    obj.testGetMap(int(sys.argv[4]))

if __name__ == "__main__":
    main()
