import pygame
import math
import random
import numpy as np

# Initialize Core Game and Audio Engines
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

# Game Window Configuration
WIDTH, HEIGHT = 900, 700
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Realistic Vector-Physics Pac-Man")
CLOCK = pygame.time.Clock()
FPS = 60

# Palette Constants (Neon Cyberpunk Theme)
COLOR_BG = (10, 10, 18)
COLOR_WALL = (0, 102, 255)
COLOR_PACMAN = (255, 238, 0)
COLOR_GHOST = (255, 60, 60)
COLOR_PELLET = (255, 184, 174)

def generate_tone(frequency, duration, volume=0.15, wave_type="square"):
    """Generates pure retro arcade audio arrays directly into system memory."""
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    if wave_type == "square":
        wave = np.sign(np.sin(2 * np.pi * frequency * t))
    else:
        wave = np.sin(2 * np.pi * frequency * t)
        
    audio_buffer = (wave * volume * 32767).astype(np.int16)
    return pygame.mixer.Sound(buffer=audio_buffer)

# Pre-compile Synthesized Wave Audio Channels
SOUND_CHOMP = generate_tone(440, 0.05, volume=0.06, wave_type="square")
SOUND_DEATH = generate_tone(150, 0.4, volume=0.25, wave_type="sine")

class Obstacle:
    """Represents rigid physical structures inside the simulation workspace."""
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, surface):
        # Render clean glowing wall layers
        pygame.draw.rect(surface, COLOR_WALL, self.rect, border_radius=4)
        
        # FIX: Use inflate() with negative numbers to shrink the rectangle inward safely
        inner_rect = self.rect.inflate(-4, -4)
        pygame.draw.rect(surface, (0, 30, 100), inner_rect, border_radius=2)

class PhysicsEntity:
    """Base engineering class using explicit vector Euler integration."""
    def __init__(self, x, y, radius, color):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.acc = pygame.Vector2(0, 0)
        self.radius = radius
        self.color = color
        self.mass = 1.0
        self.friction = 0.88  # Surface momentum dampening multiplier
        self.max_speed = 4.5

    def apply_force(self, force_vector):
        self.acc += force_vector / self.mass

    def update_physics(self, walls):
        # Compute acceleration vectors into current speed
        self.vel += self.acc
        self.vel *= self.friction
        self.acc *= 0  # Reset acceleration accumulator
        
        # Clamp velocity magnitude to prevent terminal clipping instabilities
        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)

        # X-Axis Resolution (Axis-Aligned Bounding Box Collision)
        self.pos.x += self.vel.x
        for wall in walls:
            if self.check_wall_collision(wall):
                if self.vel.x > 0: self.pos.x = wall.rect.left - self.radius
                elif self.vel.x < 0: self.pos.x = wall.rect.right + self.radius
                self.vel.x *= -0.25  # Elastic bounce recoil factor

        # Y-Axis Resolution (Axis-Aligned Bounding Box Collision)
        self.pos.y += self.vel.y
        for wall in walls:
            if self.check_wall_collision(wall):
                if self.vel.y > 0: self.pos.y = wall.rect.top - self.radius
                elif self.vel.y < 0: self.pos.y = wall.rect.bottom + self.radius
                self.vel.y *= -0.25  # Elastic bounce recoil factor

    def check_wall_collision(self, wall):
        """Calculates distance between circle center and closest bounding box point."""
        closest_x = max(wall.rect.left, min(self.pos.x, wall.rect.right))
        closest_y = max(wall.rect.top, min(self.pos.y, wall.rect.bottom))
        distance = math.hypot(self.pos.x - closest_x, self.pos.y - closest_y)
        return distance < self.radius

class Pacman(PhysicsEntity):
    def __init__(self, x, y):
        super().__init__(x, y, radius=18, color=COLOR_PACMAN)
        self.engine_power = 0.65
        self.mouth_angle = 0
        self.mouth_closing = False

    def handle_input(self, keys):
        # Accumulate movement intent forces depending on input layout state
        move_intent = pygame.Vector2(0, 0)
        if keys[pygame.K_UP] or keys[pygame.K_w]:    move_intent.y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:  move_intent.y = 1
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:  move_intent.x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_intent.x = 1

        if move_intent.length() > 0:
            move_intent.normalize_ip()
            self.apply_force(move_intent * self.engine_power)

    def draw(self, surface):
        speed = self.vel.length()
        # Scale mouth animation speed directly based on velocity vector scale
        if speed > 0.2:
            if self.mouth_closing:
                self.mouth_angle -= 4
                if self.mouth_angle <= 5: self.mouth_closing = False
            else:
                self.mouth_angle += 4
                if self.mouth_angle >= 45: self.mouth_closing = True
        
        heading_deg = 0
        if speed > 0.1:
            heading_deg = math.degrees(math.atan2(-self.vel.y, self.vel.x))

        start_rad = math.radians(heading_deg + self.mouth_angle)
        end_rad = math.radians(heading_deg + 360 - self.mouth_angle)
        
        # Build polygon vertices representing the iconic chewing mouth arc
        points = [self.pos]
        num_segments = 24
        for i in range(num_segments + 1):
            angle = start_rad + (end_rad - start_rad) * i / num_segments
            points.append(self.pos + pygame.Vector2(math.cos(angle), -math.sin(angle)) * self.radius)
        
        if len(points) > 2:
            pygame.draw.polygon(surface, self.color, points)

