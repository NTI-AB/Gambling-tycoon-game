import pygame
import sys
import random
import math

pygame.init()

# Fönster
WIN_WIDTH, WIN_HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Casino Tycoon")

clock = pygame.time.Clock()
FPS = 60

# Färger
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
DARK_BG = (30, 30, 30)

# Storlekar
PLAYER_SIZE = (30, 30)
MACHINE_SIZE = (50, 50)

# Casinoområde
CASINO_RECT = pygame.Rect(50, 300, 700, 200)

# Pengar
money = 1000

# Vägar (flera paths)
paths = [
    [pygame.Vector2(x, 480) for x in range(100, 700, 50)],
    [pygame.Vector2(x, 420) for x in range(100, 700, 50)],
    [pygame.Vector2(x, 360) for x in range(100, 700, 50)],
]

exit_point = pygame.Vector2(750, 480)

# Maskintyper med stats och kostnader
machine_types = {
    "slot": {"cost": 200, "win_chance": 0.4, "win_amount": 50, "cooldown": 60},
    "roulette": {"cost": 500, "win_chance": 0.3, "win_amount": 150, "cooldown": 90},
    "blackjack": {"cost": 800, "win_chance": 0.5, "win_amount": 300, "cooldown": 120},
}

selected_machine_type = "slot"
machines = []  # List of dicts: {"pos": Vector2, "type": "slot", ...}

# Player
player_pos = pygame.Vector2(100, 350)
build_mode = False

# NPC lista
npcs = []

# Hjälpmeny
show_help = False

# Font
font = pygame.font.SysFont(None, 24)

# Q-knapp area
q_rect = pygame.Rect(10, 70, 30, 30)


def distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def find_closest_point(point, path):
    closest = path[0]
    min_dist = distance(point, closest)
    for p in path:
        d = distance(point, p)
        if d < min_dist:
            closest = p
            min_dist = d
    return closest


def shortest_path_to_exit(npc_pos):
    best_path = None
    best_start_index = 0
    best_dist = float('inf')

    for path in paths:
        closest_point = find_closest_point(npc_pos, path)
        dist = distance(npc_pos, closest_point)
        if dist < best_dist:
            best_dist = dist
            best_path = path
            best_start_index = path.index(closest_point)

    return best_path, best_start_index


class NPC:
    def __init__(self):
        self.path = random.choice(paths)
        self.path_index = 0
        self.pos = self.path[0].copy()
        self.state = "walking_path"  # walking_path, to_machine, playing, leaving
        self.target_machine = None
        self.cooldown = 0
        self.losses = 0
        self.machines_played = 0
        self.plays = 0

    def update(self):
        global money
        speed = 1.5

        if self.state == "walking_path":
            if self.path_index < len(self.path) - 1:
                target = self.path[self.path_index + 1]
                direction = target - self.pos
                if direction.length() > speed:
                    self.pos += direction.normalize() * speed
                else:
                    self.path_index += 1
            else:
                # Gå till maskin eller lämna om ingen maskin eller för lite pengar
                if machines and money >= 50:
                    self.target_machine = random.choice(machines)
                    self.state = "to_machine"
                else:
                    self.state = "leaving"
                    self.set_exit_path()

        elif self.state == "to_machine":
            direction = self.target_machine["pos"] - self.pos
            if direction.length() > speed:
                self.pos += direction.normalize() * speed
            else:
                self.state = "playing"
                self.cooldown = 0
                self.losses = 0
                self.plays = 0

        elif self.state == "playing":
            if self.cooldown > 0:
                self.cooldown -= 1
            else:
                self.cooldown = self.target_machine["cooldown"]
                cost_to_play = 50

                if money >= cost_to_play:
                    money -= cost_to_play
                else:
                    self.state = "leaving"
                    self.set_exit_path()
                    return

                machine_data = self.target_machine
                win_chance = machine_data["win_chance"]
                win_amount = machine_data["win_amount"]

                if random.random() < win_chance:
                    money += win_amount
                    self.losses = 0
                else:
                    self.losses += 1

                self.plays += 1

                if self.losses >= 3:
                    self.machines_played += 1
                    if self.machines_played >= 2:
                        self.state = "leaving"
                        self.set_exit_path()
                    else:
                        available_machines = [m for m in machines if m != self.target_machine]
                        if available_machines:
                            self.target_machine = random.choice(available_machines)
                            self.state = "to_machine"
                            self.losses = 0
                            self.plays = 0
                        else:
                            self.state = "leaving"
                            self.set_exit_path()

        elif self.state == "leaving":
            if self.path_index < len(self.path) - 1:
                target = self.path[self.path_index + 1]
                direction = target - self.pos
                if direction.length() > speed:
                    self.pos += direction.normalize() * speed
                else:
                    self.path_index += 1
            else:
                if self in npcs:
                    npcs.remove(self)

    def set_exit_path(self):
        self.path, self.path_index = shortest_path_to_exit(self.pos)


