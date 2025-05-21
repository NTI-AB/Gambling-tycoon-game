import pygame
import sys
import random
import math
from enum import Enum

pygame.init()

# Game Constants
WIN_WIDTH, WIN_HEIGHT = 800, 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (0, 0, 200)
PURPLE = (200, 0, 200)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
DARK_BG = (30, 30, 30)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# Sizes
PLAYER_SIZE = (30, 30)
MACHINE_SIZE = (50, 50)
WALL_SIZE = 50

# Machine types with stats, costs and unlock requirements
class MachineType(Enum):
    SLOT = "slot"
    ROULETTE = "roulette"
    BLACKJACK = "blackjack"
    POKER = "poker"
    CRAPS = "craps"
    
machine_types = {
    MachineType.SLOT: {
        "name": "Slot Machine",
        "cost": 200,
        "win_chance": 0.4,
        "win_amount": 50,
        "cooldown": 60,
        "unlock_at": 0,
        "color": GREEN
    },
    MachineType.ROULETTE: {
        "name": "Roulette",
        "cost": 500,
        "win_chance": 0.3,
        "win_amount": 150,
        "cooldown": 90,
        "unlock_at": 2000,
        "color": PURPLE
    },
    MachineType.BLACKJACK: {
        "name": "Blackjack",
        "cost": 800,
        "win_chance": 0.5,
        "win_amount": 300,
        "cooldown": 120,
        "unlock_at": 5000,
        "color": BLUE
    },
    MachineType.POKER: {
        "name": "Poker Table",
        "cost": 1200,
        "win_chance": 0.45,
        "win_amount": 400,
        "cooldown": 150,
        "unlock_at": 10000,
        "color": ORANGE
    },
    MachineType.CRAPS: {
        "name": "Craps Table",
        "cost": 1500,
        "win_chance": 0.35,
        "win_amount": 500,
        "cooldown": 180,
        "unlock_at": 15000,
        "color": CYAN
    }
}

# Casino upgrades
casino_upgrades = {
    "more_machines": {
        "name": "More Machines",
        "description": "NPCs will play up to 3 machines before leaving",
        "cost": 3000,
        "max_level": 3,
        "current_level": 0
    },
    "faster_cooldown": {
        "name": "Faster Play",
        "description": "Reduces machine cooldown by 10% per level",
        "cost": 2000,
        "max_level": 5,
        "current_level": 0
    },
    "better_odds": {
        "name": "Better Odds",
        "description": "Increases win chance by 5% per level",
        "cost": 5000,
        "max_level": 3,
        "current_level": 0
    },
    "higher_payouts": {
        "name": "Higher Payouts",
        "description": "Increases win amount by 20% per level",
        "cost": 4000,
        "max_level": 3,
        "current_level": 0
    }
}

