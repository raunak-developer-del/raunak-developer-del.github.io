import pygame
import random
import math

pygame.init()

# ============================================================
# SETTINGS
# ============================================================

CELL = 32
COLS = 10
ROWS = 20

BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL

SIDE_W = 330

WIDTH = BOARD_W + SIDE_W
HEIGHT = BOARD_H

FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TETRIS NEXUS")
clock = pygame.time.Clock()

# ============================================================
# COLORS
# ============================================================

BG = (8, 10, 18)
BOARD_BG = (13, 16, 27)
GRID = (29, 34, 48)

WHITE = (240, 245, 255)
GRAY = (130, 140, 160)

CYAN = (70, 220, 240)
YELLOW = (245, 215, 60)
PURPLE = (175, 90, 235)
GREEN = (80, 220, 120)
RED = (240, 75, 85)
BLUE = (70, 125, 240)
ORANGE = (245, 145, 50)

COLORS = {
    "I": CYAN,
    "O": YELLOW,
    "T": PURPLE,
    "S": GREEN,
    "Z": RED,
    "J": BLUE,
    "L": ORANGE
}

# ============================================================
# FONTS
# ============================================================

title_font = pygame.font.Font(None, 52)
big_font = pygame.font.Font(None, 70)
font = pygame.font.Font(None, 32)
small_font = pygame.font.Font(None, 24)

# ============================================================
# TETROMINOES
# ============================================================

SHAPES = {
    "I": [
        [
            "....",
            "IIII",
            "....",
            "...."
        ]
    ],

    "O": [
        [
            ".OO.",
            ".OO.",
            "....",
            "...."
        ]
    ],

    "T": [
        [
            ".T..",
            "TTT.",
            "....",
            "...."
        ]
    ],

    "S": [
        [
            ".SS.",
            "SS..",
            "....",
            "...."
        ]
    ],

    "Z": [
        [
            "ZZ..",
            ".ZZ.",
            "....",
            "...."
        ]
    ],

    "J": [
        [
            "J...",
            "JJJ.",
            "....",
            "...."
        ]
    ],

    "L": [
        [
            "..L.",
            "LLL.",
            "....",
            "...."
        ]
    ]
}

# ============================================================
# ROTATION
# ============================================================

def rotate_matrix(matrix):
    return [
        [matrix[3 - x][y] for x in range(4)]
        for y in range(4)
    ]


def get_rotations(shape):
    rotations = []

    matrix = [list(row) for row in shape[0]]

    for _ in range(4):
        if matrix not in rotations:
            rotations.append(matrix)

        matrix = rotate_matrix(matrix)

    return rotations


ROTATIONS = {}

for name in SHAPES:
    ROTATIONS[name] = get_rotations(SHAPES[name])

# ============================================================
# BOARD
# ============================================================

board = [
    [None for _ in range(COLS)]
    for _ in range(ROWS)
]

# ============================================================
# PARTICLES
# ============================================================

particles = []


def create_particles(x, y, color, amount=12):

    for _ in range(amount):

        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 4)

        particles.append({
            "x": x,
            "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": random.randint(20, 40),
            "size": random.randint(2, 5),
            "color": color
        })


def update_particles():

    for p in particles[:]:

        p["x"] += p["vx"]
        p["y"] += p["vy"]

        p["vy"] += 0.08
        p["life"] -= 1

        if p["life"] <= 0:
            particles.remove(p)


def draw_particles():

    for p in particles:

        pygame.draw.circle(
            screen,
            p["color"],
            (int(p["x"]), int(p["y"])),
            p["size"]
        )

# ============================================================
# PIECE CLASS
# ============================================================

class Piece:

    def __init__(self, kind):

        self.kind = kind
        self.rotation = 0

        self.x = 3
        self.y = -1

    def cells(self):

        matrix = ROTATIONS[self.kind][self.rotation]

        result = []

        for row in range(4):

            for col in range(4):

                if matrix[row][col] != ".":

                    result.append(
                        (
                            self.x + col,
                            self.y + row
                        )
                    )

        return result

    def color(self):

        return COLORS[self.kind]

