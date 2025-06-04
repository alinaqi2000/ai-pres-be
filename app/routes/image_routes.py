from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from database.init import get_db
from services.image_service import ImageService
from responses.error import internal_server_error
from responses.success import data_response, empty_response
from utils.dependencies import get_current_user
from database.models.user_model import User
from schemas.image_response import PropertyImageResponse, UnitImageResponse

router = APIRouter(prefix="/images", tags=["Images"])

image_service = ImageService()


@router.post("/property/{property_id}/thumbnail", response_model=PropertyImageResponse)
async def upload_property_thumbnail(
    property_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        result = await image_service.create_property_thumbnail(
            db, property_id, file, current_user
        )
        image_response = PropertyImageResponse.from_orm(result)
        return data_response(image_response.model_dump(mode="json"))
    except Exception as e:
        return internal_server_error(str(e))


@router.post("/property/{property_id}/image", response_model=PropertyImageResponse)
async def upload_property_image(
    property_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        result = await image_service.create_property_image(
            db, property_id, file, current_user
        )
        image_response = PropertyImageResponse.from_orm(result)
        return data_response(image_response.model_dump(mode="json"))
    except Exception as e:
        return internal_server_error(str(e))


@router.post("/unit/{unit_id}/image", response_model=UnitImageResponse)
async def upload_unit_image(
    unit_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        result = await image_service.create_unit_image(db, unit_id, file, current_user)
        image_response = UnitImageResponse.from_orm(result)
        return data_response(image_response.model_dump(mode="json"))
    except Exception as e:
        return internal_server_error(str(e))


@router.delete("/property/image/{image_id}")
async def delete_property_image(
    image_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """
    Delete a property image

    Args:
        image_id: ID of the image to delete
    """
    if not isinstance(current_user, User):
        return current_user
    try:
        await image_service.delete_property_image(db, image_id, current_user)
        return empty_response()
    except Exception as e:
        return internal_server_error(str(e))


@router.delete("/unit/image/{image_id}")
async def delete_unit_image(
    image_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """
    Delete a unit image

    Args:
        image_id: ID of the image to delete
    """
    if not isinstance(current_user, User):
        return current_user
    try:
        await image_service.delete_unit_image(db, image_id, current_user)
        return empty_response()
    except Exception as e:
        return internal_server_error(str(e))
