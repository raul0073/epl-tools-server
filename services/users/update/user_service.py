from typing import Optional, Dict, Any
from bson import ObjectId
from db.mongo_client import collection, fix_id
from models.user.prediction import RoundPredictions, SeasonPredictions
from models.user.points import Points
from models.user.register_models import UserRead


class UserUpdateService:
    @staticmethod
    async def update_user_full(
        user_id: str,
        full_user: Dict[str, Any]
    ) -> UserRead:
        """
        Fully replace the user document with `full_user`.
        """
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID")

        # Ensure predictions is always a dict
        if "predictions" not in full_user or not isinstance(full_user["predictions"], dict):
            full_user["predictions"] = {}

        # Replace the entire document
        result = await collection.replace_one(
            {"_id": ObjectId(user_id)},
            full_user
        )

        if result.matched_count == 0:
            raise ValueError("User not found or replace failed")

        # Fetch and return updated document
        updated_user = await collection.find_one({"_id": ObjectId(user_id)})
        if updated_user is None:
            raise ValueError("Cannot update user.")
        cleaned = fix_id(updated_user)
        return UserRead(**cleaned)

    @staticmethod
    async def update_user(
        user_id: str,
        updates: Dict[str, Any]
    ) -> UserRead:
        """
        Partially update user by ID.
        Supports arbitrary fields in `updates` dict.
        """
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID")

        result = await collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": updates},
            return_document=True
        )

        if result is None:
            raise ValueError("User not found or update failed")

        cleaned = fix_id(result)
        return UserRead(**cleaned)

    @staticmethod
    async def update_picture(user_id: str, picture_url: str) -> UserRead:
        """
        Update the user's avatar/picture URL.
        """
        return await UserUpdateService.update_user(user_id, {"picture": picture_url})

    @staticmethod
    async def update_predictions(
        user_id: str,
        predictions: Optional[Dict[int, RoundPredictions]] = None,
        season_predictions: Optional[SeasonPredictions] = None
    ) -> UserRead:
        """
        Update predictions and/or season predictions.
        """
        update_data: Dict[str, Any] = {}
        if predictions is not None:
            # Convert Pydantic objects to dicts for MongoDB
            update_data["predictions"] = {k: v.model_dump() for k, v in predictions.items()}

        if season_predictions is not None:
            update_data["season_predictions"] = season_predictions.model_dump()

        if not update_data:
            raise ValueError("No data provided to update")

        return await UserUpdateService.update_user(user_id, update_data)

    @staticmethod
    async def update_points(user_id: str, points: Points) -> UserRead:
        """
        Update the user's points structure.
        """
        return await UserUpdateService.update_user(user_id, {"points": points.model_dump()})

    @staticmethod
    async def add_prediction(user_id: str, round_number: int, prediction: dict) -> UserRead:
        """
        Append a prediction to a specific round.
        """
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID")

        result = await collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$push": {f"predictions.{round_number}.matches": prediction}},
            return_document=True
        )

        if result is None:
            raise ValueError("User not found or failed to add prediction")

        cleaned = fix_id(result)
        return UserRead(**cleaned)

    @staticmethod
    async def remove_prediction(user_id: str, round_number: int, game_id: str) -> UserRead:
        """
        Remove a prediction from a specific round by game_id.
        """
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID")

        result = await collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$pull": {f"predictions.{round_number}.matches": {"game_id": game_id}}},
            return_document=True
        )

        if result is None:
            raise ValueError("User not found or failed to remove prediction")

        cleaned = fix_id(result)
        return UserRead(**cleaned)