# ============================================================
# 7-BAG RANDOMIZER
# ============================================================

bag = []


def refill_bag():

    global bag

    bag = list(SHAPES.keys())
    random.shuffle(bag)


def random_piece():

    global bag

    if not bag:
        refill_bag()

    return Piece(bag.pop())

# ============================================================
# QUEUE
# ============================================================

next_queue = []


def fill_queue():

    while len(next_queue) < 5:
        next_queue.append(random_piece())


# ============================================================
# COLLISION
# ============================================================

def collision(piece):

    for x, y in piece.cells():

        if x < 0 or x >= COLS:
            return True

        if y >= ROWS:
            return True

        if y >= 0 and board[y][x] is not None:
            return True

    return False

# ============================================================
# MOVE
# ============================================================

def move_piece(dx, dy):

    global current

    current.x += dx
    current.y += dy

    if collision(current):

        current.x -= dx
        current.y -= dy

        return False

    return True

# ============================================================
# ROTATE
# ============================================================

def rotate_piece():

    global current

    old_rotation = current.rotation

    current.rotation = (
        current.rotation + 1
    ) % len(ROTATIONS[current.kind])

    # Simple wall kicks
    kicks = [0, -1, 1, -2, 2]

    for kick in kicks:

        current.x += kick

        if not collision(current):
            return True

        current.x -= kick

    current.rotation = old_rotation

    return False

# ============================================================
# GHOST PIECE
# ============================================================

def get_ghost():

    ghost = Piece(current.kind)

    ghost.x = current.x
    ghost.y = current.y
    ghost.rotation = current.rotation

    while True:

        ghost.y += 1

        if collision(ghost):
            ghost.y -= 1
            break

    return ghost

# ============================================================
# LOCK PIECE
# ============================================================

def lock_piece():

    global score
    global lines
    global level
    global combo
    global back_to_back
    global current

    for x, y in current.cells():

        if y < 0:

            game_over = True
            return

        board[y][x] = current.kind

        create_particles(
            x * CELL + CELL // 2,
            y * CELL + CELL // 2,
            COLORS[current.kind],
            3
        )

    cleared = clear_lines()

    if cleared > 0:

        # Combo
        combo += 1

        combo_bonus = combo * 50

        # Standard line scoring
        if cleared == 1:
            base = 100

        elif cleared == 2:
            base = 300

        elif cleared == 3:
            base = 500

        else:
            base = 800

        # Tetris bonus
        if cleared == 4:

            base += 400

            back_to_back += 1

            if back_to_back > 1:
                base += 300

        else:
            back_to_back = 0

        score += (base + combo_bonus) * level

        lines += cleared

        # Level up every 10 lines
        level = lines // 10 + 1

    else:

        combo = 0

# ============================================================
# CLEAR LINES
# ============================================================

def clear_lines():

    global board

    full_rows = []

    for y in range(ROWS):

        if all(board[y][x] is not None for x in range(COLS)):
            full_rows.append(y)

    for y in full_rows:

        for x in range(COLS):

            create_particles(
                x * CELL + CELL // 2,
                y * CELL + CELL // 2,
                WHITE,
                5
            )

    for y in reversed(full_rows):

        del board[y]

        board.insert(
            0,
            [None for _ in range(COLS)]
        )

    return len(full_rows)

# ============================================================
# SPAWN
# ============================================================

current = None
hold_piece = None
hold_used = False


def spawn_piece():

    global current
    global hold_used

    fill_queue()

    current = next_queue.pop(0)

    fill_queue()

    current.x = 3
    current.y = -1
    current.rotation = 0

    hold_used = False

    if collision(current):
        return False

    return True

# ============================================================
# HOLD
# ============================================================

