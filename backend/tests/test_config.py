import unittest

from app.core.config import DEFAULT_JWT_SECRET, Settings, _normalize_database_url


class DatabaseUrlTests(unittest.TestCase):
    def test_postgresql_url_uses_psycopg_3(self) -> None:
        self.assertEqual(
            "postgresql+psycopg://user:password@localhost/library",
            _normalize_database_url(
                "postgresql://user:password@localhost/library"
            ),
        )

    def test_provider_postgres_alias_uses_psycopg_3(self) -> None:
        self.assertEqual(
            "postgresql+psycopg://user:password@localhost/library",
            _normalize_database_url("postgres://user:password@localhost/library"),
        )

    def test_explicit_driver_url_is_unchanged(self) -> None:
        value = "postgresql+psycopg://user:password@localhost/library"
        self.assertEqual(value, _normalize_database_url(value))

    def test_production_rejects_default_jwt_secret(self) -> None:
        with self.assertRaises(RuntimeError):
            Settings(
                environment="production",
                jwt_secret_key=DEFAULT_JWT_SECRET,
            )

    def test_production_accepts_strong_jwt_secret(self) -> None:
        settings = Settings(
            environment="production",
            jwt_secret_key="a-unique-production-secret-that-is-long-enough",
        )
        self.assertEqual("HS256", settings.jwt_algorithm)

    def test_unsupported_jwt_algorithm_is_rejected(self) -> None:
        with self.assertRaises(RuntimeError):
            Settings(jwt_algorithm="none")


if __name__ == "__main__":
    unittest.main()
