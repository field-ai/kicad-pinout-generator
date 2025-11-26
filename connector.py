from dataclasses import dataclass
from typing import Generator

import os
import re
import wx
import yaml

import pcbnew


from . import pinout_generator_result

@dataclass
class Pin:
    number : str
    name : str

@dataclass
class Connection:
    pin : Pin
    net : str

@dataclass
class GenericPart:
    manufacturer: str
    part_no: str

@dataclass
class Connector:
    type: str
    terminal : GenericPart
    housing : GenericPart
    crimp : GenericPart
    connections : list[Connection]


def is_pad_electrical(pad : pcbnew.PAD) -> bool:
    return not re.match('MP[0-9]+$', pad.GetName())


def get_connections(footprint : pcbnew.FOOTPRINT) -> list[Connection]:
    return [
        Connection(Pin(pad.GetNumber(), pad.GetName()), pad.GetShortNetname())
        for pad in footprint.Pads() if is_pad_electrical(pad)
    ]

def is_connector(footprint : pcbnew.FOOTPRINT) -> bool:
    return re.match('J[0-9]+$', footprint.GetReference())

def get_fields(footprint : pcbnew.FOOTPRINT) -> dict:
    if hasattr(footprint, "GetProperties"):
        return footprint.GetProperties()
    elif hasattr(footprint, "GetFields"):
        return footprint.GetFieldsShownText()
    else:
        return {}

def wireviz_format(connectors : list[Connector]) -> str:

    def connector_to_dict(connector : Connector) -> dict:
        return {
            'type': connector.type,
            'pinlabels': [connection.net for connection in connector.connections],
            'manufacturer': connector.terminal.manufacturer,
            'mpn': connector.terminal.part_no,
            'image' : {'src': '<image.png>'},
            'additional_components': [{
                'type': 'Crimp',
                'subtype': connector.type + ', Crimp',
                'qty_multiplier': 'populated',
                'manufacturer': connector.housing.manufacturer,
                'mpn': connector.housing.part_no
            }]
        }

    return yaml.dump({
        f'X{i}': connector_to_dict(c) for i, c in enumerate(connectors, 1)
    })


def make_connector(footprint : pcbnew.FOOTPRINT) -> Connector:
    
    fields : dict = get_fields(footprint)

    return Connector(
        type=fields.get('Type', '<Type>'),
        terminal=GenericPart(
            fields.get('MFG', '<Manufacturer>'),
            fields.get('MPN', '<Part Number>')
        ),
        housing=GenericPart(
            fields.get('HOUSING_MFG', '<Manufacturer>'),
            fields.get('HOUSING_MPN', '<Part Number>')
        ),
        crimp=GenericPart(
            fields.get('CRIMP_MFG', '<Manufacturer>'),
            fields.get('CRIMP_MPN', '<Part Number>')
        ),
        connections=get_connections(footprint)
    )