def hold_current():

    global current
    global hold_piece
    global hold_used

    if hold_used:
        return

    if hold_piece is None:

        hold_piece = Piece(current.kind)
        spawn_piece()

    else:

        temp = hold_piece

        hold_piece = Piece(current.kind)

        current = Piece(temp.kind)

        current.x = 3
        current.y = -1
        current.rotation = 0

    hold_used = True

# ============================================================
# HARD DROP
# ============================================================

def hard_drop():

    global score

    distance = 0

    while move_piece(0, 1):
        distance += 1

    score += distance * 2

    lock_piece()

    spawn_piece()

# ============================================================
# RESET
# ============================================================

score = 0
lines = 0
level = 1
combo = 0
back_to_back = 0

game_over = False
paused = False

fall_timer = 0
lock_timer = 0

DAS = 0


def reset_game():

    global board
    global score
    global lines
    global level
    global combo
    global back_to_back
    global current
    global hold_piece
    global hold_used
    global next_queue
    global game_over
    global fall_timer
    global lock_timer

    board = [
        [None for _ in range(COLS)]
        for _ in range(ROWS)
    ]

    score = 0
    lines = 0
    level = 1
    combo = 0
    back_to_back = 0

    current = None
    hold_piece = None
    hold_used = False

    next_queue = []

    game_over = False

    fall_timer = 0
    lock_timer = 0

    fill_queue()

    spawn_piece()


reset_game()

# ============================================================
# FALL SPEED
# ============================================================

def fall_speed():

    # Starts comfortable and becomes faster
    return max(
        70,
        int(650 - (level - 1) * 55)
    )

# ============================================================
# DRAW BLOCK
# ============================================================

def draw_block(x, y, color, ghost=False):

    px = x * CELL
    py = y * CELL

    if ghost:

        pygame.draw.rect(
            screen,
            color,
            (
                px + 5,
                py + 5,
                CELL - 10,
                CELL - 10
            ),
            2,
            border_radius=5
        )

        return

    # Main block
    pygame.draw.rect(
        screen,
        color,
        (
            px + 2,
            py + 2,
            CELL - 4,
            CELL - 4
        ),
        border_radius=6
    )

    # Highlight
    highlight = tuple(
        min(255, c + 45)
        for c in color
    )

    pygame.draw.line(
        screen,
        highlight,
        (px + 7, py + 7),
        (px + CELL - 8, py + 7),
        2
    )

    pygame.draw.line(
        screen,
        highlight,
        (px + 7, py + 7),
        (px + 7, py + CELL - 8),
        2
    )

# ============================================================
# DRAW BOARD
# ============================================================

def draw_board():

    pygame.draw.rect(
        screen,
        BOARD_BG,
        (0, 0, BOARD_W, BOARD_H)
    )

    # Grid
    for x in range(COLS + 1):

        pygame.draw.line(
            screen,
            GRID,
            (x * CELL, 0),
            (x * CELL, BOARD_H)
        )

    for y in range(ROWS + 1):

        pygame.draw.line(
            screen,
            GRID,
            (0, y * CELL),
            (BOARD_W, y * CELL)
        )

    # Locked blocks
    for y in range(ROWS):

        for x in range(COLS):

            if board[y][x] is not None:

                draw_block(
                    x,
                    y,
                    COLORS[board[y][x]]
                )

# ============================================================
# DRAW CURRENT PIECE
# ============================================================

def draw_current():

    ghost = get_ghost()

    for x, y in ghost.cells():

        if y >= 0:
            draw_block(
                x,
                y,
                current.color(),
                True
            )

    for x, y in current.cells():

        if y >= 0:
            draw_block(
                x,
                y,
                current.color()
            )

# ============================================================
# DRAW MINI PIECE
# ============================================================

