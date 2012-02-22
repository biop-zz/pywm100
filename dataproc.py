#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division

import datetime,os,time

def makeDateString(result,datetimeformat=False):
  if len(result) !=7: 
    return "makeDateString:Error"    
  s=(result[0]&0x0f)*10+(result[0]>>4)
  m=(result[1]&0x0f)*10+(result[1]>>4)
  h=(result[2]&0x0f)*10+(result[2]>>4)
  d=(result[3]&0x0f)*10+(result[3]>>4)
  mo=(result[4]&0x0f)*10+(result[4]>>4)
  #ye=(result[6]&0x0f)*100+(result[6]>>4)*1000+(result[5]&0x0f)+(result[5]>>4)*10
  ye=(result[6]&0x0f)*100+(result[6]>>4)*1000+(result[5]&0x0f)*10+(result[5]>>4)*1
  if datetimeformat:
    return datetime.datetime(ye,mo,d,h,m,s)
  else:
    return "%4i%02i%02i_%02ih%02imin%02i" % (ye,mo,d,h,m,s)

def makeDurationString(d):
   mn=d//60
   s=d%60
   txt="%3imin%2i" % (mn,s)
   return txt



def recordFormat(record,dt,step=2,dtformat="%Y/%m/%d,%Hh%M:%S"):
  """ step could be 5s on some device"""
  max  = len(record)
  str=''
  prevhr=0
  for i in range(0,max):
     dtcur = dt + datetime.timedelta(seconds=i*step)
     if record[i]==0: 
	hr=prevhr
     else:
        hr=record[i]
        prevhr=hr
     str+="%s,%i\n" % (dtcur.strftime(dtformat),hr)
  return str  
 
def recordHrmFormat(record,dt,step=2):
  """ step could be 5s on some device"""
  max=len(record)
  Date = dt.strftime("%Y%m%d");
  StartTime = dt.strftime("%H:%M:%S.0")
  Length = str(datetime.timedelta(seconds=step*max))
  txt="""[Params]
Version=107
SMode=000000000
Date=%s
StartTime=%s
Length=%s
Interval=2

[HRData]
""" % (Date,StartTime,Length)
  prevhr=0
  for i in range(0,max):
     if record[i]==0: 
	hr=prevhr
     else:
        hr=record[i]
        prevhr=hr
     txt+="%i\n" % hr
  return txt

def recordFitlogFormat(record,dt,step=2,dtformat="%Y/%m/%d,%Hh%M:%S"):
  """ step could be 5s on some device"""
  max=len(record)
  dtnowtxt=datetime.datetime.now().strftime(dtformat)
  dttxt=dt.strftime(dtformat)
  txt="""<?xml version="1.0" encoding="utf-8"?>
<FitnessWorkbook xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.zonefivesoftware.com/xmlschemas/FitnessLogbook/v2">
<AthleteLog>
  <Athlete Id="3debfbe3-271d-47fd-9c6d-474d9e9948e7" Name="Philippe" />
  <Activity StartTime="%s" Id="c5009569-718c-4eba-9996-70afe3d22e08">
    <Metadata Source="Cardio Connect Kalenji" Created="%s" Modified="%s" />
    <Duration TotalSeconds="%i" />
    <Name>Cardio Connect Kalenji</Name>
    <Category Id="fa756214-cf71-11db-9705-005056c00008" Name="Mes séances" />
      <Track StartTime="%s">\n""" % (dttxt,dtnowtxt,dtnowtxt,step*max,dttxt)
  prevhr=0
  for i in range(0,max):
     s=i*step
     if record[i]==0: 
	hr=prevhr
     else:
        hr=record[i]
        prevhr=hr
     txt+="""        <pt tm="%i" hr="%i" />\n""" % (s,hr)
  txt+="""      </Track>
    </Activity>
  </AthleteLog>
</FitnessWorkbook>"""
  return txt   

def calAverage(record,hrmax_ref=175,hrmin_ref=50):
    hrmoy=0
    hrmax=0
    for hr in record:
      hrmoy+=hr
      if hr > hrmax:
	hrmax=hr
    hrmoy/=len(record)
    return hrmoy,hrmax


def dataProcess(data,hrmax_ref=180,hrmin_ref=50,filterOut=True,offset=0):
  H1=0xFC
  H2=0xFA
  EOF=0xFF
  i=0
  totalLength=0
  Ok=True
  while Ok:
    i+=1
    #print "EOF",data[data.index(H2):].index(EOF)
    if data.count(H2)>0 and data.count(H1)>0:
      if data[data.index(H1)+1]==data[data.index(H2)]:
        data[0:data.index(H2)+1]=[]
      else:
	print "pb"
	break
      if data[0]==EOF: break
    elif data.count(EOF)>0:
      print "only EOF,no header"
      break
    #process header
    date=data[0:7]
    datestr=makeDateString(date)
    data[0:7]=[]
    if data.count(H1) > 0 and data.index(EOF) > data.index(H1):
      #keep data until H1
      record=data[0:data.index(H1)]
    elif data.count(EOF)>0 :
      #keep data until EOF
      record=data[0:data.index(EOF)]
      #break
    else:
      #keep all data until the end
      record=data[0:]
      Ok=False
    hrmoy,hrmax=calAverage(record,hrmax_ref,hrmin_ref)

    if offset!=0:
      for j,hr in enumerate(record):
        if hrmin_ref < hr + offset : record[j]=hr + offset

    if filterOut:
      for j,hr in enumerate(record):
	if hr > hrmax_ref:
	  record[j]=hrmoy
      
    hrmoy,hrmax=calAverage(record,hrmax_ref,hrmin_ref)
    #print "hrmoy=%.1f hrmax=%.0f" %(hrmoy,hrmax)
      
    totalLength+=len(record)
    txt="Activity no:%2i at %s [%s], hrmoy=%.1f hrmax=%.0f" % (i,datestr,str(datetime.timedelta(seconds=len(record)*2)),hrmoy,hrmax)
    #print "record[",len(record),"]=",record
    filename='data/' + datestr + '.hrm'
    print "filename=%s" % filename
    if not os.path.isfile(filename):
      if not os.path.exists('data'):
        os.mkdir('data')
      #f=open(datestr + '.fitlog','w')
      f=open(filename,'w')
      #recordstr=recordFitlogFormat(record,makeDateString(date,datetimeformat=True),dtformat="%Y-%m-%dT%H:%M:%SZ")
      recordstr=recordHrmFormat(record,makeDateString(date,datetimeformat=True))
      f.writelines(recordstr)
      f.close()
      txt +=" => saved"
      print txt
    else:
      txt +=" => %s exists already, not saved" % filename
      print txt
    #print "%s done" % filename
  print "Total Length=%i Total Duration=%is [%s]" % (totalLength,totalLength*2,str(datetime.timedelta(seconds=totalLength*2)))

if __name__ == '__main__':
  f = open('data.txt','r')
  datastr=f.readline()
  print datastr
  data1=datastr.split(',')
  data=[]
  for i in data1:
    data.append(int(i))
  print data
  dataProcess(data)



