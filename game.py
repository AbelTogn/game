import os

from os import listdir
from os.path import isfile, join
from typing import Optional

import pygame

# Initialize pygame
pygame.init()

# Set up the window
pygame.display.set_caption("Platformer")

# Set window dimensions and frames per second
WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5
BLOCK_SIZE = 96
font = pygame.font.Font(None, 36)
colors = [(255, 0, 0),(0, 0, 0)]

# Create the game window
window = pygame.display.set_mode((WIDTH, HEIGHT))


# Function to load sprite sheets
def load_sprite_sheets(directory_1, directory_2, width, height, direction=False) -> dict:
    path = join("assets", directory_1, directory_2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []

        # Split sprite sheet into individual sprites
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        # Store sprites in dictionary, handling direction if specified
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = [pygame.transform.flip(sprite, True, False) for sprite
                                                                in sprites]
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


# Function to get block image
def get_block(size: float) -> pygame.Surface:
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


# Define Player class
class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        super().__init__()
        # Initialize player attributes
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

    # Method to make the player jump
    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    # Method to move the player
    def move(self, dx: int, dy: int) -> None:
        self.rect.x += dx
        self.rect.y += dy

    # Method to handle player being hit by enemies
    def make_hit(self, enemy_object: object) -> None:
        enemy_object_class = type(enemy_object).__name__
        if enemy_object_class == "Fire" or enemy_object_class == "Enemy":
            if not self.invincible:
                self.invincible = True
                self.invincible_count = FPS * 3
                self.lives -= 1

    # Method to move player left
    def move_left(self, vel: int) -> None:
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    # Method to move player right
    def move_right(self, vel: int) -> None:
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    # Method to update player state and animation
    def loop(self, FPS: int) -> None:
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
        self.y_vel += min(1, (self.fall_count / FPS) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > FPS * 2:
            self.hit = False
            self.hit_count = 0

        self.update_sprite()

    # Method to handle player landing
    def landed(self) -> None:
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    # Method to handle player hitting ceiling
    def hit_head(self) -> None:
        self.count = 0
        self.y_vel *= -1

    # Method to update player sprite based on state
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

    # Method to update player position and mask
    def update(self) -> None:
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    # Method to draw player on screen
    def draw(self, win: pygame.Surface, offset_x: int) -> None:
        if self.invincible and (self.invincible_count // 10) % 2 == 0:
            win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))
        elif not self.invincible:
            win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Enemy(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 0.5  # Adjust gravity as needed
    SPRITES = load_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x: int, y: int, width: int, height: int, name=None) -> None:
        super().__init__()
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

    def loop(self, FPS: int, objects: list) -> None:
        on_ground = False
        for obj in objects:
            if isinstance(obj, Block) and obj.rect.colliderect(self.rect.move(0, self.y_vel + 1)):
                on_ground = True
                self.rect.bottom = obj.rect.top  # Adjust position to be just above the ground
                self.y_vel = 0  # Stop falling
                break

        if not on_ground:
            # Apply gravity to make the enemy fall when not on the ground
            self.y_vel += self.GRAVITY

        self.move(0, self.y_vel)
        self.update_sprite()

    def handle_collision(self, objects: list) -> None:
        for obj in objects:
            if pygame.sprite.collide_rect(self, obj):
                if self.rect.colliderect(obj.rect):  # Check for collision with object
                    if self.y_vel > 0:  # If falling downwards
                        self.rect.bottom = obj.rect.top  # Adjust position to be just above the ground
                        self.fall_count = 0  # Reset fall count
                        self.y_vel = 0  # Stop falling
                    elif self.y_vel < 0:  # If moving upwards
                        self.rect.top = obj.rect.bottom  # Adjust position below the ceiling
                        self.y_vel = 0  # Stop moving upwards

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

class Button:
    def __init__(self, text: str, font: pygame.font.Font, x: int, y: int, width: int, height: int) -> None:
        self.text = text
        self.font = font
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.colors = [(255, 0, 0), (0, 0, 0)]  # Red background, black text

    def draw(self, window: pygame.Surface) -> None:
        pygame.draw.rect(window, self.colors[0], (self.x, self.y, self.width, self.height))
        text_surface = self.font.render(self.text, True, self.colors[1])
        text_rect = text_surface.get_rect(center=(self.x + self.width / 2, self.y + self.height / 2))
        window.blit(text_surface, text_rect)
        


def get_background(name: str) -> tuple:
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw_background(window: pygame.Surface, background: list, bg_image: pygame.Surface) -> None:
    for tile in background:
        window.blit(bg_image, tile)


def draw_objects(window: pygame.Surface, objects: list, offset_x: int) -> None:
    for obj in objects:
        obj.draw(window, offset_x)


def draw(window: pygame.Surface, background: list, bg_image: pygame.Surface,
         player: object, enemy: object, fire: object, objects: list, offset_x: int) -> None:
    draw_background(window, background, bg_image)
    draw_objects(window, objects, offset_x)
    fire.draw(window, offset_x)
    player.draw(window, offset_x)
    enemy.draw(window, offset_x)
    pygame.display.update()


def handle_vertical_collision(character: object, objects: list, dy: int) -> list:
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(character, obj):
            if dy > 0:
                character.rect.bottom = obj.rect.top
                character.landed()
            elif dy < 0:
                character.rect.top = obj.rect.bottom + 1  # Fix to avoid continuous collision
                if isinstance(character, Player):  # Check if character is Player
                    character.hit_head()
                elif isinstance(character, Enemy):  # Check if character is Enemy
                    character.rect.bottom = obj.rect.bottom  # Adjust position to be at same level as obstacle
                    character.y_vel = 0  # Stop upward movement for enemy
            collided_objects.append(obj)

    return collided_objects


def collide(character: object, objects: list, dx: int) -> Optional[object]:
    character.move(dx, 0)
    character.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(character, obj):
            collided_object = obj
            break

    character.move(-dx, 0)
    character.update()
    return collided_object


def handle_move(player: object, first_enemy: object, objects: list) -> None:
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if isinstance(obj, Fire):  # Check if obj is an instance of the Fire class
            player.make_hit(obj)  # Handle collision with fire
        elif obj == first_enemy:  # Check if obj is the first enemy
            player.make_hit(first_enemy)  # Handle collision with first enemy

    # Adjust enemy movement
    enemy_on_ground = False
    for obj in objects:
        if isinstance(obj, Block) and obj.rect.colliderect(first_enemy.rect.move(0, 1)):
            enemy_on_ground = True
            break

    if enemy_on_ground:
        # If enemy is on the ground, reset its vertical velocity
        first_enemy.y_vel = 0
    else:
        # Apply gravity to make the enemy fall when not on the ground
        first_enemy.y_vel += min(1, (first_enemy.fall_count / FPS) * first_enemy.GRAVITY)

    # Update enemy's horizontal movement
    first_enemy.move(first_enemy.x_vel, 0)

    # Move enemy vertically
    first_enemy.move(0, first_enemy.y_vel)

    # Update enemy's sprite
    first_enemy.update_sprite()
    first_enemy.update_sprite()


def main(window: pygame.Surface):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    block_size = 96

    player = Player(0, HEIGHT - block_size, 50, 50)
    first_enemy = Enemy(block_size * 6, HEIGHT - block_size * 4, 50, 50)
    gameOver_button = Button("Retry ?", font, WIDTH//2, HEIGHT//2, 200, 100)
    fire = Fire(block_size * 2, HEIGHT - block_size - 64, 16, 32)
    fire.on()
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-100, 100)]

    base = [Block(block_size * (4 + i), HEIGHT - block_size * 2, block_size) for i in range(5)]
    first_floor = [Block(block_size * (5 + i), HEIGHT - block_size * 3, block_size) for i in range(3)]
    pyramid = [*base, *first_floor, Block(block_size * 6, HEIGHT - block_size * 4, block_size)]

    left_tower = [Block(block_size * -4, HEIGHT - block_size * (2 + 2 * i), block_size) for i in range(5)]

    objects = [*floor, *pyramid, *left_tower, fire, first_enemy]
    offset_x = 0
    scroll_area_width = 200

    # Set enemy's initial velocity to move left
    first_enemy.x_vel = -2  # Adjust as needed

    run = True
    while run:
        clock.tick(FPS)

        lives_text = font.render(f"Lives: {player.lives}", True, (0, 0, 0))
        window.blit(lives_text, (10, 10))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_SPACE or event.key == pygame.K_UP) and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        first_enemy.loop(FPS, objects)
        fire.loop()
        handle_move(player, first_enemy, objects)
        draw(window, background, bg_image, player, first_enemy, fire, objects, offset_x)

        if player.rect.y > HEIGHT:
            player.lives = 0

        if player.lives == 0:
            gameOver_button.draw(window)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)