def draw_mini(piece, center_x, center_y, scale=22):

    matrix = ROTATIONS[piece.kind][0]

    color = COLORS[piece.kind]

    width = 4 * scale
    height = 4 * scale

    start_x = center_x - width // 2
    start_y = center_y - height // 2

    for row in range(4):

        for col in range(4):

            if matrix[row][col] != ".":

                rect = pygame.Rect(
                    start_x + col * scale + 2,
                    start_y + row * scale + 2,
                    scale - 4,
                    scale - 4
                )

                pygame.draw.rect(
                    screen,
                    color,
                    rect,
                    border_radius=4
                )

# ============================================================
# PANEL
# ============================================================

def draw_panel():

    panel_x = BOARD_W

    pygame.draw.rect(
        screen,
        BG,
        (
            panel_x,
            0,
            SIDE_W,
            HEIGHT
        )
    )

    pygame.draw.line(
        screen,
        GRID,
        (panel_x, 0),
        (panel_x, HEIGHT),
        2
    )

    # Title
    title = title_font.render(
        "TETRIS NEXUS",
        True,
        CYAN
    )

    screen.blit(
        title,
        (
            panel_x + 25,
            25
        )
    )

    # Score
    score_label = small_font.render(
        "SCORE",
        True,
        GRAY
    )

    screen.blit(
        score_label,
        (
            panel_x + 25,
            95
        )
    )

    score_text = font.render(
        f"{score:,}",
        True,
        WHITE
    )

    screen.blit(
        score_text,
        (
            panel_x + 25,
            117
        )
    )

    # Level
    level_label = small_font.render(
        "LEVEL",
        True,
        GRAY
    )

    screen.blit(
        level_label,
        (
            panel_x + 170,
            95
        )
    )

    level_text = font.render(
        str(level),
        True,
        WHITE
    )

    screen.blit(
        level_text,
        (
            panel_x + 170,
            117
        )
    )

    # Lines
    lines_label = small_font.render(
        "LINES",
        True,
        GRAY
    )

    screen.blit(
        lines_label,
        (
            panel_x + 25,
            160
        )
    )

    lines_text = font.render(
        str(lines),
        True,
        WHITE
    )

    screen.blit(
        lines_text,
        (
            panel_x + 25,
            182
        )
    )

    # Combo
    combo_label = small_font.render(
        "COMBO",
        True,
        GRAY
    )

    screen.blit(
        combo_label,
        (
            panel_x + 170,
            160
        )
    )

    combo_text = font.render(
        str(combo),
        True,
        YELLOW
    )

    screen.blit(
        combo_text,
        (
            panel_x + 170,
            182
        )
    )

    # Hold
    hold_label = font.render(
        "HOLD",
        True,
        WHITE
    )

    screen.blit(
        hold_label,
        (
            panel_x + 25,
            240
        )
    )

    pygame.draw.rect(
        screen,
        BOARD_BG,
        (
            panel_x + 20,
            275,
            130,
            110
        ),
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        GRID,
        (
            panel_x + 20,
            275,
            130,
            110
        ),
        2,
        border_radius=10
    )

    if hold_piece is not None:

        draw_mini(
            hold_piece,
            panel_x + 85,
            330
        )

    # Next
    next_label = font.render(
        "NEXT",
        True,
        WHITE
    )

    screen.blit(
        next_label,
        (
            panel_x + 180,
            240
        )
    )

    pygame.draw.rect(
        screen,
        BOARD_BG,
        (
            panel_x + 170,
            275,
            135,
            250
        ),
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        GRID,
        (
            panel_x + 170,
            275,
            135,
            250
        ),
        2,
        border_radius=10
    )

    for i, piece in enumerate(next_queue[:4]):

        draw_mini(
            piece,
            panel_x + 237,
            310 + i * 58,
            18
        )

    # Controls
    controls_y = 550

    controls = [
        "W  Rotate",
        "A / D  Move",
        "S  Soft Drop",
        "SPACE  Hard Drop",
        "C  Hold",
        "P  Pause",
        "R  Restart"
    ]

    for i, text in enumerate(controls):

        surface = small_font.render(
            text,
            True,
            GRAY
        )

        screen.blit(
            surface,
            (
                panel_x + 25,
                controls_y + i * 20
            )
        )

