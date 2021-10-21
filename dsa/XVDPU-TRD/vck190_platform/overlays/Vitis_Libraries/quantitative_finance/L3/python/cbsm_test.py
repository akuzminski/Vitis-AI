#!/usr/bin/env python3

# argument checking and help
import argparse
parser = argparse.ArgumentParser(
    description='Example of the Black-Scholes-Merton Closed Form financial model running on a FPGA.')
required = parser.add_argument_group("required arguments")
required.add_argument("-x","--xclbin_file", dest="xclbin_filename", type=str, required=True,
    help="The model hardware bitstream xclbin filename. Build instructions for which are in '/<path to xf_fintech>/L2/tests/CFBlackScholesMerton'")
required.add_argument("-c","--card",dest="card_type", type=str,required=True,
    help='Current supported Alveo cards are u200 and u250')
args = parser.parse_args()
# State test financial model and args entered
print("+---------------------------------------------------------------------------------")
print(parser.description)
print(args)
print("+---------------------------------------------------------------------------------")

# Ensure environmental variables i.e. paths are set to the named the modules
import sys
# Check not using python 2
if sys.version.startswith("2"):
    sys.exit("Seem to be running with the no longer supported python 2 - require version 3")
from os.path import exists
from xf_fintech_python import DeviceManager, CFBlackScholesMerton, OptionType

# Basic checking that the number of arguments are correct
if not (args.card_type == "u250" or args.card_type == "u200"):
    sys.exit("This version executes on either card type u200 or u250")
if not exists(args.xclbin_filename):
    sys.exit("Please check the supplied FPGA load filename - program does not see it")

# Declaring Variables
deviceList = DeviceManager.getDeviceList(args.card_type) # Pass in the card type from the command line

if len(deviceList) == 0 : # Check at least one card found
    sys.exit(("Please check that you have a "+args.card_type+" card present and ready for use"))

lastruntime = 0
numAssets = 0
# Inputs
stockPriceList = []
strikePriceList = []
volatilityList = []
riskFreeRateList= []
timeToMaturityList = []
dividendYieldList = []
# checklist of expected result, and tolerance
expectedResultList = []
tolerance =  0.1
# Outputs - declaring them as empty lists
optionPriceList = []
deltaList = []
gammaList = []
vegaList = []
thetaList = []
rhoList = []


