"""In-memory implementation of PreferenceRepository."""

from app.domain.entities.user_preference import UserPreferences
from app.domain.interfaces.preference_repository import PreferenceRepositoryInterface


class InMemoryPreferenceRepository(PreferenceRepositoryInterface):
    """
    In-memory implementation of preference repository.

    Note: This is a simple implementation that stores preferences in memory.
    In production, consider using a database-backed implementation.
    """

    def __init__(self):
        self._preferences = UserPreferences()

    def get(self) -> UserPreferences:
        """ユーザー設定を取得"""
        return self._preferences

    def save(self, preferences: UserPreferences) -> UserPreferences:
        """ユーザー設定を保存"""
        self._preferences = preferences
        return self._preferences