# ============================================================
# PAUSE SCREEN
# ============================================================

def draw_pause():

    overlay = pygame.Surface(
        (BOARD_W, BOARD_H),
        pygame.SRCALPHA
    )

    overlay.fill((0, 0, 0, 175))

    screen.blit(
        overlay,
        (0, 0)
    )

    text = big_font.render(
        "PAUSED",
        True,
        WHITE
    )

    screen.blit(
        text,
        (
            BOARD_W // 2 - text.get_width() // 2,
            BOARD_H // 2 - 50
        )
    )

    hint = font.render(
        "Press P to continue",
        True,
        GRAY
    )

    screen.blit(
        hint,
        (
            BOARD_W // 2 - hint.get_width() // 2,
            BOARD_H // 2 + 25
        )
    )

# ============================================================
# GAME OVER SCREEN
# ============================================================

def draw_game_over():

    overlay = pygame.Surface(
        (BOARD_W, BOARD_H),
        pygame.SRCALPHA
    )

    overlay.fill((0, 0, 0, 190))

    screen.blit(
        overlay,
        (0, 0)
    )

    text = big_font.render(
        "GAME OVER",
        True,
        RED
    )

    screen.blit(
        text,
        (
            BOARD_W // 2 - text.get_width() // 2,
            BOARD_H // 2 - 90
        )
    )

    score_text = font.render(
        f"Score: {score:,}",
        True,
        WHITE
    )

    screen.blit(
        score_text,
        (
            BOARD_W // 2 - score_text.get_width() // 2,
            BOARD_H // 2 - 10
        )
    )

    restart = font.render(
        "Press R to restart",
        True,
        CYAN
    )

    screen.blit(
        restart,
        (
            BOARD_W // 2 - restart.get_width() // 2,
            BOARD_H // 2 + 45
        )
    )

# ============================================================
# MAIN LOOP
# ============================================================

running = True

while running:

    dt = clock.tick(FPS)

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

            # Pause
            if event.key == pygame.K_p:

                if not game_over:
                    paused = not paused

            # Restart
            if event.key == pygame.K_r:

                reset_game()

            if not paused and not game_over:

                # WASD movement
                if event.key == pygame.K_a:
                    move_piece(-1, 0)

                if event.key == pygame.K_d:
                    move_piece(1, 0)

                if event.key == pygame.K_w:
                    rotate_piece()

                if event.key == pygame.K_s:
                    if move_piece(0, 1):
                        score += 1

                # Hard drop
                if event.key == pygame.K_SPACE:
                    hard_drop()

                # Hold
                if event.key == pygame.K_c:
                    hold_current()

    # --------------------------------------------------------
    # GAME UPDATE
    # --------------------------------------------------------

    if not paused and not game_over:

        keys = pygame.key.get_pressed()

        # Continuous A/D movement
        DAS += 1

        if DAS >= 6:

            if keys[pygame.K_a]:
                move_piece(-1, 0)

            if keys[pygame.K_d]:
                move_piece(1, 0)

            DAS = 0

        # Automatic gravity
        fall_timer += dt

        if fall_timer >= fall_speed():

            if not move_piece(0, 1):

                lock_timer += dt

                if lock_timer >= 450:

                    lock_piece()

                    if not spawn_piece():
                        game_over = True

                    lock_timer = 0

            else:

                lock_timer = 0

            fall_timer = 0

    # --------------------------------------------------------
    # DRAW
    # --------------------------------------------------------

    draw_board()

    if current is not None and not game_over:
        draw_current()

    update_particles()
    draw_particles()

    draw_panel()

    if paused:
        draw_pause()

    if game_over:
        draw_game_over()

    pygame.display.flip()


pygame.quit()