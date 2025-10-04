from typing import List, Optional
from bson import ObjectId
from db.mongo_client import collection, fix_id
from models.user.prediction import RoundPredictions, SeasonPredictions
from models.user.points import Points, SeasonPoints
from models.user.register_models import UserCreate, UserRead


class UserService:
    @staticmethod
    async def create_user(user: UserCreate) -> UserRead:
        """
        Create a new user if they don't exist.
        If user exists, return the existing user.
        Initializes predictions, season predictions, and points if not provided.
        """
        # Check if user already exists
        existing = await collection.find_one({"email": user.email})
        if existing:
            cleaned_existing = fix_id(existing)
            return UserRead(**cleaned_existing)

        # Initialize missing fields
        if user.predictions is None:
            user.predictions = {}

        if user.season_predictions is None:
            user.season_predictions = SeasonPredictions(
                top_scorer="",
                league_champion="",
                assist_king="",
                relegated_teams=[],
            )

        if user.points is None:
            # create a SeasonPoints object from season_predictions or default zeros
            season_points_obj = SeasonPoints(
                top_scorer=0,
                assist_king=0,
                league_champion=0,
                relegated_teams=0
            )

            user.points = Points(
                total_points=0,
                last_round_points=0,
                matches={},       
                season_points=season_points_obj
            )

        # Convert to dict for MongoDB
        user_dict = user.model_dump()
        
        # Insert new user
        result = await collection.insert_one(user_dict)

        # Retrieve created user
        created = await collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Failed to create user in DB")

        cleaned = fix_id(created)
        return UserRead(**cleaned)

    @staticmethod
    async def get_user_by_id(user_id: str) -> UserRead:
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user id")

        user = await collection.find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise ValueError("User not found")

        cleaned = fix_id(user)
        return UserRead(**cleaned)

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[UserRead]:
        user = await collection.find_one({"email": email})
        if user is None:
            return None

        cleaned = fix_id(user)
        return UserRead(**cleaned)

    @staticmethod
    async def get_all_users() -> List[UserRead]:
        """
        Retrieve all users from the database.
        Returns a list of UserRead objects, with IDs fixed.
        """
        users_cursor = collection.find()
        users_list: List[UserRead] = []

        async for user in users_cursor:
            cleaned = fix_id(user)
            users_list.append(UserRead(**cleaned))

        return users_list