class GameState:
    def __init__(self):
        self.win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        pygame.display.set_caption("Casino Tycoon")
        self.clock = pygame.time.Clock()
        
        # Game objects
        self.casino_rect = pygame.Rect(50, 300, 700, 200)
        self.money = 1000
        self.total_earnings = 0
        self.total_visitors = 0
        self.machines = []
        self.npcs = []
        self.walls = []
        
        # Player state
        self.player_pos = pygame.Vector2(100, 350)
        self.build_mode = False
        self.wall_mode = False
        self.selected_machine_type = MachineType.SLOT
        
        # UI state
        self.show_help = False
        self.show_stats = False
        self.show_upgrades = False
        self.ui_font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 32)
        
        # Paths for NPCs
        self.paths = [
            [pygame.Vector2(x, 480) for x in range(100, 700, 50)],
            [pygame.Vector2(x, 420) for x in range(100, 700, 50)],
            [pygame.Vector2(x, 360) for x in range(100, 700, 50)],
        ]
        self.exit_point = pygame.Vector2(750, 480)
        
        # UI elements
        self.q_rect = pygame.Rect(10, 70, 30, 30)
        self.s_rect = pygame.Rect(10, 110, 30, 30)
        self.u_rect = pygame.Rect(10, 150, 30, 30)
        
        # Animation effects
        self.effects = []
        
        # Spawn timer
        self.spawn_timer = 0
        self.spawn_rate = FPS * 5  # 5 seconds
        
    def distance(self, a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
    
    def find_closest_point(self, point, path):
        closest = path[0]
        min_dist = self.distance(point, closest)
        for p in path:
            d = self.distance(point, p)
            if d < min_dist:
                closest = p
                min_dist = d
        return closest
    
    def shortest_path_to_exit(self, npc_pos):
        best_path = None
        best_start_index = 0
        best_dist = float('inf')

        for path in self.paths:
            closest_point = self.find_closest_point(npc_pos, path)
            dist = self.distance(npc_pos, closest_point)
            if dist < best_dist:
                best_dist = dist
                best_path = path
                best_start_index = path.index(closest_point)

        return best_path, best_start_index
    
    def add_effect(self, pos, color, duration=30, size=15):
        self.effects.append({
            "pos": pos.copy(),
            "color": color,
            "timer": duration,
            "max_time": duration,
            "size": size
        })
    
    def update_effects(self):
        for effect in self.effects[:]:
            effect["timer"] -= 1
            if effect["timer"] <= 0:
                self.effects.remove(effect)

class Machine:
    def __init__(self, pos, machine_type):
        self.pos = pos
        self.type = machine_type
        self.data = machine_types[machine_type]
        self.cooldown = 0
        self.upgrades = {
            "speed": 0,
            "odds": 0,
            "payout": 0
        }
        
    def get_win_chance(self):
        base = self.data["win_chance"]
        upgraded = base + (0.05 * self.upgrades["odds"])
        return min(upgraded, 0.9)  # Cap at 90% chance
        
    def get_win_amount(self):
        base = self.data["win_amount"]
        upgraded = base * (1 + (0.2 * self.upgrades["payout"]))
        return int(upgraded)
        
    def get_cooldown(self):
        base = self.data["cooldown"]
        upgraded = base * (0.9 ** self.upgrades["speed"])
        return int(upgraded)
        
    def can_upgrade(self, upgrade_type):
        return self.upgrades[upgrade_type] < 3
        
    def upgrade_cost(self, upgrade_type):
        return 500 * (self.upgrades[upgrade_type] + 1)
        
    def upgrade(self, upgrade_type):
        if self.can_upgrade(upgrade_type):
            cost = self.upgrade_cost(upgrade_type)
            if game.money >= cost:
                game.money -= cost
                self.upgrades[upgrade_type] += 1
                return True
        return False

class NPC:
    def __init__(self):
        self.path = random.choice(game.paths)
        self.path_index = 0
        self.pos = self.path[0].copy()
        self.state = "walking_path"  # walking_path, to_machine, playing, leaving
        self.target_machine = None
        self.cooldown = 0
        self.losses = 0
        self.machines_played = 0
        self.plays = 0
        self.max_machines = 2 + casino_upgrades["more_machines"]["current_level"]
        self.speed = 1.5
        
    def update(self):
        if self.state == "walking_path":
            self.walk_path()
        elif self.state == "to_machine":
            self.move_to_machine()
        elif self.state == "playing":
            self.play_machine()
        elif self.state == "leaving":
            self.leave_casino()
    
    def walk_path(self):
        if self.path_index < len(self.path) - 1:
            target = self.path[self.path_index + 1]
            direction = target - self.pos
            if direction.length() > self.speed:
                self.pos += direction.normalize() * self.speed
            else:
                self.path_index += 1
        else:
            # Choose machine or leave if no machines or not enough money
            if game.machines and game.money >= 50:
                self.choose_machine()
            else:
                self.state = "leaving"
                self.set_exit_path()
    
    def choose_machine(self):
        # AI: Choose machine based on best value (win_chance * win_amount / cooldown)
        best_value = 0
        best_machine = None
        
        for machine in game.machines:
            # Skip machines that are on cooldown
            if machine.cooldown > 0:
                continue
                
            win_chance = machine.get_win_chance()
            win_amount = machine.get_win_amount()
            cooldown = machine.get_cooldown()
            
            value = (win_chance * win_amount) / cooldown
            
            if value > best_value:
                best_value = value
                best_machine = machine
        
        if best_machine:
            self.target_machine = best_machine
            self.state = "to_machine"
        else:
            self.state = "leaving"
            self.set_exit_path()
    
    def move_to_machine(self):
        direction = self.target_machine.pos - self.pos
        if direction.length() > self.speed:
            self.pos += direction.normalize() * self.speed
        else:
            self.state = "playing"
            self.cooldown = 0
            self.losses = 0
            self.plays = 0
    
    def play_machine(self):
        if self.cooldown > 0:
            self.cooldown -= 1
        else:
            cost_to_play = 50
            
            if game.money >= cost_to_play:
                game.money -= cost_to_play
            else:
                self.state = "leaving"
                self.set_exit_path()
                return
            
            # Get machine stats with upgrades applied
            win_chance = self.target_machine.get_win_chance()
            win_amount = self.target_machine.get_win_amount()
            self.target_machine.cooldown = self.target_machine.get_cooldown()
            
            if random.random() < win_chance:
                game.money += win_amount
                game.total_earnings += win_amount - cost_to_play
                self.losses = 0
                game.add_effect(self.pos, GREEN)  # Win effect
            else:
                game.total_earnings -= cost_to_play
                self.losses += 1
                game.add_effect(self.pos, RED)  # Lose effect
            
            self.plays += 1
            self.cooldown = self.target_machine.cooldown
            
            # Check if NPC should leave or try another machine
            if self.losses >= 3:
                self.machines_played += 1
                if self.machines_played >= self.max_machines:
                    self.state = "leaving"
                    self.set_exit_path()
                else:
                    self.choose_machine()
                    self.losses = 0
                    self.plays = 0
    
    def leave_casino(self):
        if self.path_index < len(self.path) - 1:
            target = self.path[self.path_index + 1]
            direction = target - self.pos
            if direction.length() > self.speed:
                self.pos += direction.normalize() * self.speed
            else:
                self.path_index += 1
        else:
            if self in game.npcs:
                game.npcs.remove(self)
    
    def set_exit_path(self):
        self.path, self.path_index = game.shortest_path_to_exit(self.pos)

def spawn_npc():
    game.npcs.append(NPC())
    game.total_visitors += 1

def place_machine():
    cost = machine_types[game.selected_machine_type]["cost"]
    pos_rect = pygame.Rect(game.player_pos.x, game.player_pos.y, *MACHINE_SIZE)
    
    # Check if position is valid (inside casino and not overlapping walls or other machines)
    if (game.casino_rect.contains(pos_rect) and 
        game.money >= cost and
        not any(wall.colliderect(pos_rect) for wall in game.walls) and
        not any(machine.pos.x == game.player_pos.x and 
                machine.pos.y == game.player_pos.y for machine in game.machines)):
        
        game.machines.append(Machine(game.player_pos.copy(), game.selected_machine_type))
        game.money -= cost

def place_wall():
    pos_rect = pygame.Rect(game.player_pos.x, game.player_pos.y, *MACHINE_SIZE)
    cost = 100
    
    # Check if position is valid (inside casino and not overlapping machines)
    if (game.casino_rect.contains(pos_rect) and 
        game.money >= cost and
        not any(machine.pos.x == game.player_pos.x and 
                machine.pos.y == game.player_pos.y for machine in game.machines)):
        
        game.walls.append(pos_rect)
        game.money -= cost

def draw_window():
    game.win.fill((50, 50, 50))
    
    # Draw casino area
    pygame.draw.rect(game.win, (100, 100, 100), game.casino_rect)
    
    # Draw walls
    for wall in game.walls:
        pygame.draw.rect(game.win, (70, 70, 70), wall)
    
    # Draw paths
    for path in game.paths:
        for pos in path:
            pygame.draw.rect(game.win, GRAY, (pos.x, pos.y, 50, 10))
    
    # Draw machines
    for machine in game.machines:
        color = machine.data["color"]
        pygame.draw.rect(game.win, color, (machine.pos.x, machine.pos.y, *MACHINE_SIZE))
        
        # Draw cooldown indicator
        if machine.cooldown > 0:
            cooldown_ratio = machine.cooldown / machine.get_cooldown()
            height = int(MACHINE_SIZE[1] * cooldown_ratio)
            pygame.draw.rect(game.win, (0, 0, 0, 128), 
                           (machine.pos.x, machine.pos.y + MACHINE_SIZE[1] - height, 
                            MACHINE_SIZE[0], height))
    
    # Draw NPCs
    for npc in game.npcs:
        pygame.draw.circle(game.win, RED, (int(npc.pos.x + 15), int(npc.pos.y + 15)), 15)
        
        # Draw state indicator
        if npc.state == "playing":
            pygame.draw.circle(game.win, YELLOW, (int(npc.pos.x + 15), int(npc.pos.y - 10)), 5)
    
    # Draw effects
    for effect in game.effects:
        alpha = int(255 * (effect["timer"] / effect["max_time"]))
        size = int(effect["size"] * (effect["timer"] / effect["max_time"]))
        
        s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*effect["color"], alpha), (size, size), size)
        game.win.blit(s, (effect["pos"].x + 15 - size, effect["pos"].y + 15 - size))
    
    # Draw player
    if game.build_mode:
        player_color = GREEN
    elif game.wall_mode:
        player_color = BLUE
    else:
        player_color = WHITE
    pygame.draw.rect(game.win, player_color, (game.player_pos.x, game.player_pos.y, *PLAYER_SIZE))
    
    # Draw UI
    draw_ui()
    
    pygame.display.update()

