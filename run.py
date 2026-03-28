"""
run.py - Entry point for Top-Down RPG.
"""

from src.game import Game


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
