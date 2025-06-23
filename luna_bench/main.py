from luna_quantum.util.log_utils import Logging

logger = Logging.get_logger(__file__)


def main() -> None:
    """Fake main function."""
    logger.info("Hello world!")


if __name__ == "__main__":
    main()
