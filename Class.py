import pygame
from game import *


# Définit la classe Player (joueur)
class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        super().__init__()
        # Initialise les attributs du joueur
        self.sprite = None
        self.count = None
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel, self.y_vel = 0, 0
        self.mask = None
        self.direction = "right"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.lives = 3
        self.invincible = False
        self.invincible_count = 0

    # Méthode pour faire sauter le joueur
    def jump(self):

        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    # Méthode pour déplacer le joueur
    def move(self, dx: int, dy: int) -> None:
        self.rect.x += dx
        self.rect.y += dy

    # Méthode pour gérer la prise de dégats du joueur
    def make_hit(self, enemy_object: object) -> None:
        enemy_object_class = type(enemy_object).__name__
        if enemy_object_class == "Fire" or enemy_object_class == "Enemy":
            if not self.invincible:
                self.invincible = True
                self.invincible_count = FPS * 3
                self.lives -= 1

    # Méthode pour faire aller le joueur à gauche
    def move_left(self, vel: int) -> None:
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    # Méthode pour faire aller le joueur à droite
    def move_right(self, vel: int) -> None:
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    # Méthode pour gérer la mise à jour du sprite et son état
    def loop(self, fps: int) -> None:
        if self.invincible:
            self.invincible_count -= 1
            if self.invincible_count <= 0:
                self.invincible = False
                self.invincible_count = 0

        if self.invincible:
            self.invincible_count -= 1
            if self.invincible_count <= 0:
                self.invincible = False

        self.fall_count += 1
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.update_sprite()

    # Méthode pour gérer l'atterissage du joueur
    def landed(self) -> None:
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    # Méthode pour gérer quand le personnage touche le bas d'un bloc avec la tête
    def hit_head(self) -> None:
        self.count = 0
        self.y_vel *= -1

    # Méthode pour changer le sprite du joueur en fonction de son état
    def update_sprite(self) -> None:
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    # Méthode pour mettre à jour le sprite et le masque du joueur
    def update(self) -> None:
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    # Méthode pour afficher le joueut à l'écran
    def draw(self, win: pygame.Surface, offset_x: int) -> None:
        if self.invincible and (self.invincible_count // 10) % 2 == 0:
            win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))
        elif not self.invincible:
            win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


# Crée la classe Enemy (ennemi)
class Enemy(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 0.5  # Adjust gravity as needed
    SPRITES = load_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        super().__init__()
        self.sprite = None
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel, self.y_vel = 0, 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.hit = False
        self.hit_count = 0

    def move(self, dx: int, dy: int) -> None:
        self.rect.x += dx
        self.rect.y += dy

    def loop(self, objects: list) -> None:
        on_ground = False
        for obj in objects:
            if isinstance(obj, Block) and obj.rect.colliderect(self.rect.move(0, self.y_vel + 1)):
                on_ground = True
                self.rect.bottom = obj.rect.top
                self.y_vel = 0
                break

        if not on_ground:
            self.y_vel += self.GRAVITY

        self.move(0, self.y_vel)
        self.update_sprite()

    def handle_collision(self, objects: list) -> None:
        for obj in objects:
            if pygame.sprite.collide_rect(self, obj):
                if self.rect.colliderect(obj.rect):
                    if self.y_vel > 0:
                        self.rect.bottom = obj.rect.top
                        self.fall_count = 0
                        self.y_vel = 0
                    elif self.y_vel < 0:
                        self.rect.top = obj.rect.bottom
                        self.y_vel = 0

    def update_sprite(self) -> None:
        sprite_sheet_name = "run_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self) -> None:
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win: pygame.Surface, offset_x: int) -> None:
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


# Define Object class
class GameObject(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, width: int, height: int, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win: pygame.Surface, offset_x: int) -> None:
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


# Define Block class
class Block(GameObject):
    def __init__(self, x: int, y: int, size: int):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


# Define Fire class
class Fire(GameObject):
    ANIMATION_DELAY = 3

    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self) -> None:
        self.animation_name = "on"

    def off(self) -> None:
        self.animation_name = "off"

    def loop(self) -> None:
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


# noinspection PyPep8Naming
class Button:
    def __init__(self, text: str, FONT: pygame.font.Font, x: int, y: int, width: int, height: int) -> None:
        self.text = text
        self.font = FONT
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.colors = [(255, 0, 0), (0, 0, 0)]  # Red background, black text

    def draw(self, WINDOW: pygame.Surface) -> None:
        pygame.draw.rect(WINDOW, self.colors[0], (self.x, self.y, self.width, self.height))
        text_surface = self.font.render(self.text, True, self.colors[1])
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        WINDOW.blit(text_surface, text_rect)
