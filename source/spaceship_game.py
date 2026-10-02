import pygame
import random
import math
import sys

# ============================================================
# INITIALIZATION
# ============================================================

pygame.init()

WIDTH = 1200
HEIGHT = 750
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GALACTIC STRIKE v2.0")

clock = pygame.time.Clock()

# ============================================================
# COLORS
# ============================================================

BLACK = (3, 5, 15)
WHITE = (240, 245, 255)

BLUE = (50, 160, 255)
CYAN = (50, 230, 255)

RED = (255, 60, 70)
ORANGE = (255, 150, 40)
YELLOW = (255, 230, 70)

GREEN = (60, 240, 120)
PURPLE = (180, 80, 255)

GRAY = (100, 110, 130)
DARK_GRAY = (30, 35, 50)

# ============================================================
# FONTS
# ============================================================

font = pygame.font.Font(None, 30)
small_font = pygame.font.Font(None, 23)
big_font = pygame.font.Font(None, 72)

# ============================================================
# GAME VARIABLES
# ============================================================

score = 0
credits = 0

weapon_level = 1

game_active = True

# ============================================================
# STARFIELD
# ============================================================

stars = []

for _ in range(220):

    stars.append({
        "x": random.randint(0, WIDTH),
        "y": random.randint(0, HEIGHT),
        "speed": random.uniform(0.5, 4),
        "size": random.randint(1, 3)
    })


def update_stars():

    for star in stars:

        star["x"] -= star["speed"]

        if star["x"] < 0:

            star["x"] = WIDTH
            star["y"] = random.randint(0, HEIGHT)


def draw_stars():

    for star in stars:

        brightness = int(80 + star["speed"] * 40)

        color = (
            min(brightness, 255),
            min(brightness, 255),
            min(brightness + 25, 255)
        )

        pygame.draw.circle(
            screen,
            color,
            (int(star["x"]), int(star["y"])),
            star["size"]
        )


# ============================================================
# PLAYER
# ============================================================

player = pygame.Rect(
    120,
    HEIGHT // 2,
    70,
    40
)

player_speed = 5
boost_speed = 10

hull = 100
max_hull = 100

shield = 100
max_shield = 100

boost_energy = 100
max_boost = 100


# ============================================================
# PLAYER BULLETS
# ============================================================

bullets = []


def shoot():

    if weapon_level == 1:

        bullets.append({
            "rect": pygame.Rect(
                player.right,
                player.centery - 3,
                25,
                6
            ),
            "damage": 20
        })

    elif weapon_level == 2:

        for offset in (-10, 10):

            bullets.append({
                "rect": pygame.Rect(
                    player.right,
                    player.centery + offset,
                    25,
                    5
                ),
                "damage": 25
            })

    else:

        for offset in (-15, 0, 15):

            bullets.append({
                "rect": pygame.Rect(
                    player.right,
                    player.centery + offset,
                    30,
                    5
                ),
                "damage": 30
            })


# ============================================================
# ENEMY BULLETS
# ============================================================

enemy_bullets = []


def enemy_shoot(enemy):

    rect = enemy["rect"]

    enemy_bullets.append({

        "rect": pygame.Rect(
            rect.left - 15,
            rect.centery - 3,
            18,
            6
        ),

        "speed": random.uniform(6, 9),

        "damage": 8
    })


# ============================================================
# ENEMIES
# ============================================================

enemies = []

spawn_timer = 0
spawn_delay = 70

enemy_types = [
    "fighter",
    "tank",
    "kamikaze"
]


def spawn_enemy():

    enemy_type = random.choice(enemy_types)

    y = random.randint(
        60,
        HEIGHT - 60
    )

    if enemy_type == "fighter":

        enemy = {

            "type": "fighter",

            "rect": pygame.Rect(
                WIDTH + 50,
                y,
                60,
                35
            ),

            "speed": random.uniform(
                3,
                4.5
            ),

            "health": 40,
            "max_health": 40,

            "cooldown": random.randint(
                40,
                100
            ),

            "phase": random.uniform(
                0,
                math.pi * 2
            )
        }

    elif enemy_type == "tank":

        enemy = {

            "type": "tank",

            "rect": pygame.Rect(
                WIDTH + 50,
                y,
                85,
                55
            ),

            "speed": random.uniform(
                1.5,
                2.2
            ),

            "health": 120,
            "max_health": 120,

            "cooldown": random.randint(
                60,
                120
            ),

            "phase": random.uniform(
                0,
                math.pi * 2
            )
        }

    else:

        enemy = {

            "type": "kamikaze",

            "rect": pygame.Rect(
                WIDTH + 50,
                y,
                50,
                30
            ),

            "speed": random.uniform(
                4,
                6
            ),

            "health": 30,
            "max_health": 30,

            "cooldown": 999,

            "phase": random.uniform(
                0,
                math.pi * 2
            )
        }

    enemies.append(enemy)


