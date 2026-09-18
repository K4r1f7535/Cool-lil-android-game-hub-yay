"""
main1234.py - Cool-lil-android-game-hub-yay

Everything lives in this one file:
  * the main menu
  * Snake II
  * 2048 Retro
  * Temple Runner 2D
  * Flappy Bounce
  * Space Blaster
  * Brick Breaker

HOW TO RUN ON DESKTOP:      python3 main1234.py
CONTROLS ON DESKTOP:        arrow keys (or WASD), SPACE/ENTER = select, ESC = back
CONTROLS ON PHONE:          tap the on-screen buttons, or swipe
"""
import json
import os
import random

import pygame

# =====================================================================
# 1. SETTINGS AND COLORS
# =====================================================================
W, H = 360, 640

BLACK = (12, 12, 24)
NAVY = (26, 28, 60)
PINK = (255, 90, 160)
RED = (230, 60, 70)
ORANGE = (255, 150, 50)
YELLOW = (255, 225, 80)
GREEN = (70, 220, 110)
DKGREEN = (30, 140, 70)
CYAN = (70, 220, 230)
BLUE = (60, 110, 230)
PURPLE = (120, 70, 170)
WHITE = (240, 240, 250)
GREY = (120, 120, 150)
DKGREY = (55, 55, 85)

UP, DOWN, LEFT, RIGHT, ACTION, BACK = "up", "down", "left", "right", "action", "back"

BACK_KEYS = {pygame.K_ESCAPE, pygame.K_BACKSPACE}
if hasattr(pygame, "K_AC_BACK"):
    BACK_KEYS.add(pygame.K_AC_BACK)

FOCUS_LOST = getattr(pygame, "WINDOWFOCUSLOST", -1)


# =====================================================================
# 2. DRAWING HELPERS (text, buttons, on-screen D-pad)
# =====================================================================
_fonts = {}


def get_font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def draw_text(surf, text, size, color, center=None, topleft=None):
    """Draw pixel-style text (no smoothing = crunchy retro look)."""
    f = get_font(size)
    img = f.render(str(text), False, color)
    rect = img.get_rect()
    if center:
        rect.center = center
    elif topleft:
        rect.topleft = topleft
    shadow = f.render(str(text), False, BLACK)
    surf.blit(shadow, (rect.x + 2, rect.y + 2))
    surf.blit(img, rect)
    return rect


def draw_button(surf, rect, label, color=BLUE, size=30):
    """A chunky retro button with a little 3D edge."""
    pygame.draw.rect(surf, BLACK, rect.move(3, 4))
    pygame.draw.rect(surf, color, rect)
    pygame.draw.rect(surf, WHITE, rect, 2)
    pygame.draw.line(surf, WHITE, (rect.x + 4, rect.y + 4), (rect.right - 5, rect.y + 4))
    draw_text(surf, label, size, WHITE, center=rect.center)


def draw_scanlines(surf):
    """Faint CRT lines for the retro feel."""
    line = pygame.Surface((W, 1), pygame.SRCALPHA)
    line.fill((0, 0, 0, 40))
    for y in range(0, H, 3):
        surf.blit(line, (0, y))


# ---- The on-screen D-pad -------------------------------------------
BTN = 46
PAD_CX, PAD_CY = W // 2, 560


