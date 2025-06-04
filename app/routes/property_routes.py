from schemas.image_response import PropertyImageResponse, UnitImageResponse
from database.models.user_model import User
from database.models.image_model import PropertyImage, UnitImage
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from database.init import get_db
from services.property_service import PropertyService
from services.search_history_service import create_search_history
from schemas.search_history_schema import SearchHistoryCreate
from schemas.auth_schema import UserMinimumResponse
from schemas.property_response import ItemsResponse
from services.floor_service import FloorService
from services.unit_service import UnitService
from schemas.property_schema import PropertyCreate, FloorCreate, UnitCreate
from schemas.property_response import (
    PropertyResponse,
    PropertyListResponse,
    PropertyMinimumResponse,
    FloorMinimumResponse,
    UnitMinimumResponse,
    FloorResponse,
    FloorListResponse,
    UnitResponse,
    UnitListResponse,
)

from responses.error import (
    internal_server_error,
    conflict_error,
    forbidden_error,
    not_found_error,
)
from responses.success import data_response, empty_response
from utils.dependencies import get_current_user
from utils import generate_property_id
from utils.id_generator import generate_unit_id
import traceback
from services.email_service import EmailService
from services.property_recommendation_service import PropertyRecommendationSystem

router = APIRouter(prefix="/properties", tags=["Properties"])

property_service = PropertyService()
floor_service = FloorService()
unit_service = UnitService()
email_service = EmailService()
property_recommendation_system = PropertyRecommendationSystem()


# Initialize the recommendation system when the app starts
@router.on_event("startup")
async def initialize_recommendation_system():
    try:
        db = next(get_db())
        property_recommendation_system.train_model(db)
    except Exception as e:
        print(f"Error initializing recommendation system: {str(e)}")