# Example financial data to test the module, same as used in the C++ example script
test_data_list = [
    [50, 100, 0.0, 0.1, 1, 0.02, 0.000000],      [50, 100, 0.01, 0.1, 1, 0.02, 0.000000],
    [50, 100, 0.02, 0.1, 1, 0.02, 0.000000],     [50, 100, 0.03, 0.1, 1, 0.02, 0.000000],
    [50, 100, 0.05, 0.1, 1, 0.02, 0.000000],     [50, 100, 0.07, 0.1, 1, 0.02, 0.000000],
    [50, 100, 0.1, 0.1, 1, 0.02, 0.000000],      [50, 100, 0.25, 0.1, 1, 0.02, 0.000002],
    [50, 100, 0.01, 0.1, 1, 0.0, 0.000000],      [50, 100, 0.01, 0.1, 1, 0.01, 0.000000],
    [50, 100, 0.01, 0.1, 1, 0.02, 0.000000],     [50, 100, 0.01, 0.1, 1, 0.03, 0.000000],
    [50, 100, 0.01, 0.1, 1, 0.05, 0.000000],     [50, 100, 0.01, 0.1, 1, 0.07, 0.000000],
    [50, 100, 0.01, 0.1, 1, 0.1, 0.000000],      [50, 100, 0.01, 0.1, 1, 0.25, 0.000000],
    [50, 100, 0.01, 0.01, 1, 0.02, 0.000000],    [50, 100, 0.01, 0.05, 1, 0.02, 0.000000],
    [50, 100, 0.01, 0.1, 1, 0.02, 0.000000],     [50, 100, 0.01, 0.25, 1, 0.02, 0.012620],
    [50, 100, 0.01, 1.1, 1, 0.02, 11.161774],    [50, 100, 0.01, 2.1, 1, 0.02, 29.159644],
    [50, 100, 0.01, 0.1, 0.3, 0.02, 0.000000],   [50, 100, 0.01, 0.1, 1, 0.02, 0.000000],
    [50, 100, 0.01, 0.1, 3, 0.02, 0.000038],     [100, 100, 0.0, 0.1, 1, 0.02, 3.036848],
    [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],    [100, 100, 0.02, 0.1, 1, 0.02, 3.908798],
    [100, 100, 0.03, 0.1, 1, 0.02, 4.396423],    [100, 100, 0.05, 0.1, 1, 0.02, 5.471349],
    [100, 100, 0.07, 0.1, 1, 0.02, 6.670211],    [100, 100, 0.1, 0.1, 1, 0.02, 8.667360],
    [100, 100, 0.25, 0.1, 1, 0.02, 20.171748],   [100, 100, 0.01, 0.1, 1, 0.0, 4.485236],
    [100, 100, 0.01, 0.1, 1, 0.01, 3.948082],    [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],
    [100, 100, 0.01, 0.1, 1, 0.03, 3.006631],    [100, 100, 0.01, 0.1, 1, 0.05, 2.234944],
    [100, 100, 0.01, 0.1, 1, 0.07, 1.619499],    [100, 100, 0.01, 0.1, 1, 0.1, 0.949838],
    [100, 100, 0.01, 0.1, 1, 0.25, 0.023864],    [100, 100, 0.01, 0.01, 1, 0.02, 0.082074],
    [100, 100, 0.01, 0.05, 1, 0.02, 1.511434],   [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],
    [100, 100, 0.01, 0.25, 1, 0.02, 9.314906],   [100, 100, 0.01, 1.1, 1, 0.02, 40.655709],
    [100, 100, 0.01, 2.1, 1, 0.02, 69.085523],   [100, 100, 0.01, 0.1, 0.3, 0.02, 2.024682],
    [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],    [100, 100, 0.01, 0.1, 3, 0.02, 5.262747],
    [150, 100, 0.0, 0.1, 1, 0.02, 47.029964],    [150, 100, 0.01, 0.1, 1, 0.02, 48.024923],
    [150, 100, 0.02, 0.1, 1, 0.02, 49.010001],   [150, 100, 0.03, 0.1, 1, 0.02, 49.985290],
    [150, 100, 0.05, 0.1, 1, 0.02, 51.906875],   [150, 100, 0.07, 0.1, 1, 0.02, 53.790425],
    [150, 100, 0.1, 0.1, 1, 0.02, 56.546061],    [150, 100, 0.25, 0.1, 1, 0.02, 69.149723],
    [150, 100, 0.01, 0.1, 1, 0.0, 50.995060],    [150, 100, 0.01, 0.1, 1, 0.01, 49.502560],
    [150, 100, 0.01, 0.1, 1, 0.02, 48.024923],   [150, 100, 0.01, 0.1, 1, 0.03, 46.562008],
    [150, 100, 0.01, 0.1, 1, 0.05, 43.679802],   [150, 100, 0.01, 0.1, 1, 0.07, 40.854912],
    [150, 100, 0.01, 0.1, 1, 0.1, 36.723165],    [150, 100, 0.01, 0.1, 1, 0.25, 18.034406],
    [150, 100, 0.01, 0.01, 1, 0.02, 48.024818],  [150, 100, 0.01, 0.05, 1, 0.02, 48.024818],
    [150, 100, 0.01, 0.1, 1, 0.02, 48.024923],   [150, 100, 0.01, 0.25, 1, 0.02, 48.752211],
    [150, 100, 0.01, 1.1, 1, 0.02, 78.314027],   [150, 100, 0.01, 2.1, 1, 0.02, 111.930458],
    [150, 100, 0.01, 0.1, 0.3, 0.02, 49.404964], [150, 100, 0.01, 0.1, 1, 0.02, 48.024923],
    [150, 100, 0.01, 0.1, 3, 0.02, 44.328384],   [50, 100, 0.01, 0.1, 1, 0.01, 0.000000],
    [60, 100, 0.01, 0.1, 1, 0.01, 0.000000],     [70, 100, 0.01, 0.1, 1, 0.01, 0.000370],
    [80, 100, 0.01, 0.1, 1, 0.01, 0.039517],     [90, 100, 0.01, 0.1, 1, 0.01, 0.705293],
    [100, 100, 0.01, 0.1, 1, 0.01, 3.948082],    [110, 100, 0.01, 0.1, 1, 0.01, 10.844954],
    [120, 100, 0.01, 0.1, 1, 0.01, 19.946863],   [130, 100, 0.01, 0.1, 1, 0.01, 29.716802],
    [140, 100, 0.01, 0.1, 1, 0.01, 39.603156],   [150, 100, 0.01, 0.1, 1, 0.01, 49.502560],
    [100, 100, 0.0, 0.1, 1, 0.01, 3.490220],     [100, 100, 0.01, 0.1, 1, 0.01, 3.948082],
    [100, 100, 0.02, 0.1, 1, 0.01, 4.440608],    [100, 100, 0.03, 0.1, 1, 0.01, 4.967061],
    [100, 100, 0.05, 0.1, 1, 0.01, 6.116985],    [100, 100, 0.07, 0.1, 1, 0.01, 7.385101],
    [100, 100, 0.1, 0.1, 1, 0.01, 9.471079],     [100, 100, 0.25, 0.1, 1, 0.01, 21.148769],
    [100, 100, 0.01, 0.01, 1, 0.01, 0.394971],   [100, 100, 0.01, 0.05, 1, 0.01, 1.974658],
    [100, 100, 0.01, 0.1, 1, 0.01, 3.948082],    [100, 100, 0.01, 0.25, 1, 0.01, 9.848664],
    [100, 100, 0.01, 1.1, 1, 0.01, 41.352463],   [100, 100, 0.01, 2.1, 1, 0.01, 69.925427],
    [100, 100, 0.01, 0.1, 0.3, 0.01, 2.173331],  [100, 100, 0.01, 0.1, 1, 0.01, 3.948082],
    [100, 100, 0.01, 0.1, 3, 0.01, 6.697292],    [50, 100, 0.01, 0.1, 1, 0.1, 0.000000],
    [60, 100, 0.01, 0.1, 1, 0.1, 0.000000],      [70, 100, 0.01, 0.1, 1, 0.1, 0.000006],
    [80, 100, 0.01, 0.1, 1, 0.1, 0.002016],      [90, 100, 0.01, 0.1, 1, 0.1, 0.086171],
    [100, 100, 0.01, 0.1, 1, 0.1, 0.949838],     [110, 100, 0.01, 0.1, 1, 0.1, 4.227734],
    [120, 100, 0.01, 0.1, 1, 0.1, 10.572463],    [130, 100, 0.01, 0.1, 1, 0.1, 18.809969],
    [140, 100, 0.01, 0.1, 1, 0.1, 27.697253],    [150, 100, 0.01, 0.1, 1, 0.1, 36.723165],
    [100, 100, 0.0, 0.1, 1, 0.1, 0.791893],      [100, 100, 0.01, 0.1, 1, 0.1, 0.949838],
    [100, 100, 0.02, 0.1, 1, 0.1, 1.131235],     [100, 100, 0.03, 0.1, 1, 0.1, 1.337931],
    [100, 100, 0.05, 0.1, 1, 0.1, 1.833875],     [100, 100, 0.07, 0.1, 1, 0.1, 2.448868],
    [100, 100, 0.1, 0.1, 1, 0.1, 3.608276],      [100, 100, 0.25, 0.1, 1, 0.1, 12.849459],
    [100, 100, 0.01, 0.01, 1, 0.1, 0.000000],    [100, 100, 0.01, 0.05, 1, 0.1, 0.067542],
    [100, 100, 0.01, 0.1, 1, 0.1, 0.949838],     [100, 100, 0.01, 0.25, 1, 0.1, 5.764783],
    [100, 100, 0.01, 1.1, 1, 0.1, 35.431726],    [100, 100, 0.01, 2.1, 1, 0.1, 62.697569],
    [100, 100, 0.01, 0.1, 0.3, 0.1, 1.076712],   [100, 100, 0.01, 0.1, 1, 0.1, 0.949838],
    [100, 100, 0.01, 0.1, 3, 0.1, 0.374831],     [50, 100, 0.01, 0.1, 1, 0.25, 0.000000],
    [60, 100, 0.01, 0.1, 1, 0.25, 0.000000],     [70, 100, 0.01, 0.1, 1, 0.25, 0.000000],
    [80, 100, 0.01, 0.1, 1, 0.25, 0.000003],     [90, 100, 0.01, 0.1, 1, 0.25, 0.000585],
    [100, 100, 0.01, 0.1, 1, 0.25, 0.023864],    [110, 100, 0.01, 0.1, 1, 0.25, 0.304029],
    [120, 100, 0.01, 0.1, 1, 0.25, 1.683464],    [130, 100, 0.01, 0.1, 1, 0.25, 5.211635],
    [140, 100, 0.01, 0.1, 1, 0.25, 10.951763],   [150, 100, 0.01, 0.1, 1, 0.25, 18.034406],
    [100, 100, 0.0, 0.1, 1, 0.25, 0.017668],     [100, 100, 0.01, 0.1, 1, 0.25, 0.023864],
    [100, 100, 0.02, 0.1, 1, 0.25, 0.031959],    [100, 100, 0.03, 0.1, 1, 0.25, 0.042443],
    [100, 100, 0.05, 0.1, 1, 0.25, 0.073008],    [100, 100, 0.07, 0.1, 1, 0.25, 0.121532],
    [100, 100, 0.1, 0.1, 1, 0.25, 0.245796],     [100, 100, 0.25, 0.1, 1, 0.25, 3.105672],
    [100, 100, 0.01, 0.01, 1, 0.25, 0.000000],   [100, 100, 0.01, 0.05, 1, 0.25, 0.000001],
    [100, 100, 0.01, 0.1, 1, 0.25, 0.023864],    [100, 100, 0.01, 0.25, 1, 0.25, 1.962969],
    [100, 100, 0.01, 1.1, 1, 0.25, 27.164544],   [100, 100, 0.01, 2.1, 1, 0.25, 52.179771],
    [100, 100, 0.01, 0.1, 0.3, 0.25, 0.233456],  [100, 100, 0.01, 0.1, 1, 0.25, 0.023864],
    [100, 100, 0.01, 0.1, 3, 0.25, 0.000041],    [50, 100, 0.01, 0.01, 1, 0.02, 0.000000],
    [60, 100, 0.01, 0.01, 1, 0.02, 0.000000],    [70, 100, 0.01, 0.01, 1, 0.02, 0.000000],
    [80, 100, 0.01, 0.01, 1, 0.02, 0.000000],    [90, 100, 0.01, 0.01, 1, 0.02, 0.000000],
    [100, 100, 0.01, 0.01, 1, 0.02, 0.082074],   [110, 100, 0.01, 0.01, 1, 0.02, 8.816871],
    [120, 100, 0.01, 0.01, 1, 0.02, 18.618857],  [130, 100, 0.01, 0.01, 1, 0.02, 28.420844],
    [140, 100, 0.01, 0.01, 1, 0.02, 38.222831],  [150, 100, 0.01, 0.01, 1, 0.02, 48.024818],
    [100, 100, 0.0, 0.01, 1, 0.02, 0.008406],    [100, 100, 0.01, 0.01, 1, 0.02, 0.082074],
    [100, 100, 0.02, 0.01, 1, 0.02, 0.391041],   [100, 100, 0.03, 0.01, 1, 0.02, 1.056572],
    [100, 100, 0.05, 0.01, 1, 0.02, 2.897294],   [100, 100, 0.07, 0.01, 1, 0.02, 4.780485],
    [100, 100, 0.1, 0.01, 1, 0.02, 7.536126],    [100, 100, 0.25, 0.01, 1, 0.02, 20.139789],
    [100, 100, 0.01, 0.01, 1, 0.0, 1.077916],    [100, 100, 0.01, 0.01, 1, 0.01, 0.394971],
    [100, 100, 0.01, 0.01, 1, 0.02, 0.082074],   [100, 100, 0.01, 0.01, 1, 0.03, 0.008322],
    [100, 100, 0.01, 0.01, 1, 0.05, 0.000007],   [100, 100, 0.01, 0.01, 1, 0.07, 0.000000],
    [100, 100, 0.01, 0.01, 1, 0.1, 0.000000],    [100, 100, 0.01, 0.01, 1, 0.25, 0.000000],
    [100, 100, 0.01, 0.01, 0.3, 0.02, 0.100012], [100, 100, 0.01, 0.01, 1, 0.02, 0.082074],
    [100, 100, 0.01, 0.01, 3, 0.02, 0.027994],   [50, 100, 0.01, 0.1, 1, 0.02, 0.000000],
    [60, 100, 0.01, 0.1, 1, 0.02, 0.000000],     [70, 100, 0.01, 0.1, 1, 0.02, 0.000245],
    [80, 100, 0.01, 0.1, 1, 0.02, 0.029383],     [90, 100, 0.01, 0.1, 1, 0.02, 0.575714],
    [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],    [110, 100, 0.01, 0.1, 1, 0.02, 9.945921],
    [120, 100, 0.01, 0.1, 1, 0.02, 18.805137],   [130, 100, 0.01, 0.1, 1, 0.02, 28.441738],
    [140, 100, 0.01, 0.1, 1, 0.02, 38.224524],   [150, 100, 0.01, 0.1, 1, 0.02, 48.024923],
    [100, 100, 0.0, 0.1, 1, 0.02, 3.036848],     [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],
    [100, 100, 0.02, 0.1, 1, 0.02, 3.908798],    [100, 100, 0.03, 0.1, 1, 0.02, 4.396423],
    [100, 100, 0.05, 0.1, 1, 0.02, 5.471349],    [100, 100, 0.07, 0.1, 1, 0.02, 6.670211],
    [100, 100, 0.1, 0.1, 1, 0.02, 8.667360],     [100, 100, 0.25, 0.1, 1, 0.02, 20.171748],
    [100, 100, 0.01, 0.1, 1, 0.0, 4.485236],     [100, 100, 0.01, 0.1, 1, 0.01, 3.948082],
    [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],    [100, 100, 0.01, 0.1, 1, 0.03, 3.006631],
    [100, 100, 0.01, 0.1, 1, 0.05, 2.234944],    [100, 100, 0.01, 0.1, 1, 0.07, 1.619499],
    [100, 100, 0.01, 0.1, 1, 0.1, 0.949838],     [100, 100, 0.01, 0.1, 1, 0.25, 0.023864],
    [100, 100, 0.01, 0.1, 0.3, 0.02, 2.024682],  [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],
    [100, 100, 0.01, 0.1, 3, 0.02, 5.262747],    [50, 100, 0.01, 2, 1, 0.02, 27.610220],
    [60, 100, 0.01, 2, 1, 0.02, 35.025615],      [70, 100, 0.01, 2, 1, 0.02, 42.690643],
    [80, 100, 0.01, 2, 1, 0.02, 50.556861],      [90, 100, 0.01, 2, 1, 0.02, 58.589225],
    [100, 100, 0.01, 2, 1, 0.02, 66.761436],     [110, 100, 0.01, 2, 1, 0.02, 75.053177],
    [120, 100, 0.01, 2, 1, 0.02, 83.448386],     [130, 100, 0.01, 2, 1, 0.02, 91.934119],
    [140, 100, 0.01, 2, 1, 0.02, 100.499772],    [150, 100, 0.01, 2, 1, 0.02, 109.136537],
    [100, 100, 0.0, 2, 1, 0.02, 66.605371],      [100, 100, 0.01, 2, 1, 0.02, 66.761436],
    [100, 100, 0.02, 2, 1, 0.02, 66.917133],     [100, 100, 0.03, 2, 1, 0.02, 67.072462],
    [100, 100, 0.05, 2, 1, 0.02, 67.382003],     [100, 100, 0.07, 2, 1, 0.02, 67.690040],
    [100, 100, 0.1, 2, 1, 0.02, 68.149240],      [100, 100, 0.25, 2, 1, 0.02, 70.392012],
    [100, 100, 0.01, 2, 1, 0.0, 68.427416],      [100, 100, 0.01, 2, 1, 0.01, 67.589662],
    [100, 100, 0.01, 2, 1, 0.02, 66.761436],     [100, 100, 0.01, 2, 1, 0.03, 65.942636],
    [100, 100, 0.01, 2, 1, 0.05, 64.332920],     [100, 100, 0.01, 2, 1, 0.07, 62.759727],
    [100, 100, 0.01, 2, 1, 0.1, 60.466737],      [100, 100, 0.01, 2, 1, 0.25, 50.122296],
    [100, 100, 0.01, 2, 0.3, 0.02, 41.191693],   [100, 100, 0.01, 2, 1, 0.02, 66.761436],
    [100, 100, 0.01, 2, 3, 0.02, 86.216596],     [50, 100, 0.01, 0.1, 0.3, 0.02, 0.000000],
    [60, 100, 0.01, 0.1, 0.3, 0.02, 0.000000],   [70, 100, 0.01, 0.1, 0.3, 0.02, 0.000000],
    [80, 100, 0.01, 0.1, 0.3, 0.02, 0.000019],   [90, 100, 0.01, 0.1, 0.3, 0.02, 0.045886],
    [100, 100, 0.01, 0.1, 0.3, 0.02, 2.024682],  [110, 100, 0.01, 0.1, 0.3, 0.02, 9.750184],
    [120, 100, 0.01, 0.1, 0.3, 0.02, 19.584421], [130, 100, 0.01, 0.1, 0.3, 0.02, 29.524062],
    [140, 100, 0.01, 0.1, 0.3, 0.02, 39.464512], [150, 100, 0.01, 0.1, 0.3, 0.02, 49.404964],
    [100, 100, 0.0, 0.1, 0.3, 0.02, 1.888565],   [100, 100, 0.01, 0.1, 0.3, 0.02, 2.024682],
    [100, 100, 0.02, 0.1, 0.3, 0.02, 2.166851],  [100, 100, 0.03, 0.1, 0.3, 0.02, 2.315054],
    [100, 100, 0.05, 0.1, 0.3, 0.02, 2.629394],  [100, 100, 0.07, 0.1, 0.3, 0.02, 2.967179],
    [100, 100, 0.1, 0.1, 0.3, 0.02, 3.515974],   [100, 100, 0.25, 0.1, 0.3, 0.02, 6.860052],
    [100, 100, 0.01, 0.1, 0.3, 0.0, 2.328922],   [100, 100, 0.01, 0.1, 0.3, 0.01, 2.173331],
    [100, 100, 0.01, 0.1, 0.3, 0.02, 2.024682],  [100, 100, 0.01, 0.1, 0.3, 0.03, 1.882934],
    [100, 100, 0.01, 0.1, 0.3, 0.05, 1.619886],  [100, 100, 0.01, 0.1, 0.3, 0.07, 1.383498],
    [100, 100, 0.01, 0.1, 0.3, 0.1, 1.076712],   [100, 100, 0.01, 0.1, 0.3, 0.25, 0.233456],
    [100, 100, 0.01, 0.01, 0.3, 0.02, 0.100012], [100, 100, 0.01, 0.05, 0.3, 0.02, 0.942973],
    [100, 100, 0.01, 0.1, 0.3, 0.02, 2.024682],  [100, 100, 0.01, 0.25, 0.3, 0.02, 5.274331],
    [100, 100, 0.01, 1.1, 0.3, 0.02, 23.370978], [100, 100, 0.01, 2.1, 0.3, 0.02, 43.046895],
    [50, 100, 0.01, 0.1, 1, 0.02, 0.000000],     [60, 100, 0.01, 0.1, 1, 0.02, 0.000000],
    [70, 100, 0.01, 0.1, 1, 0.02, 0.000245],     [80, 100, 0.01, 0.1, 1, 0.02, 0.029383],
    [90, 100, 0.01, 0.1, 1, 0.02, 0.575714],     [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],
    [110, 100, 0.01, 0.1, 1, 0.02, 9.945921],    [120, 100, 0.01, 0.1, 1, 0.02, 18.805137],
    [130, 100, 0.01, 0.1, 1, 0.02, 28.441738],   [140, 100, 0.01, 0.1, 1, 0.02, 38.224524],
    [150, 100, 0.01, 0.1, 1, 0.02, 48.024923],   [100, 100, 0.0, 0.1, 1, 0.02, 3.036848],
    [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],    [100, 100, 0.02, 0.1, 1, 0.02, 3.908798],
    [100, 100, 0.03, 0.1, 1, 0.02, 4.396423],    [100, 100, 0.05, 0.1, 1, 0.02, 5.471349],
    [100, 100, 0.07, 0.1, 1, 0.02, 6.670211],    [100, 100, 0.1, 0.1, 1, 0.02, 8.667360],
    [100, 100, 0.25, 0.1, 1, 0.02, 20.171748],   [100, 100, 0.01, 0.1, 1, 0.0, 4.485236],
    [100, 100, 0.01, 0.1, 1, 0.01, 3.948082],    [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],
    [100, 100, 0.01, 0.1, 1, 0.03, 3.006631],    [100, 100, 0.01, 0.1, 1, 0.05, 2.234944],
    [100, 100, 0.01, 0.1, 1, 0.07, 1.619499],    [100, 100, 0.01, 0.1, 1, 0.1, 0.949838],
    [100, 100, 0.01, 0.1, 1, 0.25, 0.023864],    [100, 100, 0.01, 0.01, 1, 0.02, 0.082074],
    [100, 100, 0.01, 0.05, 1, 0.02, 1.511434],   [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],
    [100, 100, 0.01, 0.25, 1, 0.02, 9.314906],   [100, 100, 0.01, 1.1, 1, 0.02, 40.655709],
    [100, 100, 0.01, 2.1, 1, 0.02, 69.085523],   [50, 100, 0.01, 0.1, 3, 0.02, 0.000038],
    [60, 100, 0.01, 0.1, 3, 0.02, 0.003149],     [70, 100, 0.01, 0.1, 3, 0.02, 0.061515],
    [80, 100, 0.01, 0.1, 3, 0.02, 0.472285],     [90, 100, 0.01, 0.1, 3, 0.02, 1.946350],
    [100, 100, 0.01, 0.1, 3, 0.02, 5.262747],    [110, 100, 0.01, 0.1, 3, 0.02, 10.683065],
    [120, 100, 0.01, 0.1, 3, 0.02, 17.854285],   [130, 100, 0.01, 0.1, 3, 0.02, 26.169121],
    [140, 100, 0.01, 0.1, 3, 0.02, 35.103576],   [150, 100, 0.01, 0.1, 3, 0.02, 44.328384],
    [100, 100, 0.0, 0.1, 3, 0.02, 4.185436],     [100, 100, 0.01, 0.1, 3, 0.02, 5.262747],
    [100, 100, 0.02, 0.1, 3, 0.02, 6.499358],    [100, 100, 0.03, 0.1, 3, 0.02, 7.890544],
    [100, 100, 0.05, 0.1, 3, 0.02, 11.091010],   [100, 100, 0.07, 0.1, 3, 0.02, 14.731189],
    [100, 100, 0.1, 0.1, 3, 0.02, 20.640675],    [100, 100, 0.25, 0.1, 3, 0.02, 46.939886],
    [100, 100, 0.01, 0.1, 3, 0.0, 8.378469],     [100, 100, 0.01, 0.1, 3, 0.01, 6.697292],
    [100, 100, 0.01, 0.1, 3, 0.02, 5.262747],    [100, 100, 0.01, 0.1, 3, 0.03, 4.061738],
    [100, 100, 0.01, 0.1, 3, 0.05, 2.284543],    [100, 100, 0.01, 0.1, 3, 0.07, 1.184236],
    [100, 100, 0.01, 0.1, 3, 0.1, 0.374831],     [100, 100, 0.01, 0.1, 3, 0.25, 0.000041],
    [100, 100, 0.01, 0.01, 3, 0.02, 0.027994],   [100, 100, 0.01, 0.05, 3, 0.02, 2.064242],
    [100, 100, 0.01, 0.1, 3, 0.02, 5.262747],    [100, 100, 0.01, 0.25, 3, 0.02, 14.992954],
    [100, 100, 0.01, 1.1, 3, 0.02, 61.600161],   [100, 100, 0.01, 2.1, 3, 0.02, 87.583642],
    [50, 100, 0.01, 0.1, 1, 0.02, 0.000000],     [60, 100, 0.01, 0.1, 1, 0.02, 0.000000],
    [70, 100, 0.01, 0.1, 1, 0.02, 0.000245],     [80, 100, 0.01, 0.1, 1, 0.02, 0.029383],
    [90, 100, 0.01, 0.1, 1, 0.02, 0.575714],     [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],
    [110, 100, 0.01, 0.1, 1, 0.02, 9.945921],    [120, 100, 0.01, 0.1, 1, 0.02, 18.805137],
    [130, 100, 0.01, 0.1, 1, 0.02, 28.441738],   [140, 100, 0.01, 0.1, 1, 0.02, 38.224524],
    [150, 100, 0.01, 0.1, 1, 0.02, 48.024923],   [100, 100, 0.01, 0.1, 1, 0.0, 4.485236],
    [100, 100, 0.01, 0.1, 1, 0.01, 3.948082],    [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],
    [100, 100, 0.01, 0.1, 1, 0.03, 3.006631],    [100, 100, 0.01, 0.1, 1, 0.05, 2.234944],
    [100, 100, 0.01, 0.1, 1, 0.07, 1.619499],    [100, 100, 0.01, 0.1, 1, 0.1, 0.949838],
    [100, 100, 0.01, 0.1, 1, 0.25, 0.023864],    [100, 100, 0.01, 0.01, 1, 0.02, 0.082074],
    [100, 100, 0.01, 0.05, 1, 0.02, 1.511434],   [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],
    [100, 100, 0.01, 0.25, 1, 0.02, 9.314906],   [100, 100, 0.01, 1.1, 1, 0.02, 40.655709],
    [100, 100, 0.01, 2.1, 1, 0.02, 69.085523],   [100, 100, 0.01, 0.1, 0.3, 0.02, 2.024682],
    [100, 100, 0.01, 0.1, 1, 0.02, 3.455492],    [100, 100, 0.01, 0.1, 3, 0.02, 5.262747],
    [50, 100, 0.1, 0.1, 1, 0.02, 0.000000],      [60, 100, 0.1, 0.1, 1, 0.02, 0.000013],
    [70, 100, 0.1, 0.1, 1, 0.02, 0.006695],      [80, 100, 0.1, 0.1, 1, 0.02, 0.287844],
    [90, 100, 0.1, 0.1, 1, 0.02, 2.544035],      [100, 100, 0.1, 0.1, 1, 0.02, 8.667360],
    [110, 100, 0.1, 0.1, 1, 0.02, 17.496493],    [120, 100, 0.1, 0.1, 1, 0.02, 27.154107],
    [130, 100, 0.1, 0.1, 1, 0.02, 36.942933],    [140, 100, 0.1, 0.1, 1, 0.02, 46.744110],
    [150, 100, 0.1, 0.1, 1, 0.02, 56.546061],    [100, 100, 0.1, 0.1, 1, 0.0, 10.308151],
    [100, 100, 0.1, 0.1, 1, 0.01, 9.471079],     [100, 100, 0.1, 0.1, 1, 0.02, 8.667360],
    [100, 100, 0.1, 0.1, 1, 0.03, 7.898742],     [100, 100, 0.1, 0.1, 1, 0.05, 6.473076],
    [100, 100, 0.1, 0.1, 1, 0.07, 5.204508],     [100, 100, 0.1, 0.1, 1, 0.1, 3.608276],
    [100, 100, 0.1, 0.1, 1, 0.25, 0.245796],     [100, 100, 0.1, 0.01, 1, 0.02, 7.536126],
    [100, 100, 0.1, 0.05, 1, 0.02, 7.645543],    [100, 100, 0.1, 0.1, 1, 0.02, 8.667360],
    [100, 100, 0.1, 0.25, 1, 0.02, 13.617097],   [100, 100, 0.1, 1.1, 1, 0.02, 43.229142],
    [100, 100, 0.1, 2.1, 1, 0.02, 70.369395],    [100, 100, 0.1, 0.1, 0.3, 0.02, 3.515974],
    [100, 100, 0.1, 0.1, 1, 0.02, 8.667360],     [100, 100, 0.1, 0.1, 3, 0.02, 20.640675],
    [50, 100, 0.25, 0.1, 1, 0.02, 0.000002],     [60, 100, 0.25, 0.1, 1, 0.02, 0.005005],
    [70, 100, 0.25, 0.1, 1, 0.02, 0.356736],     [80, 100, 0.25, 0.1, 1, 0.02, 3.391579],
    [90, 100, 0.25, 0.1, 1, 0.02, 10.759913],    [100, 100, 0.25, 0.1, 1, 0.02, 20.171748],
    [110, 100, 0.25, 0.1, 1, 0.02, 29.943167],   [120, 100, 0.25, 0.1, 1, 0.02, 39.743802],
    [130, 100, 0.25, 0.1, 1, 0.02, 49.545750],   [140, 100, 0.25, 0.1, 1, 0.02, 59.347736],
    [150, 100, 0.25, 0.1, 1, 0.02, 69.149723],   [100, 100, 0.25, 0.1, 1, 0.0, 22.137590],
    [100, 100, 0.25, 0.1, 1, 0.01, 21.148769],   [100, 100, 0.25, 0.1, 1, 0.02, 20.171748],
    [100, 100, 0.25, 0.1, 1, 0.03, 19.206918],   [100, 100, 0.25, 0.1, 1, 0.05, 17.315873],
    [100, 100, 0.25, 0.1, 1, 0.07, 15.480836],   [100, 100, 0.25, 0.1, 1, 0.1, 12.849459],
    [100, 100, 0.25, 0.1, 1, 0.25, 3.105672],    [100, 100, 0.25, 0.01, 1, 0.02, 20.139789],
    [100, 100, 0.25, 0.05, 1, 0.02, 20.139791],  [100, 100, 0.25, 0.1, 1, 0.02, 20.171748],
    [100, 100, 0.25, 0.25, 1, 0.02, 22.244069],  [100, 100, 0.25, 1.1, 1, 0.02, 47.523561],
    [100, 100, 0.25, 2.1, 1, 0.02, 72.440371],   [100, 100, 0.25, 0.1, 0.3, 0.02, 6.860052],
    [100, 100, 0.25, 0.1, 1, 0.02, 20.171748],   [100, 100, 0.25, 0.1, 3, 0.02, 46.939886],
]


