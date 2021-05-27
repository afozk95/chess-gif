from typing import Literal, Optional
import argparse
import io
import os
from pathlib import Path
import shutil
import cairosvg
import chess
import chess.pgn
import chess.svg
import imageio
import pygifsicle


def read_pgn_file(path: Path) -> str:
    with open(path, "r") as f:
        data = f.read()
    return data


def pgn_to_game(pgn: str) -> Optional[chess.pgn.Game]:
    pgn_io = io.StringIO(pgn)
    game = chess.pgn.read_game(pgn_io)
    return game


def game_to_svgs(game: chess.pgn.Game, svg_folder_path: Path) -> None:
    board = game.board()
    board_to_svg(board, svg_folder_path / "0.svg")
    for i, move in enumerate(game.mainline_moves(), start=1):
        board.push(move)
        board_to_svg(board, svg_folder_path / f"{i}.svg")


def board_to_svg(board: chess.Board, path: Path) -> None:
    svg_file = chess.svg.board(board)
    save_svg(svg_file, path)


def save_svg(svg_file: chess.svg.SvgWrapper, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w+") as f:
        f.write(svg_file)


def svg_to_png(svg_path: Path, png_path: Optional[Path] = None) -> None:
    if png_path is None:
        png_path = svg_path.parent / (svg_path.stem + ".png")
    png_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))


def svgs_to_pngs(svg_folder_path: Path, png_folder_path: Optional[Path] = None) -> None:
    for svg_path in svg_folder_path.glob("*.svg"):
        png_path = png_folder_path / (svg_path.stem + ".png") if png_folder_path else None
        svg_to_png(svg_path, png_path)


def pngs_to_gif(
    png_folder_path: Path,
    gif_path: Path,
    duration: float = 1,
    optimized: Literal["new", "overwrite", "none"] = "new",
) -> None:
    png_files = sorted(png_folder_path.glob("*.png"), key=lambda x: int(x.stem))

    gif_path.parent.mkdir(parents=True, exist_ok=True)
    with imageio.get_writer(gif_path, mode="I", duration=duration) as writer:
        for filename in png_files:
            image = imageio.imread(filename)
            writer.append_data(image)

    if optimized == "new":
        optimized_gif_path = gif_path.parent / (gif_path.stem + "_optimized" + gif_path.suffix)
        pygifsicle.optimize(gif_path, optimized_gif_path)
    elif optimized == "overwrite":
        pygifsicle.optimize(gif_path)
    elif optimized == "none":
        pass
    else:
        raise ValueError(f"unknown value, {optimized=}")


def main() -> None:
    temp_path = Path("temp")
    svg_folder_path = temp_path / "svg"
    png_folder_path = temp_path / "png"

    parser = argparse.ArgumentParser()
    parser.add_argument("pgn_path", help="path to pgn file")
    parser.add_argument("gif_path", help="path to gif file")
    parser.add_argument("-d", "--duration", required=False, default=1, help="duration of each image in gif")
    parser.add_argument("-o", "--optimized", required=False, default="new", help="options to optimize gif for size")
    args = parser.parse_args()

    pgn = read_pgn_file(Path(args.pgn_path))
    game = pgn_to_game(pgn)

    if game is None:
        print("Cannot parse pgn file")
        return

    game_to_svgs(game, svg_folder_path)
    svgs_to_pngs(svg_folder_path, png_folder_path)
    pngs_to_gif(png_folder_path, Path(args.gif_path), args.duration, args.optimized)
    shutil.rmtree(temp_path)


if __name__ == "__main__":
    main()
