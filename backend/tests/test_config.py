import unittest

from app.core.config import _normalize_database_url


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


if __name__ == "__main__":
    unittest.main()