# Count the number of entries above - sets of data
numAssets = len(test_data_list)

# Populate the input lists from the above nested list
for loop in range(0, numAssets) :
    stockPriceList += [test_data_list[loop][0]]
    strikePriceList+= [test_data_list[loop][1]]
    riskFreeRateList += [test_data_list[loop][2]]
    volatilityList += [test_data_list[loop][3]]
    timeToMaturityList += [test_data_list[loop][4]]
    dividendYieldList += [test_data_list[loop][5]]
    #This final field is not passed to the FPGA it is used to compare the result, as per the C++ example
    expectedResultList += [test_data_list[loop][6]]
    # Outputs - already declared those as empty lists



# Identify which cards are installed and choose the first available U250 card, as defined in deviceList above
print("Found these {0} device(s):".format(len(deviceList)))
for x in deviceList:
    print(x.getName())
print("Choosing the first suitable card\n")
chosenDevice = deviceList[0]

# Selecting and loading into FPGA on chosen card the financial model to be used
CFBlackScholesMerton = CFBlackScholesMerton(numAssets,args.xclbin_filename)   # warning the lower levels to accomodate at least this figure
CFBlackScholesMerton.claimDevice(chosenDevice)
#Feed in the data and request the result
print("\nRunning...")
result = CFBlackScholesMerton.run(stockPriceList, strikePriceList, volatilityList, riskFreeRateList, timeToMaturityList, dividendYieldList,
                            optionPriceList, deltaList, gammaList, vegaList, thetaList, rhoList, OptionType.Call, numAssets)
