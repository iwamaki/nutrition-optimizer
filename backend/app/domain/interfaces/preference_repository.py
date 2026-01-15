"""User preference repository interface."""

from abc import ABC, abstractmethod

from app.domain.entities.user_preference import UserPreferences


class PreferenceRepositoryInterface(ABC):
    """ユーザー設定リポジトリインターフェース"""

    @abstractmethod
    def get(self) -> UserPreferences:
        """ユーザー設定を取得"""
        pass

    @abstractmethod
    def save(self, preferences: UserPreferences) -> UserPreferences:
        """ユーザー設定を保存"""
        pass
