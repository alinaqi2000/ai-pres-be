import secrets
from typing import Optional
from pydantic import BaseModel
from schemas.image_schema import (
    PropertyImageCreate,
    PropertyImage,
    UnitImageCreate,
    UnitImage,
)
from database.models import User
from sqlalchemy.orm import Session
from database.models import (
    PropertyImage as PropertyImageModel,
    UnitImage as UnitImageModel,
)
from database.models import Property, Unit
from services.base_service import BaseService
from fastapi import UploadFile
import os
from config import UPLOAD_DIR
import mimetypes


class ImageService:
    def __init__(self):
        self.property_image_service = BaseService(PropertyImageModel)
        self.unit_image_service = BaseService(UnitImageModel)

    async def save_uploaded_file(
        self, file: UploadFile, prefix: str, entity_id: int
    ) -> str:
        """
        Save an uploaded file to the uploads directory

        Args:
            file: The uploaded file
            prefix: Prefix for the file name (e.g., "property_", "unit_")
            entity_id: ID of the entity (property or unit)

        Returns:
            The full path to the saved file

        Raises:
            ValueError: If the file is not an image
        """
        # Create uploads directory if it doesn't exist
        os.makedirs(UPLOAD_DIR + "/" + str(entity_id), exist_ok=True)

        # Get file extension and MIME type
        _, ext = os.path.splitext(file.filename)
        mime_type = mimetypes.guess_type(file.filename)[0]

        # Validate that it's an image file
        if not mime_type or not mime_type.startswith("image/"):
            raise ValueError("Only image files are allowed")

        # Generate file path
        file_path = os.path.join(UPLOAD_DIR + "/" + str(entity_id), f"{prefix}{ext}")

        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return file_path

    async def create_property_thumbnail(
        self, db: Session, property_id: int, file: UploadFile, current_user: User
    ) -> Optional[PropertyImage]:
        """
        Create a property thumbnail image

        Args:
            db: Database session
            property_id: ID of the property
            file: The uploaded thumbnail file
            current_user: Current authenticated user

        Returns:
            The created PropertyImage object
        """

        try:
            # Get property
            property = db.query(Property).filter(Property.id == property_id).first()
            if not property:
                raise Exception(f"Property with ID {property_id} not found")

            # Check ownership
            if property.owner_id != current_user.id:
                raise Exception(
                    "You are not authorized to upload images for this property"
                )

            # Check if thumbnail already exists and delete it
            existing_thumbnail = (
                db.query(PropertyImageModel)
                .filter(
                    PropertyImageModel.property_id == property_id,
                    PropertyImageModel.is_thumbnail == True,
                )
                .first()
            )

            # Save the file
            file_path = await self.save_uploaded_file(file, "thumbnail", property_id)
            # Create thumbnail
            thumbnail = PropertyImageCreate(
                property_id=property_id,
                image_path=str(file_path),  # Convert to string explicitly
                is_thumbnail=True,
            )

            new_thumbnail = self.property_image_service.create(db, thumbnail)

            if existing_thumbnail:
                # Delete the existing thumbnail file from disk
                if os.path.exists(existing_thumbnail.image_path):
                    os.remove(existing_thumbnail.image_path)
                # Delete the existing thumbnail from database
                db.delete(existing_thumbnail)
                db.commit()

            return new_thumbnail
        except Exception as e:
            db.rollback()
            raise e

    async def create_property_image(
        self, db: Session, property_id: int, file: UploadFile, current_user: User
    ) -> Optional[PropertyImage]:
        """
        Create a property image

        Args:
            db: Database session
            property_id: ID of the property
            file: The uploaded image file
            current_user: Current authenticated user

        Returns:
            The created PropertyImage object
        """
        try:
            # Get property
            property = db.query(Property).filter(Property.id == property_id).first()
            if not property:
                raise Exception(f"Property with ID {property_id} not found")

            # Check ownership
            if property.owner_id != current_user.id:
                raise Exception(
                    "You are not authorized to upload images for this property"
                )

            # Check image count
            image_count = (
                db.query(PropertyImageModel)
                .filter(
                    PropertyImageModel.property_id == property_id,
                    PropertyImageModel.is_thumbnail
                    == False,  # Exclude thumbnails from count
                )
                .count()
            )

            if image_count >= 3:
                raise Exception(
                    "Maximum number of images (3) reached for this property"
                )

            # Save the file
            random_name = f"image_{secrets.token_hex(8)}"
            file_path = await self.save_uploaded_file(
                file, random_name, property_id
            )

            # Create image
            image = PropertyImageCreate(
                property_id=property_id, image_path=str(file_path)
            )
            return self.property_image_service.create(db, image)
        except Exception as e:
            db.rollback()
            raise e

    async def create_unit_image(
        self, db: Session, unit_id: int, file: UploadFile, current_user: User
    ) -> Optional[UnitImage]:
        """
        Create a unit image

        Args:
            db: Database session
            unit_id: ID of the unit
            file: The uploaded image file
            current_user: Current authenticated user

        Returns:
            The created UnitImage object
        """
        try:
            # Get unit
            unit = db.query(Unit).filter(Unit.id == unit_id).first()
            if not unit:
                raise Exception(f"Unit with ID {unit_id} not found")

            # Check ownership through property
            property = (
                db.query(Property).filter(Property.id == unit.property_id).first()
            )
            if not property or property.owner_id != current_user.id:
                raise Exception("You are not authorized to upload images for this unit")

            # Check image count
            image_count = (
                db.query(UnitImageModel)
                .filter(UnitImageModel.unit_id == unit_id)
                .count()
            )

            if image_count >= 3:
                raise Exception("Maximum number of images (3) reached for this unit")

            # Save the file
            random_name = f"unit_{unit_id}_image_{secrets.token_hex(8)}"
            file_path = await self.save_uploaded_file(
                file, random_name, unit.property_id
            )

            # Create image
            image = UnitImageCreate(unit_id=unit_id, image_path=str(file_path))
            return self.unit_image_service.create(db, image)
        except Exception as e:
            db.rollback()
            raise e

    async def delete_property_image(
        self, db: Session, image_id: int, current_user: User
    ) -> None:
        """
        Delete a property image

        Args:
            db: Database session
            image_id: ID of the image to delete
            current_user: Current authenticated user
        """
        try:
            # Get image
            image = (
                db.query(PropertyImageModel)
                .filter(PropertyImageModel.id == image_id)
                .first()
            )
            if not image:
                raise Exception(f"Image with ID {image_id} not found")

            # Check ownership
            property = (
                db.query(Property).filter(Property.id == image.property_id).first()
            )
            if not property or property.owner_id != current_user.id:
                raise Exception("You are not authorized to delete this image")

            # Check if it's a thumbnail (thumbnails cannot be deleted)
            if image.is_thumbnail:
                raise Exception("Thumbnail images cannot be deleted")

            # Delete the file from disk
            if os.path.exists(image.image_path):
                os.remove(image.image_path)

            # Delete from database
            db.delete(image)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

    async def delete_unit_image(
        self, db: Session, image_id: int, current_user: User
    ) -> None:
        """
        Delete a unit image

        Args:
            db: Database session
            image_id: ID of the image to delete
            current_user: Current authenticated user
        """
        try:
            # Get image
            image = (
                db.query(UnitImageModel).filter(UnitImageModel.id == image_id).first()
            )
            if not image:
                raise Exception(f"Image with ID {image_id} not found")

            # Check ownership through property
            unit = db.query(Unit).filter(Unit.id == image.unit_id).first()
            if not unit:
                raise Exception(f"Unit with ID {image.unit_id} not found")

            property = (
                db.query(Property).filter(Property.id == unit.property_id).first()
            )
            if not property or property.owner_id != current_user.id:
                raise Exception("You are not authorized to delete this image")

            # Delete the file from disk
            if os.path.exists(image.image_path):
                os.remove(image.image_path)

            # Delete from database
            db.delete(image)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        except Exception as e:
            db.rollback()
            raise e