def _make_dpad():
    return {
        UP:    pygame.Rect(PAD_CX - BTN // 2, PAD_CY - BTN - BTN // 2 - 2, BTN, BTN),
        DOWN:  pygame.Rect(PAD_CX - BTN // 2, PAD_CY + BTN // 2 + 2, BTN, BTN),
        LEFT:  pygame.Rect(PAD_CX - BTN - BTN // 2 - 2, PAD_CY - BTN // 2, BTN, BTN),
        RIGHT: pygame.Rect(PAD_CX + BTN // 2 + 2, PAD_CY - BTN // 2, BTN, BTN),
    }


DPAD = _make_dpad()
ARROWS = {UP: "^", DOWN: "v", LEFT: "<", RIGHT: ">"}
A_BUTTON = pygame.Rect(W - 96, PAD_CY - 28, 76, 56)
BACK_BUTTON = pygame.Rect(W - 78, 8, 68, 30)
FLAP_BUTTON = pygame.Rect(40, PAD_CY - 46, W - 80, 92)


def draw_controls(surf, show_dpad=True, show_a=False, a_label="A", held=None):
    held = held or set()
    if show_dpad:
        for d, rect in DPAD.items():
            draw_button(surf, rect, ARROWS[d], color=(90, 90, 130) if d in held else DKGREY, size=34)
    if show_a:
        draw_button(surf, A_BUTTON, a_label, color=RED, size=26)
    draw_button(surf, BACK_BUTTON, "MENU", color=DKGREY, size=22)


# =====================================================================
# 3. HIGH SCORES
# =====================================================================
def _score_file():
    base = os.environ.get("ANDROID_PRIVATE") or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "highscores.json")


def get_high(key):
    try:
        with open(_score_file()) as fh:
            return int(json.load(fh).get(key, 0))
    except (OSError, ValueError):
        return 0


def submit_score(key, score):
    try:
        with open(_score_file()) as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        data = {}
    if score > int(data.get(key, 0)):
        data[key] = int(score)
        try:
            with open(_score_file(), "w") as fh:
                json.dump(data, fh)
        except OSError:
            pass
        return True
    return False


# =====================================================================
# 4. INPUT
# =====================================================================
class Input:
    SWIPE_MIN = 28

    def __init__(self):
        self.actions = []
        self.tap_pos = None
        self.dpad_active = False
        self.held = set()
        self.keys_held = set()
        self.down_pos = None
        self.swiped = False

    def begin_frame(self):
        self.actions = []
        self.tap_pos = None

    @property
    def down_held(self):
        return DOWN in self.held or DOWN in self.keys_held

    def handle(self, event, to_virtual):
        if event.type == pygame.KEYDOWN:
            k = event.key
            if k in (pygame.K_UP, pygame.K_w):
                self.actions.append(UP)
                self.keys_held.add(UP)
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.actions.append(DOWN)
                self.keys_held.add(DOWN)
            elif k in (pygame.K_LEFT, pygame.K_a):
                self.actions.append(LEFT)
                self.keys_held.add(LEFT)
            elif k in (pygame.K_RIGHT, pygame.K_d):
                self.actions.append(RIGHT)
                self.keys_held.add(RIGHT)
            elif k in (pygame.K_SPACE, pygame.K_RETURN):
                self.actions.append(ACTION)
            elif k in BACK_KEYS:
                self.actions.append(BACK)

        elif event.type == pygame.KEYUP:
            k = event.key
            for keys, name in (((pygame.K_UP, pygame.K_w), UP), ((pygame.K_DOWN, pygame.K_s), DOWN),
                               ((pygame.K_LEFT, pygame.K_a), LEFT), ((pygame.K_RIGHT, pygame.K_d), RIGHT)):
                if k in keys:
                    self.keys_held.discard(name)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = to_virtual(event.pos)
            self.down_pos = pos
            self.swiped = False
            for d, rect in (DPAD.items() if self.dpad_active else ()):
                if rect.inflate(14, 14).collidepoint(pos):
                    self.actions.append(d)
                    self.held.add(d)
                    self.down_pos = None

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.held.clear()
            if self.down_pos is not None:
                up = to_virtual(event.pos)
                dx, dy = up[0] - self.down_pos[0], up[1] - self.down_pos[1]
                if max(abs(dx), abs(dy)) < self.SWIPE_MIN:
                    self.tap_pos = up
                elif abs(dx) > abs(dy):
                    self.actions.append(RIGHT if dx > 0 else LEFT)
                else:
                    self.actions.append(DOWN if dy > 0 else UP)
            self.down_pos = None

        elif event.type == FOCUS_LOST:
            self.held.clear()
            self.keys_held.clear()


# =====================================================================
# 5. GAME BASE CLASS
# =====================================================================
class Game:
    TITLE = "GAME"
    COLOR = BLUE
    KEY = "game"
    USES_DPAD = True

    def __init__(self):
        self.done = False
        self.reset()

    def reset(self):
        pass

    def handle_input(self, inp):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass

    def check_back(self, inp):
        if BACK in inp.actions:
            self.done = True
            return True
        if inp.tap_pos and BACK_BUTTON.collidepoint(inp.tap_pos):
            self.done = True
            return True
        return False

    def draw_game_over(self, surf, score, record, extra=""):
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        surf.blit(dim, (0, 0))
        draw_text(surf, "GAME OVER", 56, RED, center=(W // 2, 200))
        draw_text(surf, f"SCORE {score}", 36, WHITE, center=(W // 2, 262))
        if record:
            draw_text(surf, "NEW RECORD!", 34, YELLOW, center=(W // 2, 300))
        if extra:
            draw_text(surf, extra, 24, GREY, center=(W // 2, 336))
        draw_text(surf, "TAP OR PRESS SPACE", 28, CYAN, center=(W // 2, 390))
        draw_text(surf, "TO PLAY AGAIN", 28, CYAN, center=(W // 2, 416))


# =====================================================================
# 6. GAME #1 - SNAKE II
# =====================================================================
class Snake(Game):
    TITLE = "SNAKE II"
    COLOR = DKGREEN
    KEY = "snake"

    CELL = 20
    COLS = W // CELL
    ROWS = 20
    TOP = 50

    START_DELAY = 0.20
    MIN_DELAY = 0.06
    SPEEDUP = 0.006

    VECTOR = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}
    OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

    def reset(self):
        cx, cy = self.COLS // 2, self.ROWS // 2
        self.body = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = RIGHT
        self.queue = []
        self.delay = self.START_DELAY
        self.timer = 0.0
        self.score = 0
        self.alive = True
        self.new_record = False
        self.high = get_high(self.KEY)
        self.place_food()

    def place_food(self):
        free = [(x, y) for x in range(self.COLS) for y in range(self.ROWS)
                if (x, y) not in self.body]
        self.food = random.choice(free) if free else None

    def queue_turn(self, d):
        last = self.queue[-1] if self.queue else self.direction
        if d != last and d != self.OPPOSITE[last] and len(self.queue) < 3:
            self.queue.append(d)

    def handle_input(self, inp):
        if self.check_back(inp):
            return
        if not self.alive:
            if ACTION in inp.actions or inp.tap_pos:
                self.reset()
            return
        for a in inp.actions:
            if a in self.VECTOR:
                self.queue_turn(a)

    def update(self, dt):
        if not self.alive:
            return
        self.timer += dt
        while self.timer >= self.delay and self.alive:
            self.timer -= self.delay
            self.step()

    def step(self):
        if self.queue:
            self.direction = self.queue.pop(0)
        dx, dy = self.VECTOR[self.direction]
        hx, hy = self.body[0]
        new = (hx + dx, hy + dy)

        hit_wall = not (0 <= new[0] < self.COLS and 0 <= new[1] < self.ROWS)
        if hit_wall or new in self.body[:-1]:
            self.alive = False
            self.new_record = submit_score(self.KEY, self.score)
            self.high = get_high(self.KEY)
            return

        self.body.insert(0, new)
        if new == self.food:
            self.score += 10
            self.delay = max(self.MIN_DELAY, self.delay - self.SPEEDUP)
            self.place_food()
        else:
            self.body.pop()

    def draw(self, surf):
        surf.fill(BLACK)
        draw_text(surf, f"SCORE {self.score}", 28, WHITE, topleft=(10, 12))
        draw_text(surf, f"HI {max(self.high, self.score)}", 28, YELLOW, topleft=(10, 32))

        c = self.CELL
        field = pygame.Rect(0, self.TOP, W, self.ROWS * c)
        pygame.draw.rect(surf, NAVY, field)
        for x in range(self.COLS):
            for y in range(self.ROWS):
                if (x + y) % 2 == 0:
                    pygame.draw.rect(surf, (32, 34, 72), (x * c, self.TOP + y * c, c, c))
        pygame.draw.rect(surf, WHITE, field, 2)

        if self.food:
            fx, fy = self.food
            r = pygame.Rect(fx * c + 3, self.TOP + fy * c + 3, c - 6, c - 6)
            pygame.draw.rect(surf, RED, r)
            pygame.draw.rect(surf, YELLOW, (r.x + 2, r.y + 2, 4, 4))

        for i, (x, y) in enumerate(self.body):
            r = pygame.Rect(x * c + 1, self.TOP + y * c + 1, c - 2, c - 2)
            pygame.draw.rect(surf, GREEN if i else YELLOW, r)
            if i == 0:
                pygame.draw.rect(surf, BLACK, (r.x + 4, r.y + 4, 4, 4))
                pygame.draw.rect(surf, BLACK, (r.right - 8, r.y + 4, 4, 4))

        draw_controls(surf, show_dpad=True)
        if not self.alive:
            self.draw_game_over(surf, self.score, self.new_record)


# =====================================================================
# 7. GAME #2 - 2048 RETRO
# =====================================================================
class Game2048(Game):
    TITLE = "2048 RETRO"
    COLOR = ORANGE
    KEY = "2048"

    SIZE = 4
    CELL = 76
    GAP = 6
    BOARD_X = (W - (4 * 76 + 5 * 6)) // 2
    BOARD_Y = 130
    SLIDE_TIME = 0.10

    TILE_COLORS = {
        0: (44, 46, 82), 2: (238, 228, 218), 4: (237, 224, 200), 8: (242, 177, 121),
        16: (245, 149, 99), 32: (246, 124, 95), 64: (246, 94, 59), 128: (237, 207, 114),
        256: (237, 204, 97), 512: (237, 200, 80), 1024: (237, 197, 63), 2048: (237, 194, 46),
    }

    def reset(self):
        self.grid = [[0] * self.SIZE for _ in range(self.SIZE)]
        self.score = 0
        self.won = False
        self.over = False
        self.new_record = False
        self.high = get_high(self.KEY)
        self.anim = []
        self.anim_t = 0.0
        self.pop = {}
        self.add_tile()
        self.add_tile()

    def add_tile(self):
        empty = [(r, c) for r in range(self.SIZE) for c in range(self.SIZE) if self.grid[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            self.grid[r][c] = 4 if random.random() < 0.1 else 2
            self.pop[(r, c)] = 0.15

    @staticmethod
    def slide_line(line):
        items = [(i, v) for i, v in enumerate(line) if v]
        result, moves, points = [], [], 0
        i = 0
        while i < len(items):
            idx, val = items[i]
            if i + 1 < len(items) and items[i + 1][1] == val:
                merged = val * 2
                points += merged
                moves.append((idx, len(result), val))
                moves.append((items[i + 1][0], len(result), val))
                result.append(merged)
                i += 2
            else:
                moves.append((idx, len(result), val))
                result.append(val)
                i += 1
        result += [0] * (len(line) - len(result))
        return result, points, moves

    def move(self, direction):
        if self.anim:
            self.finish_anim()
        n = self.SIZE
        new_grid = [[0] * n for _ in range(n)]
        gained = 0
        anim = []
        for k in range(n):
            if direction == LEFT:
                coords = [(k, j) for j in range(n)]
            elif direction == RIGHT:
                coords = [(k, j) for j in reversed(range(n))]
            elif direction == UP:
                coords = [(j, k) for j in range(n)]
            else:
                coords = [(j, k) for j in reversed(range(n))]
            line = [self.grid[r][c] for r, c in coords]
            new_line, pts, moves = self.slide_line(line)
            gained += pts
            for j, v in enumerate(new_line):
                r, c = coords[j]
                new_grid[r][c] = v
            for a, b, val in moves:
                anim.append((coords[a], coords[b], val))

        if new_grid == self.grid:
            return False
        self.grid = new_grid
        self.score += gained
        self.anim = anim
        self.anim_t = 0.0
        self.pending_spawn = True
        return True

    def finish_anim(self):
        self.anim = []
        if getattr(self, "pending_spawn", False):
            self.pending_spawn = False
            self.add_tile()
            self.check_end()

    def can_move(self):
        n = self.SIZE
        for r in range(n):
            for c in range(n):
                if self.grid[r][c] == 0:
                    return True
                if c + 1 < n and self.grid[r][c] == self.grid[r][c + 1]:
                    return True
                if r + 1 < n and self.grid[r][c] == self.grid[r + 1][c]:
                    return True
        return False

    def check_end(self):
        if any(2048 in row for row in self.grid):
            self.won = True
        if not self.can_move():
            self.over = True
            self.new_record = submit_score(self.KEY, self.score)
            self.high = get_high(self.KEY)

    def handle_input(self, inp):
        if self.check_back(inp):
            return
        if self.over:
            if ACTION in inp.actions or inp.tap_pos:
                self.reset()
            return
        for a in inp.actions:
            if a in (UP, DOWN, LEFT, RIGHT):
                if self.move(a):
                    break

    def update(self, dt):
        for key in list(self.pop):
            self.pop[key] -= dt
            if self.pop[key] <= 0:
                del self.pop[key]
        if self.anim:
            self.anim_t += dt
            if self.anim_t >= self.SLIDE_TIME:
                self.finish_anim()

    def cell_xy(self, r, c):
        return (self.BOARD_X + self.GAP + c * (self.CELL + self.GAP),
                self.BOARD_Y + self.GAP + r * (self.CELL + self.GAP))

    def draw_tile(self, surf, x, y, value, scale=1.0):
        color = self.TILE_COLORS.get(value, (60, 58, 50))
        size = int(self.CELL * scale)
        off = (self.CELL - size) // 2
        rect = pygame.Rect(x + off, y + off, size, size)
        pygame.draw.rect(surf, color, rect)
        if value:
            pygame.draw.rect(surf, WHITE, rect, 1)
            txt_color = BLACK if value <= 4 else WHITE
            fsize = 44 if value < 100 else 34 if value < 1000 else 26
            f = get_font(fsize).render(str(value), False, txt_color)
            surf.blit(f, f.get_rect(center=rect.center))

    def draw(self, surf):
        surf.fill(BLACK)
        draw_text(surf, "2048", 48, YELLOW, topleft=(14, 12))
        draw_text(surf, f"SCORE {self.score}", 26, WHITE, topleft=(14, 60))
        draw_text(surf, f"HI {max(self.high, self.score)}", 26, YELLOW, topleft=(14, 84))

        bw = 4 * self.CELL + 5 * self.GAP
        board = pygame.Rect(self.BOARD_X, self.BOARD_Y, bw, bw)
        pygame.draw.rect(surf, DKGREY, board)
        pygame.draw.rect(surf, WHITE, board, 2)

        for r in range(self.SIZE):
            for c in range(self.SIZE):
                x, y = self.cell_xy(r, c)
                self.draw_tile(surf, x, y, 0)

        if self.anim:
            t = min(1.0, self.anim_t / self.SLIDE_TIME)
            t = 1 - (1 - t) * (1 - t)
            for (r0, c0), (r1, c1), val in self.anim:
                x0, y0 = self.cell_xy(r0, c0)
                x1, y1 = self.cell_xy(r1, c1)
                self.draw_tile(surf, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, val)
        else:
            for r in range(self.SIZE):
                for c in range(self.SIZE):
                    v = self.grid[r][c]
                    if v:
                        x, y = self.cell_xy(r, c)
                        scale = 1.0
                        if (r, c) in self.pop:
                            scale = 1.0 - self.pop[(r, c)] / 0.15 * 0.6
                        self.draw_tile(surf, x, y, v, scale)

        if self.won and not self.over:
            draw_text(surf, "YOU MADE 2048!", 26, YELLOW, center=(W - 100, 60))
        draw_text(surf, "swipe or use buttons", 20, GREY, center=(W // 2, 478))
        draw_controls(surf, show_dpad=True)
        if self.over:
            self.draw_game_over(surf, self.score, self.new_record)


# =====================================================================
# 8. GAME #3 - TEMPLE RUNNER 2D
# =====================================================================
class Runner(Game):
    TITLE = "TEMPLE RUNNER"
    COLOR = PURPLE
    KEY = "runner"

    GROUND_Y = 400
    PLAYER_X = 70
    STAND_H, DUCK_H, PLAYER_W = 44, 22, 28
    GRAVITY = 1900.0
    JUMP_SPEED = -640.0

    def reset(self):
        self.py = float(self.GROUND_Y - self.STAND_H)
        self.vy = 0.0
        self.on_ground = True
        self.ducking = False
        self.duck_timer = 0.0
        self.speed = 240.0
        self.distance = 0.0
        self.obstacles = []
        self.spawn_in = 1.0
        self.scroll = 0.0
        self.alive = True
        self.new_record = False
        self.high = get_high(self.KEY)
        self.stars = [(random.randint(0, W), random.randint(20, 300)) for _ in range(28)]

    @property
    def score(self):
        return int(self.distance / 10)

    def handle_input(self, inp):
        if self.check_back(inp):
            return
        if not self.alive:
            if ACTION in inp.actions or inp.tap_pos:
                self.reset()
            return
        for a in inp.actions:
            if a in (UP, ACTION):
                if self.on_ground:
                    self.vy = self.JUMP_SPEED
                    self.on_ground = False
            elif a == DOWN:
                self.duck_timer = 0.55
        if inp.tap_pos and inp.tap_pos[1] < 470 and self.on_ground:
            self.vy = self.JUMP_SPEED
            self.on_ground = False
        if inp.tap_pos and A_BUTTON.collidepoint(inp.tap_pos) and self.on_ground:
            self.vy = self.JUMP_SPEED
            self.on_ground = False
        self.holding_down = inp.down_held

    def player_rect(self):
        h = self.DUCK_H if self.ducking else self.STAND_H
        top = self.py if not self.ducking else self.GROUND_Y - h if self.on_ground else self.py
        return pygame.Rect(self.PLAYER_X, int(top), self.PLAYER_W, h)

    def update(self, dt):
        if not self.alive:
            return

        self.duck_timer = max(0.0, self.duck_timer - dt)
        self.ducking = (getattr(self, "holding_down", False) or self.duck_timer > 0) and self.on_ground

        if not self.on_ground:
            self.vy += self.GRAVITY * dt
            self.py += self.vy * dt
            floor = self.GROUND_Y - self.STAND_H
            if self.py >= floor:
                self.py = float(floor)
                self.vy = 0.0
                self.on_ground = True

        self.speed = min(560.0, self.speed + 6.0 * dt)
        self.distance += self.speed * dt
        self.scroll = (self.scroll + self.speed * dt) % 40

        self.spawn_in -= dt
        if self.spawn_in <= 0:
            if random.random() < 0.55:
                h = random.choice((26, 34, 42))
                self.obstacles.append(dict(kind="rock", x=W + 20, y=self.GROUND_Y - h, w=26, h=h))
            else:
                self.obstacles.append(dict(kind="branch", x=W + 20, y=self.GROUND_Y - 62, w=44, h=26))
            gap = random.uniform(0.9, 1.6) * (300.0 / self.speed) * 1.25
            self.spawn_in = max(0.55, gap)

        for ob in self.obstacles:
            ob["x"] -= self.speed * dt
        self.obstacles = [o for o in self.obstacles if o["x"] > -60]

        me = self.player_rect().inflate(-6, -4)
        for ob in self.obstacles:
            if me.colliderect(pygame.Rect(int(ob["x"]), ob["y"], ob["w"], ob["h"]).inflate(-4, -2)):
                self.alive = False
                self.new_record = submit_score(self.KEY, self.score)
                self.high = get_high(self.KEY)
                break

    def draw(self, surf):
        surf.fill((28, 22, 52))
        for (sx, sy) in self.stars:
            pygame.draw.rect(surf, (200, 200, 230), (sx, sy, 2, 2))
        for i in range(4):
            bx = (i * 120 - int(self.distance * 0.1)) % (W + 120) - 60
            pygame.draw.rect(surf, (44, 36, 78), (bx, self.GROUND_Y - 70, 70, 70))
            pygame.draw.rect(surf, (44, 36, 78), (bx + 12, self.GROUND_Y - 96, 46, 26))

        pygame.draw.rect(surf, (90, 60, 40), (0, self.GROUND_Y, W, 90))
        pygame.draw.line(surf, ORANGE, (0, self.GROUND_Y), (W, self.GROUND_Y), 3)
        for x in range(-40, W + 40, 40):
            pygame.draw.rect(surf, (70, 46, 30), (x - int(self.scroll), self.GROUND_Y + 14, 20, 6))

        for ob in self.obstacles:
            r = pygame.Rect(int(ob["x"]), ob["y"], ob["w"], ob["h"])
            if ob["kind"] == "rock":
                pygame.draw.rect(surf, (150, 150, 170), r)
                pygame.draw.rect(surf, WHITE, r, 2)
            else:
                pygame.draw.rect(surf, DKGREEN, r)
                pygame.draw.rect(surf, GREEN, r, 2)
                pygame.draw.rect(surf, (110, 70, 40), (r.centerx - 3, r.bottom, 6, 30))

        p = self.player_rect()
        pygame.draw.rect(surf, ORANGE, p)
        pygame.draw.rect(surf, WHITE, p, 2)
        pygame.draw.rect(surf, BLACK, (p.right - 10, p.y + 5, 4, 4))
        pygame.draw.rect(surf, YELLOW, (p.x, p.y - 5, p.w, 6))

        draw_text(surf, f"DIST {self.score}", 28, WHITE, topleft=(10, 12))
        draw_text(surf, f"HI {max(self.high, self.score)}", 28, YELLOW, topleft=(10, 34))
        draw_text(surf, "tap/A/UP = jump    DOWN = duck", 20, GREY, center=(W // 2, 468))

        draw_controls(surf, show_dpad=True, show_a=True, a_label="JUMP")
        if not self.alive:
            self.draw_game_over(surf, self.score, self.new_record)


# =====================================================================
# 9. GAME #4 - FLAPPY / BOUNCE MINI
# =====================================================================
class Flappy(Game):
    TITLE = "FLAPPY BOUNCE"
    COLOR = (40, 150, 170)
    KEY = "flappy"
    USES_DPAD = False

    GRAVITY = 1500.0
    FLAP_SPEED = -430.0
    PIPE_W = 54
    GAP_START = 170
    GAP_MIN = 120
    GROUND_Y = 470
    BIRD_X = 90
    BIRD_R = 13

    def reset(self):
        self.by = 260.0
        self.vy = 0.0
        self.started = False
        self.alive = True
        self.pipes = []
        self.score = 0
        self.speed = 130.0
        self.time = 0.0
        self.scroll = 0.0
        self.spawn_x = W + 40
        self.new_record = False
        self.high = get_high(self.KEY)
        self.clouds = [(random.randint(0, W), random.randint(40, 300), random.randint(30, 60))
                       for _ in range(5)]
        self.make_pipe(W + 60)
        self.make_pipe(W + 60 + 190)

    MAX_STEP = 110

    def make_pipe(self, x):
        gap = max(self.GAP_MIN, self.GAP_START - self.score * 2)
        moving = self.score >= 5 and random.random() < 0.5
        amp = random.randint(18, 30) if moving else 0

        lo = int(gap / 2) + 60 + amp
        hi = self.GROUND_Y - int(gap / 2) - 40 - amp
        if self.pipes:
            prev = self.pipes[-1]["base"]
            reach = self.MAX_STEP - amp - self.pipes[-1]["amp"]
            lo = max(lo, int(prev - max(40, reach)))
            hi = min(hi, int(prev + max(40, reach)))
        if lo > hi:
            lo = hi = int((lo + hi) / 2)
        centre = random.randint(lo, hi)
        self.pipes.append(dict(x=float(x), base=float(centre), gap=float(gap),
                               amp=amp, phase=random.uniform(0, 6.28), passed=False))

    def gap_centre(self, pipe):
        if pipe["amp"] == 0:
            return pipe["base"]
        lo = pipe["gap"] / 2 + 20
        hi = self.GROUND_Y - pipe["gap"] / 2 - 20
        y = pipe["base"] + pipe["amp"] * pygame.math.Vector2(0, 1).rotate(
            (self.time * 90 + pipe["phase"] * 57.3)).y
        return max(lo, min(hi, y))

    def flap(self):
        self.started = True
        self.vy = self.FLAP_SPEED

    def handle_input(self, inp):
        if self.check_back(inp):
            return
        if not self.alive:
            if ACTION in inp.actions or inp.tap_pos:
                self.reset()
            return
        for a in inp.actions:
            if a in (UP, ACTION):
                self.flap()
        if inp.tap_pos and not BACK_BUTTON.collidepoint(inp.tap_pos):
            self.flap()

    def die(self):
        self.alive = False
        self.new_record = submit_score(self.KEY, self.score)
        self.high = get_high(self.KEY)

    def bird_rect(self):
        r = self.BIRD_R
        return pygame.Rect(int(self.BIRD_X - r + 3), int(self.by - r + 3), 2 * r - 6, 2 * r - 6)

    def update(self, dt):
        if not self.alive:
            return
        self.time += dt
        self.scroll = (self.scroll + self.speed * dt) % 24

        if not self.started:
            self.by = 260 + 8 * pygame.math.Vector2(0, 1).rotate(self.time * 300).y
            return

        self.vy += self.GRAVITY * dt
        self.by += self.vy * dt

        self.speed = min(200.0, 130.0 + self.score * 2.5)

        for pipe in self.pipes:
            pipe["x"] -= self.speed * dt
            if not pipe["passed"] and pipe["x"] + self.PIPE_W < self.BIRD_X - self.BIRD_R:
                pipe["passed"] = True
                self.score += 1
        self.pipes = [p for p in self.pipes if p["x"] > -self.PIPE_W - 10]
        if not self.pipes or self.pipes[-1]["x"] < W - 190:
            self.make_pipe(self.pipes[-1]["x"] + 190 if self.pipes else W + 40)

        if self.by + self.BIRD_R >= self.GROUND_Y or self.by - self.BIRD_R <= 0:
            self.die()
            return
        me = self.bird_rect()
        for pipe in self.pipes:
            cy = self.gap_centre(pipe)
            top = pygame.Rect(int(pipe["x"]), 0, self.PIPE_W, int(cy - pipe["gap"] / 2))
            bottom = pygame.Rect(int(pipe["x"]), int(cy + pipe["gap"] / 2),
                                 self.PIPE_W, self.GROUND_Y - int(cy + pipe["gap"] / 2))
            if me.colliderect(top) or me.colliderect(bottom):
                self.die()
                return

    def draw_pipe_part(self, surf, rect, cap_at_bottom):
        if rect.height <= 0:
            return
        pygame.draw.rect(surf, DKGREEN, rect)
        pygame.draw.rect(surf, GREEN, (rect.x + 4, rect.y, 8, rect.height))
        pygame.draw.rect(surf, BLACK, rect, 2)
        cap = pygame.Rect(rect.x - 4, rect.bottom - 16 if cap_at_bottom else rect.y, rect.w + 8, 16)
        pygame.draw.rect(surf, GREEN, cap)
        pygame.draw.rect(surf, BLACK, cap, 2)

    def draw(self, surf):
        surf.fill((88, 190, 230))
        for (cx, cy, cw) in self.clouds:
            pygame.draw.rect(surf, (235, 245, 255), (cx, cy, cw, 14))
            pygame.draw.rect(surf, (235, 245, 255), (cx + 8, cy - 8, cw - 16, 10))

        for pipe in self.pipes:
            cy = self.gap_centre(pipe)
            top = pygame.Rect(int(pipe["x"]), 0, self.PIPE_W, int(cy - pipe["gap"] / 2))
            bottom = pygame.Rect(int(pipe["x"]), int(cy + pipe["gap"] / 2),
                                 self.PIPE_W, self.GROUND_Y - int(cy + pipe["gap"] / 2))
            self.draw_pipe_part(surf, top, cap_at_bottom=True)
            self.draw_pipe_part(surf, bottom, cap_at_bottom=False)

        pygame.draw.rect(surf, (222, 200, 130), (0, self.GROUND_Y, W, H - self.GROUND_Y))
        pygame.draw.line(surf, (90, 160, 60), (0, self.GROUND_Y), (W, self.GROUND_Y), 6)
        for x in range(-24, W + 24, 24):
            pygame.draw.rect(surf, (200, 176, 105), (x - int(self.scroll), self.GROUND_Y + 12, 12, 6))

        tilt = max(-1.0, min(1.0, self.vy / 500.0))
        bx, by = self.BIRD_X, int(self.by)
        pygame.draw.rect(surf, YELLOW, (bx - 13, by - 10, 26, 20))
        pygame.draw.rect(surf, BLACK, (bx - 13, by - 10, 26, 20), 2)
        pygame.draw.rect(surf, WHITE, (bx + 3, by - 8, 9, 9))
        pygame.draw.rect(surf, BLACK, (bx + 8, by - 6, 4, 4))
        pygame.draw.rect(surf, ORANGE, (bx + 12, by - 1 + int(tilt * 3), 9, 6))
        wing = -4 if int(self.time * 12) % 2 == 0 else 3
        pygame.draw.rect(surf, ORANGE, (bx - 12, by + wing, 12, 7))

        draw_text(surf, f"{self.score}", 64, WHITE, center=(W // 2, 70))
        draw_text(surf, f"HI {max(self.high, self.score)}", 24, YELLOW, topleft=(10, 12))

        if not self.started and self.alive:
            draw_text(surf, "TAP / SPACE TO FLAP", 28, WHITE, center=(W // 2, 190))
        draw_text(surf, "tap anywhere to flap", 22, (90, 60, 30), center=(W // 2, 500))

        draw_controls(surf, show_dpad=False, show_a=False)
        draw_button(surf, FLAP_BUTTON, "FLAP", color=RED, size=40)
        if not self.alive:
            self.draw_game_over(surf, self.score, self.new_record)


# =====================================================================
# 10. GAME #5 - SPACE BLASTER
# =====================================================================
class SpaceBlaster(Game):
    TITLE = "SPACE BLASTER"
    COLOR = CYAN
    KEY = "blaster"
    USES_DPAD = True

    def reset(self):
        self.px = W // 2 - 15
        self.pw, self.ph = 30, 20
        self.py = 430
        self.bullets = []
        self.enemies = []
        self.score = 0
        self.alive = True
        self.shoot_cooldown = 0.0
        self.spawn_timer = 0.0
        self.new_record = False
        self.high = get_high(self.KEY)

    def handle_input(self, inp):
        if self.check_back(inp):
            return
        if not self.alive:
            if ACTION in inp.actions or inp.tap_pos:
                self.reset()
            return

        if LEFT in inp.actions or LEFT in inp.held:
            self.px -= 6
        if RIGHT in inp.actions or RIGHT in inp.held:
            self.px += 6
        self.px = max(10, min(W - 10 - self.pw, self.px))

        shooting = UP in inp.actions or ACTION in inp.actions
        if inp.tap_pos and A_BUTTON.collidepoint(inp.tap_pos):
            shooting = True

        if shooting and self.shoot_cooldown <= 0:
            self.bullets.append({"x": self.px + self.pw // 2 - 2, "y": self.py})
            self.shoot_cooldown = 0.18

    def update(self, dt):
        if not self.alive:
            return

        self.shoot_cooldown -= dt
        self.spawn_timer -= dt

        if self.spawn_timer <= 0:
            self.enemies.append({
                "x": float(random.randint(20, W - 44)),
                "y": 50.0,
                "speed": random.uniform(90.0, 160.0)
            })
            self.spawn_timer = max(0.35, 1.3 - (self.score / 150))

        for b in self.bullets:
            b["y"] -= 380 * dt
        self.bullets = [b for b in self.bullets if b["y"] > 0]

        p_rect = pygame.Rect(self.px, self.py, self.pw, self.ph)
        for e in self.enemies:
            e["y"] += e["speed"] * dt
            e_rect = pygame.Rect(int(e["x"]), int(e["y"]), 24, 20)
            if e_rect.colliderect(p_rect) or e["y"] > 450:
                self.alive = False
                self.new_record = submit_score(self.KEY, self.score)
                self.high = get_high(self.KEY)
                return

        for b in self.bullets[:]:
            b_rect = pygame.Rect(int(b["x"]), int(b["y"]), 4, 10)
            for e in self.enemies[:]:
                e_rect = pygame.Rect(int(e["x"]), int(e["y"]), 24, 20)
                if b_rect.colliderect(e_rect):
                    if b in self.bullets:
                        self.bullets.remove(b)
                    if e in self.enemies:
                        self.enemies.remove(e)
                    self.score += 10
                    break

    def draw(self, surf):
        surf.fill(BLACK)
        draw_text(surf, f"SCORE {self.score}", 28, WHITE, topleft=(10, 12))
        draw_text(surf, f"HI {max(self.high, self.score)}", 28, YELLOW, topleft=(10, 34))

        # Player ship
        pygame.draw.rect(surf, CYAN, (self.px, self.py, self.pw, self.ph))
        pygame.draw.rect(surf, WHITE, (self.px + 10, self.py - 6, 10, 6))

        # Bullets
        for b in self.bullets:
            pygame.draw.rect(surf, YELLOW, (int(b["x"]), int(b["y"]), 4, 10))

        # Enemies
        for e in self.enemies:
            pygame.draw.rect(surf, RED, (int(e["x"]), int(e["y"]), 24, 20))
            pygame.draw.rect(surf, ORANGE, (int(e["x"]) + 6, int(e["y"]) + 4, 12, 12))

        draw_controls(surf, show_dpad=True, show_a=True, a_label="FIRE")
        if not self.alive:
            self.draw_game_over(surf, self.score, self.new_record)


# =====================================================================
# 11. GAME #6 - BRICK BREAKER
# =====================================================================
class BrickBreaker(Game):
    TITLE = "BRICK BREAKER"
    COLOR = PINK
    KEY = "breaker"
    USES_DPAD = True

    def reset(self):
        self.pw = 64
        self.px = (W - self.pw) // 2
        self.py = 440
        self.bx = W // 2
        self.by = 300
        self.bvx = 150.0 * random.choice([-1, 1])
        self.bvy = -180.0
        self.score = 0
        self.alive = True
        self.new_record = False
        self.high = get_high(self.KEY)
        self.build_bricks()

    def build_bricks(self):
        self.bricks = []
        cols, rows = 6, 5
        bw, bh = (W - 30) // cols, 16
        colors = [RED, ORANGE, YELLOW, GREEN, CYAN]
        for r in range(rows):
            for c in range(cols):
                rect = pygame.Rect(15 + c * bw, 60 + r * (bh + 4), bw - 2, bh)
                self.bricks.append({"rect": rect, "color": colors[r % len(colors)]})

    def handle_input(self, inp):
        if self.check_back(inp):
            return
        if not self.alive:
            if ACTION in inp.actions or inp.tap_pos:
                self.reset()
            return

        if LEFT in inp.actions or LEFT in inp.held:
            self.px -= 7
        if RIGHT in inp.actions or RIGHT in inp.held:
            self.px += 7
        self.px = max(5, min(W - 5 - self.pw, self.px))

    def update(self, dt):
        if not self.alive:
            return

        self.bx += self.bvx * dt
        self.by += self.bvy * dt

        if self.bx <= 8:
            self.bx = 8
            self.bvx *= -1
        elif self.bx >= W - 8:
            self.bx = W - 8
            self.bvx *= -1

        if self.by <= 50:
            self.by = 50
            self.bvy *= -1

        if self.by >= 470:
            self.alive = False
            self.new_record = submit_score(self.KEY, self.score)
            self.high = get_high(self.KEY)
            return

        ball_rect = pygame.Rect(int(self.bx - 5), int(self.by - 5), 10, 10)
        paddle_rect = pygame.Rect(self.px, self.py, self.pw, 12)

        if ball_rect.colliderect(paddle_rect) and self.bvy > 0:
            self.bvy = -abs(self.bvy)
            offset = (self.bx - (self.px + self.pw / 2)) / (self.pw / 2)
            self.bvx = offset * 220

        for brick in self.bricks[:]:
            if ball_rect.colliderect(brick["rect"]):
                self.bricks.remove(brick)
                self.bvy *= -1
                self.score += 10
                break

        if not self.bricks:
            self.build_bricks()
            self.bvy *= 1.1

    def draw(self, surf):
        surf.fill(BLACK)
        draw_text(surf, f"SCORE {self.score}", 28, WHITE, topleft=(10, 12))
        draw_text(surf, f"HI {max(self.high, self.score)}", 28, YELLOW, topleft=(10, 34))

        for b in self.bricks:
            pygame.draw.rect(surf, b["color"], b["rect"])
            pygame.draw.rect(surf, WHITE, b["rect"], 1)

        pygame.draw.rect(surf, WHITE, (self.px, self.py, self.pw, 12))
        pygame.draw.circle(surf, YELLOW, (int(self.bx), int(self.by)), 5)

        draw_controls(surf, show_dpad=True)
        if not self.alive:
            self.draw_game_over(surf, self.score, self.new_record)


# =====================================================================
# 12. THE HUB (main menu + the loop that runs everything)
# =====================================================================
ALL_GAMES = [Snake, Game2048, Runner, Flappy, SpaceBlaster, BrickBreaker]


class Hub:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Cool-lil-android-game-hub-yay")
        self.on_android = "ANDROID_ARGUMENT" in os.environ
        if self.on_android:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode((W, H), pygame.RESIZABLE)
        self.canvas = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.inp = Input()
        self.current = None
        self.selected = 0
        self.tick = 0.0
        self.button_rects = []
        self.running = True
        self.scale = 1.0
        self.dest = pygame.Rect(0, 0, W, H)

    def layout(self):
        ww, wh = self.window.get_size()
        self.scale = min(ww / W, wh / H)
        self.dest = pygame.Rect(0, 0, int(W * self.scale), int(H * self.scale))
        self.dest.center = (ww // 2, wh // 2)

    def to_virtual(self, pos):
        return ((pos[0] - self.dest.x) / self.scale, (pos[1] - self.dest.y) / self.scale)

    def frame(self, dt):
        self.tick += dt
        self.layout()
        self.inp.begin_frame()
        self.inp.dpad_active = self.current is not None and self.current.USES_DPAD
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            self.inp.handle(event, self.to_virtual)

        if self.current:
            self.current.handle_input(self.inp)
            self.current.update(dt)
            self.current.draw(self.canvas)
            if self.current.done:
                self.current = None
        else:
            self.menu_input()
            self.draw_menu()

        draw_scanlines(self.canvas)
        self.window.fill((0, 0, 0))
        self.window.blit(pygame.transform.scale(self.canvas, self.dest.size), self.dest)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(60) / 1000.0, 0.05)
            self.frame(dt)
        pygame.quit()

    def launch(self, index):
        if 0 <= index < len(ALL_GAMES):
            self.current = ALL_GAMES[index]()

    def menu_input(self):
        n = len(ALL_GAMES)
        for a in self.inp.actions:
            if a == UP:
                self.selected = (self.selected - 1) % n
            elif a == DOWN:
                self.selected = (self.selected + 1) % n
            elif a == ACTION and self.inp.tap_pos is None:
                self.launch(self.selected)
            elif a == BACK:
                self.running = False
        if self.inp.tap_pos:
            for i, rect in enumerate(self.button_rects):
                if rect.collidepoint(self.inp.tap_pos):
                    self.selected = i
                    self.launch(i)

    def draw_menu(self):
        s = self.canvas
        s.fill(BLACK)
        for i in range(0, H, 40):
            y = (i + int(self.tick * 30)) % H
            pygame.draw.line(s, NAVY, (0, y), (W, y), 2)

        bob = int(3 * pygame.math.Vector2(0, 1).rotate(self.tick * 180).y)
        draw_text(s, "COOL-LIL", 50, PINK, center=(W // 2, 60 + bob))
        draw_text(s, "GAME HUB", 50, YELLOW, center=(W // 2, 104 + bob))
        draw_text(s, "* * *  YAY  * * *", 22, CYAN, center=(W // 2, 142))

        self.button_rects = []
        n = len(ALL_GAMES)
        btn_h = 48 if n > 4 else 68
        gap = 10 if n > 4 else 20
        y_start = 175 if n > 4 else 205

        y = y_start
        for i, cls in enumerate(ALL_GAMES):
            rect = pygame.Rect(30, y, W - 60, btn_h)
            self.button_rects.append(rect)
            draw_button(s, rect, cls.TITLE, color=cls.COLOR, size=26 if n > 4 else 34)
            draw_text(s, f"HI {get_high(cls.KEY)}", 16 if n > 4 else 20, YELLOW, center=(rect.centerx, rect.bottom - 9))
            if i == self.selected and int(self.tick * 3) % 2 == 0:
                draw_text(s, ">", 28 if n > 4 else 34, YELLOW, center=(rect.x - 14, rect.centery))
                draw_text(s, "<", 28 if n > 4 else 34, YELLOW, center=(rect.right + 14, rect.centery))
            y += btn_h + gap

        draw_text(s, "TAP A GAME TO PLAY", 20, GREY, center=(W // 2, H - 36))
        draw_text(s, "keys: arrows + ENTER", 16, GREY, center=(W // 2, H - 16))


def main():
    Hub().run()


if __name__ == "__main__":
    main()
