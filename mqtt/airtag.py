from dataclasses import dataclass
from typing import Optional, List, Any

@dataclass
class Address:
    label: str = None
    streetAddress: Optional[str] = None
    stateCode: Optional[str] = None
    countryCode: Optional[str] = None
    administrativeArea: Optional[str] = None
    streetName: Optional[str] = None
    formattedAddressLines: Optional[List[str]] = None
    mapItemFullAddress: Optional[str] = None
    fullThroroughfare: Optional[str] = None
    locality: Optional[str] = None
    country: Optional[str] = None
    # areaOfInterest: List[Any]


@dataclass
class Location:
    positionType: Optional[str] = None
    verticalAccuracy: Optional[int] = None
    longitude: Optional[float] = None
    floorLevel: Optional[int] = None
    isInaccurate: Optional[bool] = None
    isOld: Optional[bool] = None
    horizontalAccuracy: Optional[float] = None
    latitude: Optional[float] = None
    timeStamp: Optional[int] = None
    altitude: Optional[int] = None
    locationFinished: Optional[bool] = None


@dataclass
class ProductInformation:
    manufacturerName: Optional[str] = None
    modelName: Optional[str] = None
    productIdentifier: Optional[int] = None
    vendorIdentifier: Optional[int] = None
    antennaPower: Optional[int] = None


@dataclass
class ProductType:
    type: Optional[str] = None
    productInformation: Optional[ProductInformation] = None


@dataclass
class Role:
    name: str = None
    emoji: str = None
    identifier: int = None


@dataclass
class Item:
    name: str
    role: Role
    productType: Optional[ProductType] = None
    owner: Optional[str] = None
    batteryStatus: Optional[int] = None
    serialNumber: Optional[str] = None
    capabilities: Optional[int] = None
    identifier: Optional[str] = None
    address: Optional[Address] = None
    location: Optional[Location] = None
    systemVersion: Optional[str] = None
    crowdSourcedLocation: Optional[Location] = None

