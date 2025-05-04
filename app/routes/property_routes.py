from database.models.user_model import User
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from database.init import get_db
from services.property_service import PropertyService
from services.floor_service import FloorService
from services.unit_service import UnitService
from schemas.property_schema import PropertyCreate, Property, FloorCreate, Floor, UnitCreate, Unit
from schemas.property_response import PropertyResponse, PropertyListResponse, FloorResponse, UnitResponse
from responses.error import internal_server_error, conflict_error, forbidden_error
from responses.success import data_response, empty_response
from utils.dependencies import get_current_user
import traceback

router = APIRouter(prefix="/properties", tags=["Properties"])

property_service = PropertyService()
floor_service = FloorService()
unit_service = UnitService()

# Property Routes

@router.patch("/{property_id}/publish", response_model=PropertyResponse)
async def update_property_publish_status(
    property_id: int,
    is_published: bool,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update the publish status of a property"""
    if not isinstance(current_user, User):
        return current_user
    
    try:
        property = property_service.get_property(db, property_id)
        if not property:
            return not_found_error(f"No property found with id {property_id}")
        if property.owner_id != current_user.id:
            return forbidden_error("Not authorized to update this property")
            
        updated_property = property_service.update_property_publish_status(db, property_id, is_published)
        property_response = PropertyResponse.from_orm(updated_property)
        return data_response(property_response.model_dump(mode='json'))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

# Property Routes
@router.post("/", response_model=PropertyResponse)
async def create_property(
    property_in: PropertyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not isinstance(current_user, User):
        return current_user
    
    try:
        property = property_service.create_property(db, current_user.id, property_in)
        property_response = PropertyResponse.from_orm(property)
        return data_response(property_response.model_dump(mode='json'))
    except IntegrityError:
        db.rollback()
        return conflict_error("Property with this name already exists")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

@router.get("/", response_model=PropertyListResponse)
async def get_properties(
    skip: int = 0,
    limit: int = 100,
    city: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all published properties"""
    try:
        properties = property_service.get_properties(db, skip, limit, city, is_published=True)
        property_responses = []
        for property in properties:
            property_data = PropertyResponse.from_orm(property)
            property_data.floors = [FloorResponse.from_orm(floor) for floor in property_data.floors]
            property_responses.append(property_data)
        return data_response([p.model_dump(mode='json') for p in property_responses])
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

@router.get("/me", response_model=PropertyListResponse)
async def get_my_properties(
    skip: int = 0,
    limit: int = 100,
    city: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all properties owned by the current user"""
    if not isinstance(current_user, User):
        return current_user
    
    try:
        properties = property_service.get_properties(db, skip, limit, city, owner_id=current_user.id)
        property_responses = []
        for property in properties:
            property_data = PropertyResponse.from_orm(property)
            property_data.floors = [FloorResponse.from_orm(floor) for floor in property_data.floors]
            property_responses.append(property_data)
        return data_response([p.model_dump(mode='json') for p in property_responses])
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: int,
    db: Session = Depends(get_db)
):
    try:
        property = property_service.get_property(db, property_id)
        if not property:
            return not_found_error(f"No property found with id {property_id}")
        property_response = PropertyResponse.from_orm(property)
        return data_response(property_response.model_dump(mode='json'))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: int,
    property_in: PropertyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not isinstance(current_user, User):
        return current_user
    
    try:
        property = property_service.get_property(db, property_id)
        if not property:
            return not_found_error(f"No property found with id {property_id}")
        if property.owner_id != current_user.id:
            return forbidden_error("Not authorized to update this property")
            
        updated_property = property_service.update_property(db, property_id, property_in)
        property_response = PropertyResponse.from_orm(updated_property)
        return data_response(property_response.model_dump(mode='json'))
    except IntegrityError:
        db.rollback()
        return conflict_error("Property with this name already exists")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

@router.delete("/{property_id}", response_model=PropertyResponse)
async def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not isinstance(current_user, User):
        return current_user
    
    try:
        property = property_service.get_property(db, property_id)
        if not property:
            return not_found_error(f"No property found with id {property_id}")
        if property.owner_id != current_user.id:
            return forbidden_error("Not authorized to delete this property")
            
        if property_service.delete_property(db, property_id):
            return empty_response()
        return internal_server_error("Failed to delete property")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

# Floor Routes
@router.post("/{property_id}/floors", response_model=FloorResponse)
async def create_floor(
    property_id: int,
    floor_in: FloorCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not isinstance(current_user, User):
        return current_user
    
    try:
        property = property_service.get_property(db, property_id)
        if not property:
            return not_found_error(f"No property found with id {property_id}")
        if property.owner_id != current_user.id:
            return forbidden_error("Not authorized to create floor")

        floor = floor_service.create_floor(db, property_id, floor_in)
        floor_response = FloorResponse.from_orm(floor)
        return data_response(floor_response.model_dump(mode='json'))
    except ValueError as e:
        return conflict_error(str(e))
    except IntegrityError:
        db.rollback()
        return conflict_error("Floor with this number already exists")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

@router.get("/{property_id}/floors", response_model=List[FloorResponse])
async def get_floors(
    property_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    try:
        floors = floor_service.get_floors(db, property_id, skip, limit)
        response_data = [FloorResponse.from_orm(f).model_dump(mode='json') for f in floors]
        return data_response(response_data)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

@router.put("/{property_id}/floors/{floor_id}", response_model=FloorResponse)
async def update_floor(
    property_id: int,
    floor_id: int,
    floor_in: FloorCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not isinstance(current_user, User):
        return current_user
    
    try:
        floor = floor_service.get_floor(db, floor_id)
        if not floor:
            return not_found_error(f"No floor found with id {floor_id}")
        if floor.property.owner_id != current_user.id:
            return forbidden_error("Not authorized to update this floor")
            
        updated_floor = floor_service.update_floor(db, floor_id, floor_in)
        floor_response = FloorResponse.from_orm(updated_floor)
        return data_response(floor_response.model_dump(mode='json'))   
    except IntegrityError:
        db.rollback()
        return conflict_error("Floor with this number already exists")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

@router.delete("/{property_id}/floors/{floor_id}", response_model=FloorResponse)
async def delete_floor(
    property_id: int,
    floor_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not isinstance(current_user, User):
        return current_user
    
    try:
        floor = floor_service.get_floor(db, floor_id)
        if not floor:
            return not_found_error(f"No floor found with id {floor_id}")
        if floor.property.owner_id != current_user.id:
            return forbidden_error("Not authorized to delete this floor")
            
        if floor_service.delete_floor(db, floor_id):
            return empty_response()
        return internal_server_error("Failed to delete floor")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

# Unit Routes
@router.post("/{property_id}/floors/{floor_id}/units", response_model=UnitResponse)
async def create_unit(
    property_id: int,
    floor_id: int,
    unit_in: UnitCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not isinstance(current_user, User):
        return current_user
    
    try:
        floor = floor_service.get_floor(db, floor_id)
        if not floor:
            return not_found_error(f"No floor found with id {floor_id}")
        if floor.property.owner_id != current_user.id:
            return forbidden_error("Not authorized to create unit")
            
        unit = unit_service.create_unit(db, floor_id, unit_in)
        unit_response = UnitResponse.from_orm(unit)
        return data_response(unit_response.model_dump(mode='json'))
    except IntegrityError:
        db.rollback()
        return conflict_error("Unit with this name already exists")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

@router.get("/{property_id}/floors/{floor_id}/units", response_model=List[UnitResponse])
async def get_units(
    property_id: int,
    floor_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    try:
        units = unit_service.get_units(db, floor_id, skip, limit)
        unit_responses = [UnitResponse.from_orm(unit).model_dump(mode='json') for unit in units]
        return data_response(unit_responses)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

@router.put("/{property_id}/floors/{floor_id}/units/{unit_id}", response_model=UnitResponse)
async def update_unit(
    property_id: int,
    floor_id: int,
    unit_id: int,
    unit_in: UnitCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not isinstance(current_user, User):
        return current_user
    
    try:
        unit = unit_service.get_unit(db, unit_id)
        if not unit:
            return not_found_error(f"No unit found with id {unit_id}")
        if unit.floor.property.owner_id != current_user.id:
            return forbidden_error("Not authorized to update this unit")
            
        updated_unit = unit_service.update_unit(db, unit_id, unit_in)
        unit_response = UnitResponse.from_orm(updated_unit)
        return data_response(unit_response.model_dump(mode='json'))
    except IntegrityError:
        db.rollback()
        return conflict_error("Unit with this name already exists")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

@router.delete("/{property_id}/floors/{floor_id}/units/{unit_id}", response_model=UnitResponse)
async def delete_unit(
    property_id: int,
    floor_id: int,
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not isinstance(current_user, User):
        return current_user
    
    try:
        unit = unit_service.get_unit(db, unit_id)
        if not unit:
            return not_found_error(f"No unit found with id {unit_id}")
        if unit.floor.property.owner_id != current_user.id:
            return forbidden_error("Not authorized to delete this unit")
            
        if unit_service.delete_unit(db, unit_id):
            return empty_response()
        return internal_server_error("Failed to delete unit")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))
