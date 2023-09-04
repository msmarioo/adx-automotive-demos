from asammdf import MDF
import csv
import gzip
import os
import time 
import multiprocessing as mp
from DecodeUtils import getSource, extractSignalsByType

def processSignalAsCsv(counter, filename, signalMetadata, uuid, targetdir, blacklistedSignals):

    start_signal_time = time.time()
    print(f"pid {os.getpid()}: Launched task signal {counter}: {signalMetadata['name']}")

    if signalMetadata["name"] in blacklistedSignals:
        return (f"pid {os.getpid()}", False, counter, f">>> Skipped: {signalMetadata}")

    # Get the signal group and channel index to load that specific signal ONLY
    group_index = signalMetadata["group_index"]
    channel_index = signalMetadata["channel_index"]

    # Open the MDF file and select a single signal
    mdf = MDF(filename)          
    # We select a specific signal, both decoded and raw
    decodedSignal = mdf.select(channels=[(None, group_index, channel_index)])[0]
    rawSignal = mdf.select(channels=[(None, group_index, channel_index)], raw=True)[0]
    
    print(f"pid {os.getpid()}: Processing signal {counter}: {decodedSignal.name} group index {group_index} channel index {channel_index} with type {decodedSignal.samples.dtype}")   


    targetfile = os.path.join(targetdir, f"{uuid}-{counter}.csv.gz")
    os.makedirs(os.path.dirname(targetfile), exist_ok=True)

    # open the file in the write mode
    with gzip.open(targetfile, 'wt') as csvFile:

        source_name, source_type, bus_type, channel_group_acq_name, acq_source_name, acq_source_path = getSource(mdf, decodedSignal)
        numericSignals, stringSignals = extractSignalsByType(decodedSignal, rawSignal)

        writer = csv.writer(csvFile)
        writer.writerow(["source_uuid", "name", "unit", "timestamp", "value", "value_string", "value_raw", "source", "channel_group_acq_name", "acq_source_name", "acq_source_path", "source_type", "bus_type"])                
                        
        # Iterate on the entries for the signal
        for indx in range(0, len(decodedSignal.timestamps)):

            writer.writerow(
                [
                    str(uuid),
                    decodedSignal.name, 
                    decodedSignal.unit, 
                    decodedSignal.timestamps[indx],
                    numericSignals[indx],
                    stringSignals[indx],
                    rawSignal[indx],
                    source_name,
                    channel_group_acq_name,
                    acq_source_name,
                    acq_source_path,                    
                    source_type,
                    bus_type,
                ]
            )

    csvFile.close()
    
    end_signal_time = time.time() - start_signal_time
    mdf.close()
    
    return (f"Signal {counter}: {decodedSignal.name} with {len(decodedSignal.timestamps)} entries took {end_signal_time}")