class Ghost(PhysicsEntity):
    def __init__(self, x, y):
        super().__init__(x, y, radius=18, color=COLOR_GHOST)
        self.chase_force = 0.32

    def process_ai(self, target_pos):
        """Applies basic steering force vector pointing directly toward player tracking nodes."""
        direction = target_pos - self.pos
        if direction.length() > 0:
            direction.normalize_ip()
            # Inject microscopic noise variables to break symmetry lock cycles around tight tiles
            direction += pygame.Vector2(random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15))
            self.apply_force(direction * self.chase_force)

    def draw(self, surface):
        # Render rounded core ghost body coordinates
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
        pygame.draw.rect(surface, self.color, (int(self.pos.x - self.radius), int(self.pos.y), self.radius * 2, self.radius))
        
        # Position tracking eyeballs to offset looking toward movement velocity
        eye_offset = pygame.Vector2(0, 0)
        if self.vel.length() > 0.1:
            eye_offset = self.vel.normalize() * 4

        # Render Left and Right visual sockets
        pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x - 7 + eye_offset.x), int(self.pos.y - 2 + eye_offset.y)), 5)
        pygame.draw.circle(surface, (0, 0, 255), (int(self.pos.x - 7 + eye_offset.x * 1.5), int(self.pos.y - 2 + eye_offset.y * 1.5)), 2)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x + 7 + eye_offset.x), int(self.pos.y - 2 + eye_offset.y)), 5)
        pygame.draw.circle(surface, (0, 0, 255), (int(self.pos.x + 7 + eye_offset.x * 1.5), int(self.pos.y - 2 + eye_offset.y * 1.5)), 2)

def main():
    # Construct Arena Colliders (x, y, width, height)
    walls = [
        Obstacle(20, 20, 860, 20), Obstacle(20, 660, 860, 20),
        Obstacle(20, 20, 20, 660), Obstacle(860, 20, 20, 660),
        Obstacle(120, 100, 200, 40), Obstacle(580, 100, 200, 40),
        Obstacle(420, 40, 60, 160), Obstacle(120, 220, 100, 120),
        Obstacle(680, 220, 100, 120), Obstacle(300, 280, 300, 40),
        Obstacle(120, 420, 200, 40), Obstacle(580, 420, 200, 40),
        Obstacle(420, 480, 60, 120),
    ]

    # Instantiate Actor Entities
    player = Pacman(70, 70)
    ghost = Ghost(450, 380)

    # Spawn Consumption Node Elements (Pellets) dynamically in clear corridors
    pellets = []
    for px in range(70, 830, 45):
        for py in range(70, 630, 45):
            test_rect = pygame.Rect(px - 4, py - 4, 8, 8)
            if not any(test_rect.colliderect(wall.rect) for wall in walls):
                pellets.append(pygame.Vector2(px, py))

    score = 0
    running = True
    game_over = False

    # Main Application Loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r:  # Flush scope variables and restart
                    main()
                    return

        if not game_over:
            # Polled Movement Input Handling
            keys = pygame.key.get_pressed()
            player.handle_input(keys)
            ghost.process_ai(player.pos)

            # Frame Physics Integration step
            player.update_physics(walls)
            ghost.update_physics(walls)

            # Evaluate Pellet Proximity Captures
            for i in range(len(pellets) - 1, -1, -1):
                if player.pos.distance_to(pellets[i]) < player.radius + 4:
                    pellets.pop(i)
                    score += 10
                    SOUND_CHOMP.play()

            # Evaluate Enemy Interception Crash Conditions
            if player.pos.distance_to(ghost.pos) < player.radius + ghost.radius:
                game_over = True
                SOUND_DEATH.play()

        # Render Pipeline Stage
        SCREEN.fill(COLOR_BG)
        for wall in walls: wall.draw(SCREEN)
        # Render remaining active game entities
        for pellet in pellets: 
            pygame.draw.circle(SCREEN, COLOR_PELLET, (int(pellet.x), int(pellet.y)), 4)
            
        player.draw(SCREEN)
        ghost.draw(SCREEN)

        # Draw Live Interactive HUD Score Metrics
        font_hud = pygame.font.SysFont("Courier New", 24, bold=True)
        score_text = font_hud.render(f"SCORE: {score:05d}", True, (255, 255, 255))
        SCREEN.blit(score_text, (35, 30))

        # Game Over Interface Overlay Engine
        if game_over:
            # Render translucent background alpha backdrop matrix layer
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 10, 20, 195))
            SCREEN.blit(overlay, (0, 0))

            font_go = pygame.font.SysFont("Courier New", 56, bold=True)
            font_sub = pygame.font.SysFont("Courier New", 22, bold=False)

            text_go = font_go.render("GAME OVER", True, (255, 50, 50))
            text_score = font_sub.render(f"FINAL SCORE: {score}", True, (255, 255, 255))
            text_restart = font_sub.render("PRESS [R] TO REBOOT ENVIRONMENT", True, (0, 255, 200))

            # Render text layouts into absolute screen center anchors
            SCREEN.blit(text_go, (WIDTH // 2 - text_go.get_width() // 2, HEIGHT // 2 - 60))
            SCREEN.blit(text_score, (WIDTH // 2 - text_score.get_width() // 2, HEIGHT // 2 + 10))
            SCREEN.blit(text_restart, (WIDTH // 2 - text_restart.get_width() // 2, HEIGHT // 2 + 50))

        pygame.display.flip()
        CLOCK.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
