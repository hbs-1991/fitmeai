"""
OAuth Setup Utility for FatSecret MCP Server

Uses OAuth 1.0 three-legged flow to authorize user-level access
(food diary, exercise tracking, weight management).

Run once: python setup_oauth.py
"""

import sys
from src.fatsecret_mcp.auth.oauth_manager import run_oauth_flow
from src.fatsecret_mcp.auth.credentials import check_credentials
from src.fatsecret_mcp.utils import get_logger, ConfigurationError

logger = get_logger(__name__)


def main():
    print("\n" + "=" * 60)
    print("FatSecret MCP Server — OAuth 1.0 Setup")
    print("=" * 60)
    print("\nЭтот скрипт авторизует доступ к вашему аккаунту FatSecret.")
    print("\nПосле авторизации будут доступны:")
    print("  • Дневник питания")
    print("  • Упражнения")
    print("  • Отслеживание веса")

    # Validate credentials
    try:
        check_credentials()
    except ConfigurationError as e:
        print(f"\n❌ Ошибка конфигурации:\n{e}")
        sys.exit(1)

    print("\n" + "-" * 60)
    input("Нажмите ENTER для начала авторизации...")

    try:
        success = run_oauth_flow()

        if success:
            print("\n" + "=" * 60)
            print("Готово!")
            print("=" * 60)
            print("\nСледующие шаги:")
            print("1. Запустите сервер: python main.py")
            print("2. Подключите к Claude Desktop или боту")
            print("3. Начинайте отслеживать питание!")
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("Ошибка")
            print("=" * 60)
            print("\nПопробуйте ещё раз. Проверьте:")
            print("• Интернет-соединение")
            print("• Credentials в .env (CLIENT_ID / CLIENT_SECRET)")
            print("• Callback URL: http://localhost:8080/callback")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nОтменено.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
