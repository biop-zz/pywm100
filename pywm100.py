#!/usr/bin/python
# -*- coding: utf-8 -*-
# Philippe Perroud
#
# need to be run as root (fedora 14) or modify usb rules
#

import usb
import time
import os
import dataproc
import datetime
from optparse import OptionParser

DEVICEID = 0x0fde
PRODUCTID = 0x0105

def findInterface():
  device = 0;

  # find device
  busses = usb.busses()

  for bus in busses:
	  devices = bus.devices
	  for dev in devices:
		  #print dev.idVendor, dev.idProduct
		  if dev.idVendor==DEVICEID and dev.idProduct==PRODUCTID:
			  device = dev
			  conf = dev.configurations[0]
			  intf = conf.interfaces[0][0]
  if device == 0:
	  print "Could not find device"
	  exit()

  # device find, now open it and claim

  interface = device.open()
  return interface

def initInterface(interface):
  try:
    interface.reset()
  except:
    print "cannot reset interface"
    exit()
  try:
    interface.detachKernelDriver(0)
  except:
    print "cannot  interface.detachKernelDriver(0)"
  try:
    interface.detachKernelDriver(1)
  except:
    print "cannot  interface.detachKernelDriver(1)"
  try:
    interface.setConfiguration(conf)
  except:
    print "cannot interface.setConfiguration(conf)"
  try:
    interface.claimInterface(intf)
  except:
    print "cannot interface.claimInterface(intf)"
  return True

#USBC
#buffer1 = (0x55, 0x53, 0x42, 0x43,  0,  8,  1,  0)
buffer_a1 = (0x55, 0x53, 0x42, 0x43,  0x00,  0x01,  0x02,  0x00)
buffer_a2 = (0x01, 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00)
buffer_a3 = (0x55, 0x53, 0x42, 0x43,  0x00,  0x01,  0x01,  0x00)

buffer_b1 = (0x55, 0x53, 0x42, 0x43,  0x00,  0x01,  0x02,  0x00)
buffer_b2 = (0x02, 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00)
buffer_b3 = (0x55, 0x53, 0x42, 0x43,  0x00,  0x13,  0x01,  0x00)

# reqType = usb.TYPE_CLASS | usb.RECIP_INTERFACE | usb.ENDPOINT_OUT
# which is 0x21...
reqTypeOut = usb.TYPE_CLASS | usb.RECIP_INTERFACE | usb.ENDPOINT_OUT
# setconfig is 0x9...
#a1
reqTypeIn = usb.TYPE_CLASS | usb.RECIP_INTERFACE | usb.ENDPOINT_IN
# dt_config is 2...
GET_REPORT = 0x01
SET_REPORT = 0x09

INPUT_REPORT = 0x0100
FEATURE_REPORT = 0x0300

#try:
TimeOut=5000

def getRemainingHours(interface):
  interface.controlMsg(reqTypeOut, 0x09, buffer_a1, 0x0200, 0x01,TimeOut)
  interface.controlMsg(reqTypeOut, 0x09, buffer_a2, 0x0200, 0x00,TimeOut)
  interface.controlMsg(reqTypeOut, 0x09, buffer_a3, 0x0200, 0x01,TimeOut)
  result = interface.controlMsg(reqTypeIn, 0x01, 8, 0x0300, 0x00,TimeOut)
  #print "result:",result
  #print "Result=%s" % (' '.join(["%02X"% x for x in result]))
  #print "Remaining hours=%ih" % result[0]


def getTimeActivityUsage(interface):
 #while (True):
  #handle.controlMsg(reqType, usb.REQ_SET_CONFIGURATION, reqBuffer, value=usb.DT_CONFIG, index=0)
  interface.controlMsg(reqTypeOut, 0x09, buffer_b1, 0x0200, 0x01,TimeOut)
  interface.controlMsg(reqTypeOut, 0x09, buffer_b2, 0x0200, 0x00,TimeOut)
  interface.controlMsg(reqTypeOut, 0x09, buffer_b3, 0x0200, 0x01,TimeOut)
  result = interface.controlMsg(reqTypeIn, 0x01, 24, 0x0300, 0x00,TimeOut)
  #print "Result=%s" % (' '.join(["%02X"% x for x in result]))
  date=result[7:14]
  datestr=dataproc.makeDateString(date)
  activity=(result[14]&0x0f)*10+(result[14]>>4)
  otherstr=''.join(["%02X"% x for x in result[15:17]])
  maxmem=''.join(["%02X"% x for x in result[17:19]])
  maxmem=maxmem[::-1]
  otherstrrev=otherstr[::-1]
  used=int(otherstrrev,16)
  #print "other:",(' '.join(["%02X"% x for x in other]))
  print "time:%s activities=%-2i used=%i max=%i (available %2.1f%%)" % (datestr,activity,used,int(maxmem,16),100 - used*100.0/int(maxmem,16))
  #time.sleep(10)
  lastindex=used*2
  return lastindex

def setTime(interface):
#- Device reports 1 activity, 99% free memory
#- Sync Time (3rd July 2010, 12:27:51pm)

