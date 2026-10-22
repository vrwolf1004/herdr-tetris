# Game rules

[**English**](rules.md) | [한국어](rules.ko.md)

Each rule cites the code that implements it. Items marked **(inferred)** are my reading of the code, not something the code states directly.

## Board and pieces

- Board: 10 columns by 20 rows (`src/game.py:5-6`).
- Seven pieces: I, O, T, S, Z, J, L (`src/game.py:15-24`). Colors are set in `src/tetris.py:25`.
- New pieces start at the top with the bounding box at column 3 (`src/game.py:7`, `src/game.py:134-141`).
- Pieces come from a 7-bag: all seven kinds are shuffled once, dealt, then reshuffled (`src/game.py:113-118`).
- The next piece is shown in the side panel (`src/tetris.py:69-74`, `src/tetris.py:104`).

## Rotation

- Rotation is 90° clockwise, computed by a coordinate transform (`src/game.py:33-35`). The four states are precomputed (`src/game.py:38-45`).
- If the rotated piece collides, the game tries horizontal offsets 0, -1, +1, -2, +2 in that order (`src/game.py:12`, `src/game.py:84-89`). This is a simple wall kick. It is not the official SRS table; the offsets are the same for every piece (**inferred** from the code, not from a rule document).
- There are no vertical kicks.

## Movement and gravity

- Left and right move one column when the new position fits (`src/game.py:74-78`).
- Gravity moves a piece down one row per tick. The tick interval is `max(0.05, 0.8 - 0.07 × (level - 1))` seconds (`src/tetris.py:58-60`, `src/tetris.py:205-207`, `src/tetris.py:253-255`).
- Soft drop moves one row and gives +1 point per row (`src/game.py:96-102`).
- Hard drop moves the piece to the lowest free row and gives +2 points per row, then locks (`src/game.py:104-111`).

## Locking

- A piece locks when it cannot move down on a tick or soft drop (`src/game.py:91-94`, `src/game.py:96-102`).
- There is no lock delay (**inferred**: the first failed downward step locks the piece immediately).

## Line clear

- Every full row is removed and the rows above move down (`src/game.py:152-158`).
- Lines are removed at lock time, before the next piece spawns (`src/game.py:143-150`).

## Scoring and level

| Lines cleared at once | Base points | Points at level L |
|---|---|---|
| 1 | 100 | 100 × L |
| 2 | 300 | 300 × L |
| 3 | 500 | 500 × L |
| 4 | 800 | 800 × L |

- The table is `LINE_SCORES` (`src/game.py:10`). Points are added at lock time (`src/game.py:147-149`).
- The level used for the bonus is the level **before** this clear's lines are added (`src/game.py:147-149`, where `self.lines` is updated afterwards).
- Level = `lines // 10 + 1` (`src/game.py:68-69`). Every 10 cleared lines raise the level by one.
- The 3-line and 4-line rows in the table are scoring only. The game does not trigger a special effect.

## Game over

- After a lock and line clear, the game tries to spawn the next piece at the top. If that position overlaps existing blocks, `game_over` becomes true (`src/game.py:134-141`).
- After game over, moves, rotation, soft drop, and hard drop are ignored (`src/game.py:75`, `src/game.py:81-82`, `src/game.py:97-98`, `src/game.py:105-106`).
- The UI shows the game-over message. `R` restarts and `Q` quits (`src/tetris.py:89-90`, `src/tetris.py:233-236`).

## Pause

- `P` toggles pause. While paused, gravity does not run and piece actions are ignored (`src/tetris.py:237-241`).
- `Q` still quits while paused.
- The monitor screen also freezes the game. While it is shown, game keys are ignored and gravity does not run (`src/tetris.py:198-201`).
