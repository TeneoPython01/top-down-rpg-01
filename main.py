"""
main.py - Entry point for the top-down RPG game.
"""

from game.game import Game


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