def draw_ui():
    # Money and selected machine info
    money_text = game.ui_font.render(f"Cash: ${game.money}", True, WHITE)
    game.win.blit(money_text, (10, 10))
    
    machine_info = machine_types[game.selected_machine_type]
    info_text = game.ui_font.render(f"Selected: {machine_info['name']} (${machine_info['cost']})", True, WHITE)
    game.win.blit(info_text, (10, 40))
    
    # UI buttons
    pygame.draw.rect(game.win, LIGHT_GRAY, game.q_rect)
    q_text = game.ui_font.render("Q", True, BLACK)
    game.win.blit(q_text, (game.q_rect.x + 8, game.q_rect.y + 2))
    
    pygame.draw.rect(game.win, LIGHT_GRAY, game.s_rect)
    s_text = game.ui_font.render("S", True, BLACK)
    game.win.blit(s_text, (game.s_rect.x + 8, game.s_rect.y + 2))
    
    pygame.draw.rect(game.win, LIGHT_GRAY, game.u_rect)
    u_text = game.ui_font.render("U", True, BLACK)
    game.win.blit(u_text, (game.u_rect.x + 8, game.u_rect.y + 2))
    
    # Mode indicators
    mode_text = game.ui_font.render(
        f"Mode: {'BUILD' if game.build_mode else 'WALL' if game.wall_mode else 'MOVE'}", 
        True, WHITE)
    game.win.blit(mode_text, (WIN_WIDTH - 150, 10))
    
    # Help menu
    if game.show_help:
        draw_help_menu()
    
    # Stats menu
    if game.show_stats:
        draw_stats_menu()
    
    # Upgrades menu
    if game.show_upgrades:
        draw_upgrades_menu()

