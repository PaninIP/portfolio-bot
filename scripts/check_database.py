import asyncio

from sqlalchemy import text

from app.database.session import engine


async def main() -> None:
    """Check the PostgreSQL connection."""

    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text(
                    """
                    SELECT
                        current_database(),
                        current_user,
                        current_setting('server_version')
                    """
                )
            )

            database_name, database_user, server_version = result.one()

            print(f"Database: {database_name}")
            print(f"User: {database_user}")
            print(f"PostgreSQL: {server_version}")
            print("Connection: OK")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())