# ============================================================
# ASTEROIDS
# ============================================================

asteroids = []

asteroid_timer = 0


def spawn_asteroid():

    size = random.randint(
        25,
        60
    )

    asteroids.append({

        "rect": pygame.Rect(
            WIDTH + size,
            random.randint(
                20,
                HEIGHT - size
            ),
            size,
            size
        ),

        "speed": random.uniform(
            2,
            4
        ),

        "rotation": random.randint(
            0,
            360
        )
    })


def draw_asteroid(asteroid):

    rect = asteroid["rect"]

    pygame.draw.circle(
        screen,
        (90, 90, 100),
        rect.center,
        rect.width // 2
    )

    # Craters

    pygame.draw.circle(
        screen,
        (55, 55, 65),
        (
            rect.centerx -
            rect.width // 6,

            rect.centery -
            rect.height // 6
        ),
        max(3, rect.width // 8)
    )

    pygame.draw.circle(
        screen,
        (55, 55, 65),
        (
            rect.centerx +
            rect.width // 5,

            rect.centery +
            rect.height // 7
        ),
        max(3, rect.width // 10)
    )


# ============================================================
# PARTICLES
# ============================================================

particles = []


def explosion(
    x,
    y,
    amount=40
):

    for _ in range(amount):

        angle = random.uniform(
            0,
            math.pi * 2
        )

        speed = random.uniform(
            1,
            7
        )

        particles.append({

            "x": x,
            "y": y,

            "vx":
                math.cos(angle) *
                speed,

            "vy":
                math.sin(angle) *
                speed,

            "life":
                random.randint(
                    20,
                    50
                ),

            "size":
                random.randint(
                    2,
                    6
                )
        })


def update_particles():

    for particle in particles[:]:

        particle["x"] += particle["vx"]
        particle["y"] += particle["vy"]

        particle["vx"] *= 0.96
        particle["vy"] *= 0.96

        particle["life"] -= 1

        if particle["life"] <= 0:

            particles.remove(
                particle
            )


def draw_particles():

    for particle in particles:

        if particle["life"] > 30:

            color = ORANGE

        elif particle["life"] > 15:

            color = YELLOW

        else:

            color = RED

        pygame.draw.circle(

            screen,

            color,

            (
                int(particle["x"]),
                int(particle["y"])
            ),

            particle["size"]
        )


# ============================================================
# DRAW PLAYER
# ============================================================

def draw_player():

    x = player.x
    y = player.y

    # Engine flame

    flame = random.randint(
        15,
        30
    )

    pygame.draw.polygon(

        screen,

        ORANGE,

        [
            (x, y + 10),
            (x - flame, y + 20),
            (x, y + 30)
        ]
    )

    pygame.draw.polygon(

        screen,

        YELLOW,

        [
            (x, y + 15),
            (
                x - flame // 2,
                y + 20
            ),
            (x, y + 25)
        ]
    )

    # Main hull

    pygame.draw.polygon(

        screen,

        (70, 105, 145),

        [
            (x, y + 20),
            (x + 45, y),
            (x + 70, y + 20),
            (x + 45, y + 40)
        ]
    )

    # Nose

    pygame.draw.polygon(

        screen,

        (170, 195, 220),

        [
            (x + 45, y),
            (x + 70, y + 20),
            (x + 45, y + 40)
        ]
    )

    # Cockpit

    pygame.draw.ellipse(

        screen,

        CYAN,

        (
            x + 30,
            y + 10,
            25,
            20
        )
    )

    # Upper wing

    pygame.draw.polygon(

        screen,

        (40, 60, 90),

        [
            (x + 25, y),
            (x + 5, y - 18),
            (x + 42, y + 5)
        ]
    )

    # Lower wing

    pygame.draw.polygon(

        screen,

        (40, 60, 90),

        [
            (x + 25, y + 40),
            (x + 5, y + 58),
            (x + 42, y + 35)
        ]
    )

    # Shield

    if shield > 0:

        pygame.draw.ellipse(

            screen,

            CYAN,

            player.inflate(
                20,
                20
            ),

            2
        )


# ============================================================
# DRAW ENEMY
# ============================================================

def draw_enemy(enemy):

    rect = enemy["rect"]

    x = rect.x
    y = rect.y

    # Fighter

    if enemy["type"] == "fighter":

        pygame.draw.polygon(

            screen,

            RED,

            [
                (x, y + 17),
                (x + 50, y),
                (x + 60, y + 17),
                (x + 50, y + 35)
            ]
        )

        pygame.draw.circle(

            screen,

            ORANGE,

            (
                x + 18,
                y + 17
            ),

            6
        )

    # Tank

    elif enemy["type"] == "tank":

        pygame.draw.rect(

            screen,

            (100, 45, 55),

            rect,

            border_radius=8
        )

        pygame.draw.rect(

            screen,

            GRAY,

            (
                x + 20,
                y + 10,
                45,
                35
            )
        )

        pygame.draw.circle(

            screen,

            RED,

            (
                x + 42,
                y + 27
            ),

            9
        )

    # Kamikaze

    else:

        pygame.draw.polygon(

            screen,

            ORANGE,

            [
                (x, y + 15),
                (x + 50, y),
                (x + 40, y + 15),
                (x + 50, y + 30)
            ]
        )

    # Enemy health bar

    ratio = max(
        0,
        enemy["health"] /
        enemy["max_health"]
    )

    pygame.draw.rect(

        screen,

        RED,

        (
            x,
            y - 9,
            rect.width,
            5
        )
    )

    pygame.draw.rect(

        screen,

        GREEN,

        (
            x,
            y - 9,
            int(
                rect.width *
                ratio
            ),
            5
        )
    )


# ============================================================
# DAMAGE PLAYER
# ============================================================

def damage_player(amount):

    global shield
    global hull

    # Shield absorbs damage first

    if shield > 0:

        absorbed = min(
            shield,
            amount
        )

        shield -= absorbed

        amount -= absorbed

    # Remaining damage hits hull

    if amount > 0:

        hull -= amount

    hull = max(
        0,
        hull
    )

    shield = max(
        0,
        shield
    )


# ============================================================
# HUD
# ============================================================

def draw_bar(
    x,
    y,
    width,
    height,
    value,
    maximum,
    color
):

    pygame.draw.rect(

        screen,

        DARK_GRAY,

        (
            x,
            y,
            width,
            height
        )
    )

    current = int(

        width *
        value /
        maximum
    )

    pygame.draw.rect(

        screen,

        color,

        (
            x,
            y,
            current,
            height
        )
    )


def draw_hud():

    # Hull

    draw_bar(

        20,
        20,
        250,
        22,
        hull,
        max_hull,

        GREEN
        if hull > 30
        else RED
    )

    screen.blit(

        small_font.render(
            f"HULL: {int(hull)}",
            True,
            WHITE
        ),

        (25, 45)
    )

    # Shield

    draw_bar(

        20,
        75,
        250,
        18,
        shield,
        max_shield,
        CYAN
    )

    screen.blit(

        small_font.render(
            f"SHIELD: {int(shield)}",
            True,
            WHITE
        ),

        (25, 97)
    )

    # Boost

    draw_bar(

        20,
        125,
        250,
        15,
        boost_energy,
        max_boost,
        YELLOW
    )

    screen.blit(

        small_font.render(
            "BOOST",
            True,
            WHITE
        ),

        (25, 145)
    )

    # Score

    screen.blit(

        font.render(
            f"SCORE: {score}",
            True,
            WHITE
        ),

        (WIDTH - 200, 20)
    )

    # Credits

    screen.blit(

        font.render(
            f"CREDITS: {credits}",
            True,
            YELLOW
        ),

        (WIDTH - 220, 55)
    )

    # Weapon

    screen.blit(

        small_font.render(
            f"WEAPON LEVEL: {weapon_level}",
            True,
            CYAN
        ),

        (WIDTH - 260, 90)
    )


# ============================================================
# GAME OVER
# ============================================================

def game_over_screen():

    screen.fill(BLACK)

    title = big_font.render(

        "SHIP DESTROYED",

        True,

        RED
    )

    final_score = font.render(

        f"Final Score: {score}",

        True,

        WHITE
    )

    restart = font.render(

        "Press R to restart",

        True,

        CYAN
    )

    screen.blit(

        title,

        title.get_rect(

            center=(
                WIDTH // 2,
                HEIGHT // 2 - 70
            )
        )
    )

    screen.blit(

        final_score,

        final_score.get_rect(

            center=(
                WIDTH // 2,
                HEIGHT // 2
            )
        )
    )

    screen.blit(

        restart,

        restart.get_rect(

            center=(
                WIDTH // 2,
                HEIGHT // 2 + 60
            )
        )
    )

    pygame.display.flip()


# ============================================================
# RESET GAME
# ============================================================

def reset_game():

    global hull
    global shield
    global boost_energy
    global score
    global credits
    global weapon_level
    global spawn_delay
    global spawn_timer
    global asteroid_timer

    player.x = 120
    player.y = HEIGHT // 2

    hull = 100
    shield = 100

    boost_energy = 100

    score = 0
    credits = 0

    weapon_level = 1

    spawn_delay = 70
    spawn_timer = 0
    asteroid_timer = 0

    bullets.clear()
    enemy_bullets.clear()
    enemies.clear()
    asteroids.clear()
    particles.clear()


# ============================================================
# MAIN GAME LOOP
# ============================================================

running = True

while running:

    clock.tick(FPS)

    # ========================================================
    # EVENTS
    # ========================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        if event.type == pygame.KEYDOWN:

            # Shoot

            if (
                event.key == pygame.K_SPACE
                and game_active
            ):

                shoot()

            # Restart

            if (
                event.key == pygame.K_r
                and not game_active
            ):

                reset_game()

                game_active = True

    # ========================================================
    # ACTIVE GAME
    # ========================================================

    if game_active:

        keys = pygame.key.get_pressed()

        # ----------------------------------------------------
        # MOVEMENT
        # ----------------------------------------------------

        speed = player_speed

        # Boost

        if (
            keys[pygame.K_LSHIFT]
            and boost_energy > 0
        ):

            speed = boost_speed

            boost_energy -= 1

        else:

            if boost_energy < max_boost:

                boost_energy += 0.3

        # Movement

        if keys[pygame.K_w]:
            player.y -= speed

        if keys[pygame.K_s]:
            player.y += speed

        if keys[pygame.K_a]:
            player.x -= speed

        if keys[pygame.K_d]:
            player.x += speed

        # Keep inside screen

        player.clamp_ip(
            screen.get_rect()
        )

        # ----------------------------------------------------
        # SHIELD RECHARGE
        # ----------------------------------------------------

        if shield < max_shield:

            shield += 0.12

            shield = min(
                shield,
                max_shield
            )

        # ----------------------------------------------------
        # STARFIELD
        # ----------------------------------------------------

        update_stars()

        # ----------------------------------------------------
        # PLAYER BULLETS
        # ----------------------------------------------------

        for bullet in bullets[:]:

            bullet["rect"].x += 15

            if bullet["rect"].left > WIDTH:

                bullets.remove(
                    bullet
                )

        # ----------------------------------------------------
        # ENEMY SPAWNING
        # ----------------------------------------------------

        spawn_timer += 1

        if spawn_timer >= spawn_delay:

            spawn_enemy()

            spawn_timer = 0

            # Increase difficulty

            if spawn_delay > 30:

                spawn_delay -= 0.5

        # ----------------------------------------------------
        # ASTEROID SPAWNING
        # ----------------------------------------------------

        asteroid_timer += 1

        if asteroid_timer >= 100:

            spawn_asteroid()

            asteroid_timer = 0

        # ----------------------------------------------------
        # ASTEROID MOVEMENT
        # ----------------------------------------------------

        for asteroid in asteroids[:]:

            asteroid["rect"].x -= (
                asteroid["speed"]
            )

            asteroid["rotation"] += 2

            if asteroid["rect"].right < 0:

                asteroids.remove(
                    asteroid
                )

        # ----------------------------------------------------
        # ENEMY AI
        # ----------------------------------------------------

        for enemy in enemies[:]:

            rect = enemy["rect"]

            # Fighter

            if enemy["type"] == "fighter":

                rect.x -= enemy["speed"]

                enemy["phase"] += 0.05

                rect.y += (
                    math.sin(
                        enemy["phase"]
                    ) * 1.5
                )

            # Tank

            elif enemy["type"] == "tank":

                rect.x -= enemy["speed"]

            # Kamikaze

            else:

                rect.x -= enemy["speed"]

                if rect.centery < player.centery:

                    rect.y += 2

                elif rect.centery > player.centery:

                    rect.y -= 2

            # ------------------------------------------------
            # Enemy shooting
            # ------------------------------------------------

            enemy["cooldown"] -= 1

            if enemy["cooldown"] <= 0:

                if enemy["type"] != "kamikaze":

                    enemy_shoot(enemy)

                enemy["cooldown"] = random.randint(
                    70,
                    130
                )

            # ------------------------------------------------
            # Enemy hits player
            # ------------------------------------------------

            if rect.colliderect(player):

                if enemy["type"] == "kamikaze":

                    damage = 35

                elif enemy["type"] == "tank":

                    damage = 25

                else:

                    damage = 15

                damage_player(
                    damage
                )

                explosion(

                    rect.centerx,
                    rect.centery,
                    35
                )

                enemies.remove(
                    enemy
                )

                if hull <= 0:

                    game_active = False

        # ----------------------------------------------------
        # ENEMY BULLETS
        # ----------------------------------------------------

        for bullet in enemy_bullets[:]:

            bullet["rect"].x -= (
                bullet["speed"]
            )

            if bullet["rect"].right < 0:

                enemy_bullets.remove(
                    bullet
                )

                continue

            if bullet["rect"].colliderect(
                player
            ):

                damage_player(
                    bullet["damage"]
                )

                explosion(

                    player.centerx,
                    player.centery,
                    8
                )

                enemy_bullets.remove(
                    bullet
                )

                if hull <= 0:

                    game_active = False

        # ----------------------------------------------------
        # PLAYER BULLET COLLISIONS
        # ----------------------------------------------------

        for bullet in bullets[:]:

            hit = False

            for enemy in enemies[:]:

                if bullet["rect"].colliderect(
                    enemy["rect"]
                ):

                    enemy["health"] -= (
                        bullet["damage"]
                    )

                    hit = True

                    # Enemy destroyed

                    if enemy["health"] <= 0:

                        explosion(

                            enemy["rect"].centerx,
                            enemy["rect"].centery,
                            45
                        )

                        enemies.remove(
                            enemy
                        )

                        if enemy["type"] == "fighter":

                            score += 100
                            credits += 10

                        elif enemy["type"] == "tank":

                            score += 300
                            credits += 35

                        else:

                            score += 150
                            credits += 15

                    break

            if (
                hit
                and bullet in bullets
            ):

                bullets.remove(
                    bullet
                )

        # ----------------------------------------------------
        # ASTEROID COLLISIONS
        # ----------------------------------------------------

        for asteroid in asteroids[:]:

            if asteroid["rect"].colliderect(
                player
            ):

                damage_player(
                    15
                )

                explosion(

                    asteroid["rect"].centerx,
                    asteroid["rect"].centery,
                    25
                )

                asteroids.remove(
                    asteroid
                )

                if hull <= 0:

                    game_active = False

        # ----------------------------------------------------
        # WEAPON UPGRADES
        # ----------------------------------------------------

        if (
            weapon_level < 3
            and credits >= 100
        ):

            weapon_level = 2

        if (
            weapon_level < 3
            and credits >= 300
        ):

            weapon_level = 3

        # ----------------------------------------------------
        # PARTICLES
        # ----------------------------------------------------

        update_particles()

        # ====================================================
        # DRAW EVERYTHING
        # ====================================================

        screen.fill(BLACK)

        # Stars

        draw_stars()

        # Asteroids

        for asteroid in asteroids:

            draw_asteroid(
                asteroid
            )

        # Player lasers

        for bullet in bullets:

            pygame.draw.rect(

                screen,

                CYAN,

                bullet["rect"]
            )

            pygame.draw.rect(

                screen,

                WHITE,

                (
                    bullet["rect"].x + 5,
                    bullet["rect"].y + 1,
                    12,
                    4
                )
            )

        # Enemy lasers

        for bullet in enemy_bullets:

            pygame.draw.rect(

                screen,

                RED,

                bullet["rect"]
            )

        # Enemies

        for enemy in enemies:

            draw_enemy(
                enemy
            )

        # Player

        draw_player()

        # Explosions

        draw_particles()

        # HUD

        draw_hud()

        pygame.display.flip()

    # ========================================================
    # GAME OVER
    # ========================================================

    else:

        game_over_screen()


# ============================================================
# EXIT
# ============================================================

pygame.quit()
sys.exit()