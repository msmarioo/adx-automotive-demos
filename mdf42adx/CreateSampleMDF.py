# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import argparse
import asammdf
from asammdf import Source
import numpy as np
from asammdf.blocks import v4_constants as v4c
import numpy as np

def processFile(filename):
    ''' 
        Creates a sample MDF file that contains simulated values for Engine RPM, Vehicle Speed and Engine Power.
        The generated file will have 10,000 signals at about 100 miliseconds.

        Some of the channels are based on the asammdf documentation
    '''

    # How many samples we will generate
    numberOfValues = 10000

    # Create an empty MDF file
    mdf = asammdf.MDF()

    # Generate time array
    time = np.linspace(0, 100, numberOfValues)

    signals = []

    source = Source(source_type=Source.SOURCE_TOOL, bus_type=Source.BUS_TYPE_NONE, name="EngineControlUnit", path="PT_CAN.Powertrain", comment="Generated" )

    # Generate vehicle RPM signal
    rpm_amplitude = 500
    rpm_frequency = 10
    rpm_phase = np.pi/4
    vehicle_RPM = 3000 + rpm_amplitude * np.sin(2 * np.pi * rpm_frequency * time + rpm_phase) + np.random.normal(0, 50, size=numberOfValues)
    signals.append(asammdf.Signal(name="EngineRPM", samples=vehicle_RPM, timestamps=time, unit="RPM", source=source))

    # Generate vehicle speed signal
    speed_amplitude = 10
    speed_frequency = 10
    speed_phase = np.pi/6
    vehicle_speed = 60 + speed_amplitude * np.sin(2 * np.pi * speed_frequency * time + speed_phase) + np.random.normal(0, 2, size=numberOfValues)
    signals.append(asammdf.Signal(name="Speed", samples=vehicle_speed, timestamps=time, unit="km/h", source=source))

    # Generate engine power signal
    engine_power = vehicle_RPM * vehicle_speed / 1000 + np.random.normal(0, 50, size=numberOfValues)
    signals.append(asammdf.Signal(name="EnginePower", samples=engine_power, timestamps=time, unit="kW", source=source))

    # Generate gear signal
    gear = np.zeros(numberOfValues)
    for i in range(numberOfValues):
        if vehicle_speed[i] < 20:
            gear[i] = 1
        elif vehicle_speed[i] < 40:
            gear[i] = 2
        elif vehicle_speed[i] < 60:
            gear[i] = 3
        else:
            gear[i] = 4
    signals.append(asammdf.Signal(name="Gear", samples=gear, timestamps=time, unit="-", source=source))

    # Generate a random uint64 signal and add it to the mdf file
    random_signal = np.random.randint(0, 2**64, size=numberOfValues, dtype=np.uint64)
    signals.append(asammdf.Signal(name="Random", samples=random_signal, timestamps=time, unit="-", source=source))

    # String channel
    stringSignal = [
        'String {}'.format(i).encode('utf-8')
        for i in range(numberOfValues)
    ]
    signals.append(asammdf.Signal(name='Channel_string', samples=stringSignal, timestamps=time, unit="", source=source, encoding='utf-8'))



    # value range to text    
    vals = 20
    conversion = {
        'lower_{}'.format(i): i * 10
        for i in range(vals)
    }
    conversion.update(
        {
            'upper_{}'.format(i): (i + 1) * 10
            for i in range(vals)
        }
    )
    conversion.update(
        {
            'text_{}'.format(i): 'Level {}'.format(i)
            for i in range(vals)
        }
    )
    conversion['default'] = b'Unknown level'
    sig = asammdf.Signal(
        6 * np.arange(numberOfValues, dtype=np.uint64) % 240,
        name='Channel_value_range_to_text',
        timestamps=time,
        conversion=conversion,
        comment='Value range to text channel',
    )
    signals.append(sig)

    mdf.append(signals, common_timebase=True)

    mdf.save(args.file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generates a sample MDF file for testing")
    parser.add_argument("-f", "--file", dest="file", help="File to generate")

    args = parser.parse_args()

    if(args.file):
        processFile(args.file)