print("Done")
runtime = CFBlackScholesMerton.lastruntime()

#Format output to match the example in C++, simply to aid comparison of results
print("+-------+-----------+----------------+--------------+---------------+---------------+---------------+")
print("| Index | Price     |     Delta      |     Gamma    |     Vega      |     Theta     |     Rho       |")
print("+-------+-----------+----------------+--------------+---------------+---------------+---------------+")
for loop in range(0, numAssets) :
    print(loop,"\t%9.5f"%optionPriceList[loop],"\t%9.5f"%deltaList[loop],"\t%9.5f"%gammaList[loop],"\t%9.5f"%vegaList[loop],"\t%9.5f"%thetaList[loop],"\t%9.5f"%rhoList[loop])
    # These are usage examnples - result evaultion is possible against the pararmeters stored in the array
    # using the lines below along with the tolerance allowance however there us a degree of variation in
    # the results as shown in the c++ test please see it for detail.
    #
    #if (abs(expectedResultList[loop] - optionPriceList[loop])) > tolerance :
    #    print("Comparison failure - expected",expectedResultList[loop],"returned %9.5f"%optionPriceList[loop])


print("\nThis run took", str(runtime), "microseconds")

#Relinquish ownership of the card
CFBlackScholesMerton.releaseDevice()

sys.exit(0)
