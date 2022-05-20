from dataclasses import dataclass
from typing import List, Any


@dataclass
class Address:
    sub_administrative_area: str
    label: str
    street_address: int
    country_code: str
    state_code: None
    administrative_area: str
    street_name: str
    formatted_address_lines: List[str]
    map_item_full_address: str
    full_throroughfare: str
    area_of_interest: List[Any]
    locality: str
    country: str


@dataclass
class Location:
    position_type: str
    vertical_accuracy: int
    longitude: float
    floor_level: int
    is_inaccurate: bool
    is_old: bool
    horizontal_accuracy: float
    latitude: float
    time_stamp: int
    altitude: int
    location_finished: bool


@dataclass
class ProductInformation:
    manufacturer_name: str
    model_name: str
    product_identifier: int
    vendor_identifier: int
    antenna_power: int


@dataclass
class ProductType:
    type: str
    product_information: ProductInformation


@dataclass
class Role:
    name: str
    emoji: str
    identifier: int


@dataclass
class Item:
    part_info: None
    safe_locations: List[Any]
    product_type: ProductType
    is_firmware_update_mandatory: bool
    owner: str
    battery_status: int
    serial_number: str
    lost_mode_metadata: None
    capabilities: int
    identifier: str
    address: Address
    location: Location
    system_version: str
    crowd_sourced_location: Location
    role: Role
    group_identifier: None
    name: str