def draw_help_menu():
    help_rect = pygame.Rect(100, 100, 600, 400)
    pygame.draw.rect(game.win, DARK_BG, help_rect)
    pygame.draw.rect(game.win, WHITE, help_rect, 2)
    
    title = game.title_font.render("Casino Tycoon - Help", True, WHITE)
    game.win.blit(title, (help_rect.x + 20, help_rect.y + 20))
    
    lines = [
        "Hotkeys:",
        "WASD - Move player",
        "B - Toggle build mode",
        "W - Toggle wall mode",
        "E - Place selected item (machine/wall)",
        "1-5 - Select machine type",
        "Q - Toggle help menu",
        "S - Toggle stats menu",
        "U - Toggle upgrades menu",
        "ESC - Quit",
        "",
        "Gameplay:",
        "- Build machines to attract NPCs",
        "- NPCs play machines and can win/lose",
        "- Walls can guide NPC traffic",
        "- Upgrade machines and casino for better performance"
    ]
    
    for i, line in enumerate(lines):
        txt = game.ui_font.render(line, True, WHITE)
        game.win.blit(txt, (help_rect.x + 20, help_rect.y + 60 + i * 25))

def draw_stats_menu():
    stats_rect = pygame.Rect(100, 100, 600, 400)
    pygame.draw.rect(game.win, DARK_BG, stats_rect)
    pygame.draw.rect(game.win, WHITE, stats_rect, 2)
    
    title = game.title_font.render("Casino Statistics", True, WHITE)
    game.win.blit(title, (stats_rect.x + 20, stats_rect.y + 20))
    
    # Machine stats
    machine_stats = []
    for machine_type in MachineType:
        count = sum(1 for m in game.machines if m.type == machine_type)
        if count > 0:
            machine_stats.append(f"{machine_type.value.capitalize()}: {count}")
    
    # General stats
    lines = [
        f"Total Visitors: {game.total_visitors}",
        f"Current Visitors: {len(game.npcs)}",
        f"Total Earnings: ${game.total_earnings}",
        f"Machines: {len(game.machines)}",
        "",
        "Machine Breakdown:"
    ] + machine_stats
    
    for i, line in enumerate(lines):
        txt = game.ui_font.render(line, True, WHITE)
        game.win.blit(txt, (stats_rect.x + 20, stats_rect.y + 60 + i * 25))