def spawn_npc():
    npcs.append(NPC())


def place_machine():
    global money
    cost = machine_types[selected_machine_type]["cost"]
    pos_rect = pygame.Rect(player_pos.x, player_pos.y, *MACHINE_SIZE)
    if CASINO_RECT.contains(pos_rect) and money >= cost:
        machines.append({
            "pos": player_pos.copy(),
            "type": selected_machine_type,
            "win_chance": machine_types[selected_machine_type]["win_chance"],
            "win_amount": machine_types[selected_machine_type]["win_amount"],
            "cooldown": machine_types[selected_machine_type]["cooldown"]
        })
        money -= cost


def draw_window():
    WIN.fill((50, 50, 50))
    pygame.draw.rect(WIN, (100, 100, 100), CASINO_RECT)

    # Rita vägar
    for path in paths:
        for pos in path:
            pygame.draw.rect(WIN, GRAY, (pos.x, pos.y, 50, 10))

    # Rita maskiner
    for machine in machines:
        color = GREEN
        if machine["type"] == "roulette":
            color = (200, 0, 200)
        elif machine["type"] == "blackjack":
            color = (0, 0, 200)
        pygame.draw.rect(WIN, color, (machine["pos"].x, machine["pos"].y, *MACHINE_SIZE))

    # Rita NPCs
    for npc in npcs:
        pygame.draw.circle(WIN, RED, (int(npc.pos.x + 15), int(npc.pos.y + 15)), 15)

    # Rita spelare
    player_color = YELLOW if build_mode else WHITE
    pygame.draw.rect(WIN, player_color, (player_pos.x, player_pos.y, *PLAYER_SIZE))

    # Visa pengar och vald maskin info
    money_text = font.render(f"Cash: ${money}", True, WHITE)
    WIN.blit(money_text, (10, 10))
    machine_info = machine_types[selected_machine_type]
    info_text = font.render(f"Selected: {selected_machine_type} (Cost: ${machine_info['cost']})", True, WHITE)
    WIN.blit(info_text, (10, 40))

    # Q-knapp
    pygame.draw.rect(WIN, LIGHT_GRAY, q_rect)
    q_text = font.render("Q", True, BLACK)
    WIN.blit(q_text, (q_rect.x + 8, q_rect.y + 2))

    # Hjälpmeny
    if show_help:
        help_rect = pygame.Rect(100, 100, 600, 400)
        pygame.draw.rect(WIN, DARK_BG, help_rect)
        pygame.draw.rect(WIN, WHITE, help_rect, 2)

        lines = [
            "Hotkeys:",
            "WASD - Move player",
            "B - Toggle build mode",
            "E - Place machine",
            "1 - Select slot machine",
            "2 - Select roulette",
            "3 - Select blackjack",
            "Q - Toggle help menu",
            "ESC - Quit"
        ]

        for i, line in enumerate(lines):
            txt = font.render(line, True, WHITE)
            WIN.blit(txt, (help_rect.x + 20, help_rect.y + 20 + i * 30))

    pygame.display.update()


def main():
    global build_mode, selected_machine_type, show_help, money

    spawn_timer = 0

    while True:
        clock.tick(FPS)
        spawn_timer += 1
        if spawn_timer > FPS * 5:
            spawn_npc()
            spawn_timer = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if q_rect.collidepoint(mouse_pos):
                    show_help = not show_help

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    show_help = not show_help

                if event.key == pygame.K_b:
                    build_mode = not build_mode

                if event.key == pygame.K_1:
                    selected_machine_type = "slot"

                elif event.key == pygame.K_2:
                    selected_machine_type = "roulette"

                elif event.key == pygame.K_3:
                    selected_machine_type = "blackjack"

                if event.key == pygame.K_e and build_mode:
                    place_machine()

                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        keys = pygame.key.get_pressed()
        speed = 4
        if keys[pygame.K_w]:
            player_pos.y -= speed
        if keys[pygame.K_s]:
            player_pos.y += speed
        if keys[pygame.K_a]:
            player_pos.x -= speed
        if keys[pygame.K_d]:
            player_pos.x += speed

        # Begränsa spelare inom casinoområdet (med lite buffert)
        if player_pos.x < CASINO_RECT.left:
            player_pos.x = CASINO_RECT.left
        if player_pos.x > CASINO_RECT.right - PLAYER_SIZE[0]:
            player_pos.x = CASINO_RECT.right - PLAYER_SIZE[0]
        if player_pos.y < CASINO_RECT.top:
            player_pos.y = CASINO_RECT.top
        if player_pos.y > CASINO_RECT.bottom - PLAYER_SIZE[1]:
            player_pos.y = CASINO_RECT.bottom - PLAYER_SIZE[1]

        # Uppdatera NPCs
        for npc in npcs[:]:
            npc.update()

        draw_window()


if __name__ == "__main__":
    main()
