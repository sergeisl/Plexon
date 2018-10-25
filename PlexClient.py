#!/usr/bin/python
#coding:utf-8

###########################################################
### A Python wrapper of PlexClient
### Written by Huangxin
###########################################################

from __future__ import division
import ctypes 
import numpy as np
import logging
logger = logging.getLogger('SpikeRecord.Plexon')
from Plexon import Plexon
from operator import attrgetter
MAX_MAP_EVENTS_PER_READ = 8000
PL_ADDataType = 5

class PlexClient(object):
    """
    A Python wrapper for Plexon PlexClient.dll
    All memory that will be manipulated in Plexon library is allocated in the PlexClient object by ndarray and ctypes array. What's important is that the length of these arrays is constant after the API calls. The length of the real array that the server transferred is in the first value of the return Tuple. We have to deal with the C library so forget the dirty code. 
    """
    def __init__(self):
        self.library = Plexon._lib
        self.MAX_MAP_EVENTS_PER_READ = MAX_MAP_EVENTS_PER_READ
        self.NumMAPEvents = np.empty(self.MAX_MAP_EVENTS_PER_READ,dtype=np.uint32)
        self.MAPSampleRate = None

        self.ServerDropped = np.empty(self.MAX_MAP_EVENTS_PER_READ,dtype=np.uint32)
        self.MMFDropped =  np.empty(self.MAX_MAP_EVENTS_PER_READ,dtype=np.uint32)
        self.PollHigh =  np.empty(self.MAX_MAP_EVENTS_PER_READ,dtype=np.uint32)
        self.PollLow =  np.empty(self.MAX_MAP_EVENTS_PER_READ,dtype=np.uint32)
        self.pServerEventBuffer = (Plexon.PL_Wave * self.MAX_MAP_EVENTS_PER_READ)()
        self.ServerEventBuffer = (Plexon.PL_Event * self.MAX_MAP_EVENTS_PER_READ)()
    def __enter__(self):
        self.InitClient()
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.CloseClient()
    def InitClient(self):
        """
        InitClient() 

        Initializes PlexClient.dll for a client. Opens MMF's and registers the client with the server. Remeber to close the client by yourself. Or try the 'with' statement to initialize the PlexClient class.
        """
        if not self.library: 
            logger.warning('Failed to load Plexon client library.')
            return
        if not Plexon.PL_InitClientEx3(0, None, None):
            raise RuntimeError("Failed to initiate Plexon client.")
        TimeStampTick = self.GetTimeStampTick()
        if not TimeStampTick in (25, 40, 50):
            raise RuntimeError("Failed to get timestamp tick.")
        self.MAPSampleRate = 1000 / TimeStampTick * 1000
    def CloseClient(self):
        """
        CloseClient() 

        Cleans up PlexClient.dll (deletes CClient object) and
        Sends ClientDisconnected command to the server.
        The server decrements the counter for the number of connected clients.
        """
        if not self.library: return
        Plexon.PL_CloseClient()

    def IsSortClientRunning(self):
        """
        IsSortClientRunning() -> bool

        Return whether the SortClient is running. 
        """
        return Plexon.PL_IsSortClientRunning()
    def GetTimeStampTick(self):
        """
        GetTimeStampTick() -> integer

        Return timestamp resolution in microseconds.
        """
        return Plexon.PL_GetTimeStampTick()
    def IsLongWaveMode(self):
        """
        IsLongWaveMode() -> bool

        Return whether the server is using long wave mode.
        """
        return Plexon.PL_IsLongWaveMode()
    
    def getLongWaveFormStructures(self):       
        num = ctypes.c_int(MAX_MAP_EVENTS_PER_READ)
        Plexon.PL_GetLongWaveFormStructuresEx2(ctypes.byref(num),ctypes.byref(self.pServerEventBuffer[0]),self.ServerDropped.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),self.MMFDropped.ctypes.data_as(ctypes.POINTER(ctypes.c_int)), self.PollHigh.ctypes.data_as(ctypes.POINTER(ctypes.c_int)), self.PollLow.ctypes.data_as(ctypes.POINTER(ctypes.c_int)))
        return self.pServerEventBuffer

    def getDataFromLongWave(self):
        resultServerEventBuffer = self.getLongWaveFormStructures()
        sorted_resultServerEventBuffer = sorted(resultServerEventBuffer,key = attrgetter('TimeStamp'), reverse = False)
        ts = 0 
        resMapChannel = {64:[], 65:[], 66:[], 67:[], 68:[], 69:[], 70:[], 71:[], 72:[], 73:[]}   
        
        for i in sorted_resultServerEventBuffer:
            if i.Type == 5:
                if i.Channel == 64:
                    # if i.TimeStamp > ts:
                    #     print("+"*30)
                    # print(i.TimeStamp, i.Channel, i.NumberOfDataWords)
                    assert i.TimeStamp >= ts, 'Not sorted'
                    ts = i.TimeStamp
                    wf = np.asarray(i.WaveForm)
                    resMapChannel[i.Channel] = np.append(resMapChannel[i.Channel], wf)
        return resMapChannel
        