def draw_upgrades_menu():
    upgrades_rect = pygame.Rect(100, 100, 600, 400)
    pygame.draw.rect(game.win, DARK_BG, upgrades_rect)
    pygame.draw.rect(game.win, WHITE, upgrades_rect, 2)
    
    title = game.title_font.render("Upgrades", True, WHITE)
    game.win.blit(title, (upgrades_rect.x + 20, upgrades_rect.y + 20))
    
    # Casino upgrades
    lines = ["Casino Upgrades:"]
    for i, (key, upgrade) in enumerate(casino_upgrades.items()):
        level = upgrade["current_level"]
        max_level = upgrade["max_level"]
        cost = upgrade["cost"] * (level + 1)
        
        status = f"{level}/{max_level}"
        if level < max_level:
            line = f"{upgrade['name']} ({status}) - ${cost}: {upgrade['description']}"
        else:
            line = f"{upgrade['name']} (MAX): {upgrade['description']}"
        
        lines.append(line)
    
    # Machine upgrade instructions
    lines.extend([
        "",
        "Machine Upgrades:",
        "Click on a machine to upgrade it",
        "Available upgrades:",
        "- Speed: Reduces cooldown",
        "- Odds: Increases win chance",
        "- Payout: Increases win amount"
    ])
    
    for i, line in enumerate(lines):
        txt = game.ui_font.render(line, True, WHITE)
        game.win.blit(txt, (upgrades_rect.x + 20, upgrades_rect.y + 60 + i * 25))

def handle_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check UI buttons
            if game.q_rect.collidepoint(mouse_pos):
                game.show_help = not game.show_help
                game.show_stats = False
                game.show_upgrades = False
            elif game.s_rect.collidepoint(mouse_pos):
                game.show_stats = not game.show_stats
                game.show_help = False
                game.show_upgrades = False
            elif game.u_rect.collidepoint(mouse_pos):
                game.show_upgrades = not game.show_upgrades
                game.show_help = False
                game.show_stats = False
            
            # Check if clicking on a machine to upgrade (when not in build/wall mode)
            elif not game.build_mode and not game.wall_mode:
                for machine in game.machines:
                    machine_rect = pygame.Rect(machine.pos.x, machine.pos.y, *MACHINE_SIZE)
                    if machine_rect.collidepoint(mouse_pos):
                        show_machine_upgrades(machine)
                        break
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                game.show_help = not game.show_help
                game.show_stats = False
                game.show_upgrades = False
            elif event.key == pygame.K_s:
                game.show_stats = not game.show_stats
                game.show_help = False
                game.show_upgrades = False
            elif event.key == pygame.K_u:
                game.show_upgrades = not game.show_upgrades
                game.show_help = False
                game.show_stats = False
            elif event.key == pygame.K_b:
                game.build_mode = not game.build_mode
                game.wall_mode = False if game.build_mode else game.wall_mode
            elif event.key == pygame.K_w:
                game.wall_mode = not game.wall_mode
                game.build_mode = False if game.wall_mode else game.build_mode
            elif event.key == pygame.K_1:
                if machine_types[MachineType.SLOT]["unlock_at"] <= game.money:
                    game.selected_machine_type = MachineType.SLOT
            elif event.key == pygame.K_2:
                if machine_types[MachineType.ROULETTE]["unlock_at"] <= game.money:
                    game.selected_machine_type = MachineType.ROULETTE
            elif event.key == pygame.K_3:
                if machine_types[MachineType.BLACKJACK]["unlock_at"] <= game.money:
                    game.selected_machine_type = MachineType.BLACKJACK
            elif event.key == pygame.K_4:
                if machine_types[MachineType.POKER]["unlock_at"] <= game.money:
                    game.selected_machine_type = MachineType.POKER
            elif event.key == pygame.K_5:
                if machine_types[MachineType.CRAPS]["unlock_at"] <= game.money:
                    game.selected_machine_type = MachineType.CRAPS
            elif event.key == pygame.K_e:
                if game.build_mode:
                    place_machine()
                elif game.wall_mode:
                    place_wall()
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
    
    # Player movement
    keys = pygame.key.get_pressed()
    speed = 4
    if keys[pygame.K_w]:
        game.player_pos.y -= speed
    if keys[pygame.K_s]:
        game.player_pos.y += speed
    if keys[pygame.K_a]:
        game.player_pos.x -= speed
    if keys[pygame.K_d]:
        game.player_pos.x += speed
    
    # Keep player inside casino area (with some buffer)
    if game.player_pos.x < game.casino_rect.left:
        game.player_pos.x = game.casino_rect.left
    if game.player_pos.x > game.casino_rect.right - PLAYER_SIZE[0]:
        game.player_pos.x = game.casino_rect.right - PLAYER_SIZE[0]
    if game.player_pos.y < game.casino_rect.top:
        game.player_pos.y = game.casino_rect.top
    if game.player_pos.y > game.casino_rect.bottom - PLAYER_SIZE[1]:
        game.player_pos.y = game.casino_rect.bottom - PLAYER_SIZE[1]