@router.get("/train_model", response_model=PropertyResponse)
async def update_property_publish_status(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update the publish status of a property"""
    if not isinstance(current_user, User):
        return current_user
    try:
        property_recommendation_system.train_model(db)
        return data_response("Model trained successfully")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/recommendations", response_model=PropertyResponse)
async def get_property_recommendations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get property recommendations based on user search history"""
    if not isinstance(current_user, User):
        return current_user
    try:
        # Convert to dictionary
        property_data = {
            "id": 1,
            "name": "Updated Luxury Apartment",
            "city": "sargodha",
            "property_type": "BUILDING",
            "description": "Updated description for the luxury apartment",
            "monthly_rent": 600,
            "is_published": False,
        }

        # Get recommendations using the initialized system
        users_to_notify = property_recommendation_system.match_property_with_searches(
            property_data
        )
        return data_response(users_to_notify)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.patch("/{property_id}/publish", response_model=PropertyResponse)
async def update_property_publish_status(
    property_id: int,
    is_published: bool,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
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

        updated_property = property_service.update_property_publish_status(
            db, property_id, is_published
        )
        property_response = PropertyResponse.model_validate(updated_property)
        property_response.property_id = f"PROP-{updated_property.id:04d}"
        await email_service.send_update_action_email(
            current_user.email, "Property", property_id
        )
        return data_response(property_response.model_dump(mode="json"))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


# Property Routes


@router.get("/search-property", response_model=List[PropertyResponse])
async def search_properties(
    name: Optional[str] = None,
    city: Optional[str] = None,
    monthly_rent_gt: Optional[float] = None,
    monthly_rent_lt: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        user_id = (
            getattr(current_user, "id", None)
            if isinstance(current_user, User)
            else None
        )
        search_data = SearchHistoryCreate(
            query_name=name,
            query_city=city,
            monthly_rent_gt=float(monthly_rent_gt) if monthly_rent_gt else None,
            monthly_rent_lt=float(monthly_rent_lt) if monthly_rent_lt else None,
            user_id=user_id,
        )
        create_search_history(db, search_data)
        query = db.query(property_service.model)
        if name:
            query = query.filter(property_service.model.name.ilike(f"%{name}%"))
        if city:
            query = query.filter(property_service.model.city.ilike(f"%{city}%"))
        properties = query.offset(skip).limit(limit).all()
        property_responses = []
        for property in properties:
            match = True
            if monthly_rent_gt is not None and property.monthly_rent <= monthly_rent_gt:
                match = False
            if monthly_rent_lt is not None and property.monthly_rent >= monthly_rent_lt:
                match = False
            if match:
                prop_data = {
                    "id": property.id,
                    "property_id": f"PROP-{property.id:04d}",
                    "name": property.name,
                    "city": property.city,
                    "address": property.address,
                    "description": property.description,
                    "total_area": property.total_area,
                    "monthly_rent": property.monthly_rent,
                    "property_type": property.property_type,
                    "is_published": property.is_published,
                    "is_occupied": property.is_occupied,
                    "images": property.images,
                    "created_at": property.created_at,
                    "updated_at": property.updated_at,
                }
                property_responses.append(prop_data)
        return data_response(property_responses if property_responses else [])
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/search", response_model=List[PropertyResponse])
async def search_properties_and_units(
    name: Optional[str] = None,
    city: Optional[str] = None,
    monthly_rent_gt: Optional[float] = None,
    monthly_rent_lt: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Search for properties by name/city and filter units by monthly rent.
    Returns properties with units that match the rent criteria.
    """
    try:
        user_id = (
            getattr(current_user, "id", None)
            if isinstance(current_user, User)
            else None
        )
        search_data = SearchHistoryCreate(
            query_name=name,
            query_city=city,
            monthly_rent_gt=monthly_rent_gt,
            monthly_rent_lt=monthly_rent_lt,
            user_id=user_id,
        )
        create_search_history(db, search_data)
        query = db.query(property_service.model)
        if name:
            query = query.filter(property_service.model.name.ilike(f"%{name}%"))
        if city:
            query = query.filter(property_service.model.city.ilike(f"%{city}%"))
        properties = query.offset(skip).limit(limit).all()
        results = []
        for property in properties:
            floors = []
            for floor in property.floors:
                units = []
                for unit in floor.units:
                    match = True
                    if (
                        monthly_rent_gt is not None
                        and unit.monthly_rent <= monthly_rent_gt
                    ):
                        match = False
                    if (
                        monthly_rent_lt is not None
                        and unit.monthly_rent >= monthly_rent_lt
                    ):
                        match = False
                    if match:
                        unit_data = UnitMinimumResponse.model_validate(unit).model_dump(
                            mode="json"
                        )
                        # Add unit_id to response
                        unit_data["unit_id"] = generate_unit_id(unit.id)
                        units.append(unit_data)
                if units:
                    floor_data = {
                        "id": floor.id,
                        "number": floor.number,
                        "name": floor.name,
                        "units": units,
                    }
                    floors.append(floor_data)
            if floors:
                prop_data = {
                    "id": property.id,
                    "property_id": f"PROP-{property.id:04d}",
                    "name": property.name,
                    "city": property.city,
                    "address": property.address,
                    "property_type": str(property.property_type),
                    "floors": floors,
                }
                results.append(prop_data)
        if results:
            return data_response(results)
        return data_response([])
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.post("/", response_model=PropertyResponse)
async def create_property(
    property_in: PropertyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new property and notify matching search users"""
    if not isinstance(current_user, User):
        return current_user

    try:
        # Create the property
        property = property_service.create_property(db, current_user.id, property_in)
        property_response = PropertyResponse.model_validate(property)
        property_response.property_id = f"PROP-{property.id:04d}"

        await email_service.send_create_action_email(
            current_user.email, "Property", property.id
        )

        return data_response(property_response.model_dump(mode="json"))

    except IntegrityError:
        db.rollback()
        return conflict_error("Property with this name already exists")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/", response_model=List[PropertyListResponse])
async def get_properties(
    skip: int = 0,
    limit: int = 100,
    city: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all published properties"""

    try:
        properties = property_service.get_properties(
            db, skip, limit, city, is_published=True
        )

        property_responses = []
        for property in properties:
            property_data = {
                "id": property.id,
                "property_id": f"PROP-{property.id:04d}",
                "name": property.name,
                "city": property.city,
                "address": property.address,
                "property_type": str(property.property_type),
                "monthly_rent": property.monthly_rent,
                "is_published": property.is_published,
                "is_occupied": property.is_occupied,
                "created_at": property.created_at,
                "updated_at": property.updated_at,
                "meta": {
                    "total_floors": 0,
                    "total_units": 0,
                    "total_unoccupied_units": 0,
                },
                "floors": [],
                "owner": UserMinimumResponse.model_validate(property.owner),
            }
            total_floors = 0
            total_units = 0
            total_unoccupied_units = 0

            floors = floor_service.get_floors(db, property.id)
            if floors:
                property_data["floors"] = []
                total_floors = len(floors)

                for floor in floors:
                    floor_data = FloorMinimumResponse.model_validate(floor).model_dump(
                        mode="json"
                    )
                    units = unit_service.get_units_by_floor(db, floor.id)

                    if units:
                        floor_data["units"] = []
                        total_units += len(units)

                        for unit in units:
                            unit_data = UnitMinimumResponse.model_validate(
                                unit
                            ).model_dump(mode="json")
                            # Add unit_id to response
                            unit_data["unit_id"] = generate_unit_id(unit.id)
                            floor_data["units"].append(unit_data)

                            # Count unoccupied units
                            if not unit.is_occupied:
                                total_unoccupied_units += 1

                    property_data["floors"].append(floor_data)

            # Update meta data
            property_data["meta"]["total_floors"] = total_floors
            property_data["meta"]["total_units"] = total_units
            property_data["meta"]["total_unoccupied_units"] = total_unoccupied_units

        search_data = SearchHistoryCreate(
            query_city=city,
            monthly_rent_gt=monthly_rent_gt,
            monthly_rent_lt=monthly_rent_lt,
            user_id=user_id,
        )
        create_search_history(db, search_data)
        property_responses.append(property_data)
        return data_response(property_responses)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/me", response_model=PropertyListResponse)
async def get_my_properties(
    skip: int = 0,
    limit: int = 100,
    city: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get all properties owned by the current user"""
    if not isinstance(current_user, User):
        return current_user

    try:
        properties = property_service.get_properties(
            db, skip, limit, city, owner_id=current_user.id
        )

        property_responses = []
        for property in properties:
            property_data = {
                "id": property.id,
                "property_id": f"PROP-{property.id:04d}",
                "name": property.name,
                "city": property.city,
                "address": property.address,
                "property_type": str(property.property_type),
                "description": property.description,
                "total_area": property.total_area,
                "monthly_rent": property.monthly_rent,
                "is_published": property.is_published,
                "is_occupied": property.is_occupied,
                "created_at": property.created_at,
                "updated_at": property.updated_at,
                "thumbnail": None,
                "images": [],
                "meta": {
                    "total_floors": 0,
                    "total_units": 0,
                    "total_unoccupied_units": 0,
                },
                "floors": [],
                "owner": UserMinimumResponse.model_validate(property.owner),
            }
            total_floors = 0
            total_units = 0
            total_unoccupied_units = 0
            if property.images:
                for image in property.images:
                    if image.is_thumbnail:
                        property_data["thumbnail"] = (
                            PropertyImageResponse.model_validate(image).model_dump(
                                mode="json"
                            )
                        )
                    else:
                        property_data["images"].append(
                            PropertyImageResponse.model_validate(image).model_dump(
                                mode="json"
                            )
                        )
            floors = floor_service.get_floors(db, property.id)
            if floors:
                property_data["floors"] = []
                total_floors = len(floors)

                for floor in floors:
                    floor_data = FloorMinimumResponse.model_validate(floor).model_dump(
                        mode="json"
                    )
                    units = unit_service.get_units_by_floor(db, floor.id)

                    if units:
                        floor_data["units"] = []
                        total_units += len(units)

                        for unit in units:
                            unit_data = UnitMinimumResponse.model_validate(
                                unit
                            ).model_dump(mode="json")
                            # Add unit_id to response
                            unit_data["unit_id"] = generate_unit_id(unit.id)
                            floor_data["units"].append(unit_data)

                            # Count unoccupied units
                            if not unit.is_occupied:
                                total_unoccupied_units += 1

                    property_data["floors"].append(floor_data)

            # Update meta data
            property_data["meta"]["total_floors"] = total_floors
            property_data["meta"]["total_units"] = total_units
            property_data["meta"]["total_unoccupied_units"] = total_unoccupied_units

            property_responses.append(property_data)
        return data_response(property_responses)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(property_id: int, db: Session = Depends(get_db)):
    try:
        property = property_service.get_property(db, property_id)
        if not property:
            return not_found_error(f"No property found with id {property_id}")

        property_response = PropertyResponse.model_validate(property)

        property_response.property_id = f"PROP-{property.id:04d}"
        property_response.is_occupied = property_service.calculate_occupation_status(
            db, property
        )

        total_floors = 0
        total_units = 0
        total_unoccupied_units = 0

        floors = floor_service.get_floors(db, property.id)
        if floors:
            total_floors = len(floors)
            for floor in floors:
                units = unit_service.get_units_by_floor(db, floor.id)
                if units:
                    total_units += len(units)
                    # Count unoccupied units
                    for unit in units:
                        if not unit.is_occupied:
                            total_unoccupied_units += 1

        property_response.meta = {
            "total_floors": total_floors,
            "total_units": total_units,
            "total_unoccupied_units": total_unoccupied_units,
        }

        thumbnail = (
            db.query(PropertyImage)
            .filter(PropertyImage.property_id == property.id)
            .filter(PropertyImage.is_thumbnail == True)
            .first()
        )
        images = (
            db.query(PropertyImage)
            .filter(PropertyImage.property_id == property.id)
            .all()
        )
        if images:
            property_response.images = [
                PropertyImageResponse.model_validate(image) for image in images
            ]

        if thumbnail:
            property_response.thumbnail = PropertyImageResponse.model_validate(
                thumbnail
            )

        return data_response(property_response.model_dump(mode="json"))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: int,
    property_in: PropertyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        property = property_service.get_property(db, property_id)
        if not property:
            return not_found_error(f"No property found with id {property_id}")
        if property.owner_id != current_user.id:
            return forbidden_error("Not authorized to update this property")

        updated_property = property_service.update_property(
            db, property_id, property_in
        )
        property_response = PropertyResponse.model_validate(updated_property)
        property_response.property_id = f"PROP-{updated_property.id:04d}"
        await email_service.send_update_action_email(
            current_user.email, "Property", property_id
        )
        return data_response(property_response.model_dump(mode="json"))
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
    current_user=Depends(get_current_user),
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
            await email_service.send_delete_action_email(
                current_user.email, "Property", property_id
            )
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
    current_user=Depends(get_current_user),
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
        floor_response = FloorResponse.model_validate(floor)
        await email_service.send_create_action_email(
            current_user.email, "Floor", floor.id
        )
        return data_response(floor_response.model_dump(mode="json"))
    except ValueError as e:
        return conflict_error(str(e))
    except IntegrityError:
        db.rollback()
        return conflict_error("Floor with this number already exists")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/{property_id}/floors", response_model=List[FloorListResponse])
async def get_floors(
    property_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    try:
        floors = floor_service.get_floors(db, property_id, skip, limit)
        floor_responses = []

        for floor in floors:
            units = unit_service.get_units_by_floor(db, floor.id)
            unit_responses = [
                UnitMinimumResponse.model_validate(unit) for unit in units
            ]

            floor_data = {
                "id": floor.id,
                "number": floor.number,
                "name": floor.name,
                "description": floor.description,
                "area": floor.area,
                "created_at": floor.created_at,
                "updated_at": floor.updated_at,
                "total": len(unit_responses),
                "units": [u.model_dump(mode="json") for u in unit_responses],
            }
            floor_responses.append(floor_data)

        return data_response(floor_responses)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/{property_id}/floors/{floor_id}/units", response_model=UnitListResponse)
async def get_floor_units(
    floor_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    try:
        floor = floor_service.get_floor(db, floor_id)
        if not floor:
            return not_found_error("Floor not found")

        property = floor.property
        if not property:
            return not_found_error("Property not found")

        units = unit_service.get_units_by_floor(db, floor_id)
        unit_responses = []

        for unit in units:
            unit_data = UnitResponse.model_validate(unit)
            # Add unit_id to response
            unit_data.unit_id = generate_unit_id(unit.id)
            images = db.query(UnitImage).filter(UnitImage.unit_id == unit.id).all()
            if images:
                unit_data.images = [UnitImageResponse.model_validate(image) for image in images]
            unit_responses.append(unit_data)

        if not unit_responses:
            return data_response([])

        responses = []
        for unit_response in unit_responses:
            property_response = PropertyMinimumResponse.model_validate(property)
            if not property_response.property_id:
                property_response.property_id = generate_property_id(
                    property_response.id
                )
            floor_response = FloorMinimumResponse.model_validate(floor)
            unit = unit_response.model_dump(mode="json")
            # Ensure unit_id is included in the response
            unit["unit_id"] = generate_unit_id(unit_response.id)
            unit["floor"] = floor_response
            unit["property"] = property_response
            responses.append(unit)

        return data_response(responses)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))



@router.get("/properties-and-units/available", response_model=List[ItemsResponse])
async def get_available_properties_and_units(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get all available properties and units for booking.
    """
    if not isinstance(current_user, User):
        return current_user

    try:
        properties = property_service.get_properties(
            db, 
          is_occupied=False,
        )
        units = unit_service.get_all_available_units(
            db, 
        )
        items = []
        for property in properties:
            property_response = PropertyMinimumResponse.model_validate(property)
            if not property_response.property_id:
                property_response.property_id = generate_property_id(
                    property_response.id
                )
            items.append(
                  {
                    "item": property_response.model_dump(mode="json"),
                    "type": "property"
                }
            )
  
        items.extend(
            {
                "item": UnitMinimumResponse.model_validate(units).model_dump(mode="json"),
                "type": "unit"
            }
            for units in units
        )
        if not items:
            return data_response([])
        return data_response(items)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

@router.put("/{property_id}/floors/{floor_id}", response_model=FloorResponse)
async def update_floor(
    property_id: int,
    floor_id: int,
    floor_in: FloorCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
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
        floor_response = FloorResponse.model_validate(updated_floor)
        await email_service.send_update_action_email(
            current_user.email, "Floor", floor_id
        )
        return data_response(floor_response.model_dump(mode="json"))
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
    current_user: dict = Depends(get_current_user),
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
            await email_service.send_delete_action_email(
                current_user.email, "Floor", floor_id
            )
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
    current_user: dict = Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        floor = floor_service.get_floor(db, floor_id)
        if not floor:
            return not_found_error(f"No floor found with id {floor_id}")
        if floor.property.owner_id != current_user.id:
            return forbidden_error("Not authorized to create unit")

        unit = unit_service.create_unit(db, floor_id, property_id, unit_in)
        unit_response = UnitResponse.model_validate(unit)
        # Add unit_id to response
        unit_response.unit_id = generate_unit_id(unit.id)

        await email_service.send_create_action_email(
            current_user.email, "Unit", unit.id
        )
        return data_response(unit_response.model_dump(mode="json"))
    except IntegrityError:
        db.rollback()
        return conflict_error("Unit with this name already exists")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/{property_id}/floors/{floor_id}/units", response_model=List[UnitResponse])
async def get_unit(
    property_id: int,
    floor_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    try:
        units = unit_service.get_units_by_floor(db, floor_id, skip, limit)
        unit_responses = []

        for unit in units:
            unit_data = UnitResponse.model_validate(unit)
            # Add unit_id to response
            unit_data.unit_id = generate_unit_id(unit.id)
            
            images = db.query(UnitImage).filter(UnitImage.unit_id == unit.id).all()
            if images:
                unit_data.images = [UnitImageResponse.model_validate(image) for image in images]
            unit_responses.append(unit_data)

        return data_response([u.model_dump(mode="json") for u in unit_responses])
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get(
    "/{property_id}/floors/{floor_id}/available_units",
    response_model=List[UnitResponse],
)
async def get_available_units(
    property_id: int,
    floor_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    try:
        floor = floor_service.get_floor(db, floor_id)
        if not floor:
            return not_found_error("Floor not found")

        property = floor.property
        if not property:
            return not_found_error("Property not found")

        my_units = unit_service.get_available_units(db, floor_id, skip, limit)
        responses = []

        for unit in my_units:
            unit_data = UnitResponse.model_validate(unit)
            unit_data.unit_id = generate_unit_id(unit.id)

            # Add images if any
            images = db.query(UnitImage).filter(UnitImage.unit_id == unit.id).all()
            if images:
                unit_data.images = [
                    UnitImageResponse.model_validate(image) for image in images
                ]

            # Add property and floor information
            property_response = PropertyMinimumResponse.model_validate(property)
            if not property_response.property_id:
                property_response.property_id = generate_property_id(
                    property_response.id
                )
            floor_response = FloorMinimumResponse.model_validate(floor)

            response_data = unit_data.model_dump(mode="json")
            response_data["floor"] = floor_response.model_dump(mode="json")
            response_data["property"] = property_response.model_dump(mode="json")

            responses.append(response_data)

        return data_response(responses)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.put(
    "/{property_id}/floors/{floor_id}/units/{unit_id}", response_model=UnitResponse
)
async def update_unit(
    property_id: int,
    floor_id: int,
    unit_id: int,
    unit_in: UnitCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
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
        await email_service.send_update_action_email(
            current_user.email, "Unit", unit_id
        )
        return data_response(unit_response.model_dump(mode="json"))
    except IntegrityError:
        db.rollback()
        return conflict_error("Unit with this name already exists")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.delete(
    "/{property_id}/floors/{floor_id}/units/{unit_id}", response_model=UnitResponse
)
async def delete_unit(
    property_id: int,
    floor_id: int,
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
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
            await email_service.send_delete_action_email(
                current_user.email, "Unit", unit_id
            )
            return empty_response()
        return internal_server_error("Failed to delete unit")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))