#d64e7e00 2344479517 S Co:2:004:0 s 21 09 0200 0001 0008 8 = 55534243 00070200
#d64e7e00 2344482919 C Co:2:004:0 0 8 >
#d64e7e00 2344484523 S Co:2:004:0 s 21 09 0200 0000 0010 16 = 04157221 30700100 00000000 00000000
#                                                             04 51 27 12 03 07 10 00  
#                                                             2001/07/03 12h27'51
#d64e7e00 2344494918 C Co:2:004:0 0 16 >
#d64e7980 2347516374 S Co:2:004:0 s 21 09 0200 0001 0008 8 = 55534243 00010200

  buffer_synctime_1 = (0x55, 0x53, 0x42, 0x43,  0x00,  0x07,  0x02,  0x00)
  buffer_synctime_2 = (0x04, 0x15,0x72,0x21,0x30,0x70,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00)

  interface.controlMsg(reqTypeOut, 0x09, buffer_synctime_1, 0x0200, 0x01,TimeOut)
  dt=datetime.datetime.now()
  second= dt.second / 10 + dt.second % 10 *16 
  minute=dt.minute  / 10 + dt.minute % 10 *16 
  hour=dt.hour  / 10 + dt.hour % 10 *16
  day=dt.day  / 10 + dt.day % 10 *16
  month=dt.month  / 10 + dt.month % 10 *16
  year=(dt.year % 100 )  / 10 + dt.year % 10 *16
  #print "%x %x %x %x %x %x" % (second,minute,hour,day,month,year)

  #print "buffer=%s" % (' '.join(["%02X"% x for x in buffer_synctime_2]))
  buffer_synctime_2 = (0x04, second,minute,hour,day,month,year,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00)
  interface.controlMsg(reqTypeOut, 0x09, buffer_synctime_2, 0x0200, 0x00,TimeOut)
  #print "buffer=%s" % (' '.join(["%02X"% x for x in buffer_synctime_2]))
  time.sleep(0.2)
  
  
  
  
def readData(index,TimeOut=3000,min_index=1,max_index=1019):

  if index <0 or index > max_index: 
    print "Index error"
    return ([0],1),False
  add2  = index / 16 /16
  add1  = (index - add2 * 16 *16 ) / 16
  add0  = index  % 16
  
  byte0 = 0x06
  byte1= add0
  byte1 = byte1 << 4
  byte1 += add1
  byte2 = add2
  byte2 = byte2 <<4
  #print "add[% 4i]:%03x add:%02x%02x%02x" % (index,add2*256+add1*16+add0,byte0,byte1,byte2)
  buffer_c1 = (0x55, 0x53, 0x42, 0x43,  0x00,  0x03,  0x02,  0x00)
  buffer_c2 = (byte0, byte1,byte2,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00)
  buffer_c3 = (0x55, 0x53, 0x42, 0x43,  0x00,  0x40,  0x01,  0x00)

  interface.controlMsg(reqTypeOut, 0x09, buffer_c1, 0x0200, 0x01,TimeOut)
  interface.controlMsg(reqTypeOut, 0x09, buffer_c2, 0x0200, 0x00,TimeOut)
  interface.controlMsg(reqTypeOut, 0x09, buffer_c3, 0x0200, 0x01,TimeOut)
  result = interface.controlMsg(reqTypeIn, 0x01, 64, 0x0300, 0x00,TimeOut)
  if len(result)==16:
    #Different from Graeme, my device seems buggy, need to read twice to get correct data
    #print" try again"
    interface.controlMsg(reqTypeOut, 0x09, buffer_c3, 0x0200, 0x01,TimeOut)
    result = interface.controlMsg(reqTypeIn, 0x01, 64, 0x0300, 0x00,TimeOut)
  return result,True
  
  
parser = OptionParser()
parser.add_option("-f", "--fitlog",
                  action="store_true", dest="fitlog", default=True,
                  help="produce fitlog format file (default)")
parser.add_option("-m", "--hrm",
                  action="store_true", dest="hrm", default=False,
                  help="produce hrm format file")
parser.add_option("-a", "--hrmax", type="int", dest="hrmax",default=180)
parser.add_option("-b", "--hrmin", type="int", dest="hrmin",default=50)
parser.add_option("-c", "--filter",
                  action="store_true", dest="filter", default=False,
                  help="filter out data:limit to values between hrmin and hrmax")

(options, args) = parser.parse_args()
print "options:",options

interface=findInterface()
initInterface(interface)
#getRemainingHours(interface)
#lastindex=getTimeActivityUsage(interface)
#print "set new time"
setTime(interface)
lastindex=getTimeActivityUsage(interface)

i=0
data=[]
extra=2
H1=0xFC

#while True and extra > 0 and i <lastindex:
while i <lastindex:
  i+=1
  result,status=readData(i)
  data.extend(result)
  #print "Data[%3i]:%s" % (i,' '.join(["%02X"% x for x in result]))
  
if lastindex > 0:
  print "Process data ..."
  output_fmt=""
  if options.hrm:
    output_fmt='hrm'
  elif options.fitlog:
    output_fmt='fitlog'
  dataproc.dataProcess(data,output_fmt=output_fmt,hrmax_ref=options.hrmax,hrmin_ref=options.hrmin,filterOut=options.filter,offset=0)

try:
  interface.releaseInterface()
  print "Release Interface"
except:
  pass