def show_machine_upgrades(machine):
    # Create a popup menu for machine upgrades
    upgrade_rect = pygame.Rect(200, 200, 400, 200)
    pygame.draw.rect(game.win, DARK_BG, upgrade_rect)
    pygame.draw.rect(game.win, WHITE, upgrade_rect, 2)
    
    title = game.ui_font.render(f"Upgrade {machine.data['name']}", True, WHITE)
    game.win.blit(title, (upgrade_rect.x + 20, upgrade_rect.y + 20))
    
    # Upgrade options
    options = [
        ("Speed", machine.upgrades["speed"], machine.upgrade_cost("speed"), machine.can_upgrade("speed")),
        ("Odds", machine.upgrades["odds"], machine.upgrade_cost("odds"), machine.can_upgrade("odds")),
        ("Payout", machine.upgrades["payout"], machine.upgrade_cost("payout"), machine.can_upgrade("payout"))
    ]
    
    option_rects = []
    for i, (name, level, cost, can_upgrade) in enumerate(options):
        if level >= 3:
            text = f"{name}: MAX"
        elif can_upgrade:
            text = f"{name} (Lvl {level + 1}): ${cost}"
        else:
            text = f"{name}: MAX"
        
        text_surface = game.ui_font.render(text, True, WHITE if can_upgrade else GRAY)
        rect = pygame.Rect(upgrade_rect.x + 20, upgrade_rect.y + 60 + i * 40, 360, 30)
        option_rects.append((rect, name, can_upgrade))
        
        pygame.draw.rect(game.win, (80, 80, 80) if can_upgrade else (50, 50, 50), rect)
        game.win.blit(text_surface, (rect.x + 10, rect.y + 5))
    
    pygame.display.update()
    
    # Wait for player to click an option or click away
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Check if clicked on an upgrade option
                clicked = False
                for rect, name, can_upgrade in option_rects:
                    if rect.collidepoint(mouse_pos) and can_upgrade:
                        if machine.upgrade(name.lower()):
                            waiting = False
                            clicked = True
                            break
                
                # If clicked outside, close the menu
                if not clicked and not upgrade_rect.collidepoint(mouse_pos):
                    waiting = False
        
        game.clock.tick(FPS)

def buy_casino_upgrade(upgrade_key):
    upgrade = casino_upgrades[upgrade_key]
    if upgrade["current_level"] < upgrade["max_level"]:
        cost = upgrade["cost"] * (upgrade["current_level"] + 1)
        if game.money >= cost:
            game.money -= cost
            upgrade["current_level"] += 1
            return True
    return False

def main():
    global game
    game = GameState()
    
    while True:
        game.clock.tick(FPS)
        
        # Spawn NPCs periodically
        game.spawn_timer += 1
        if game.spawn_timer > game.spawn_rate:
            spawn_npc()
            game.spawn_timer = 0
        
        # Update game state
        handle_events()
        
        # Update NPCs
        for npc in game.npcs[:]:
            npc.update()
        
        # Update machine cooldowns
        for machine in game.machines:
            if machine.cooldown > 0:
                machine.cooldown -= 1
        
        # Update effects
        game.update_effects()
        
        # Draw everything
        draw_window()

if __name__ == "__main__":
    main()