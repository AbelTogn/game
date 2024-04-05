# Importe les librairies nécessaires
from os import listdir
from os.path import isfile, join
from typing import Optional
from Class import *

import pygame
import cv2

# Initialise pygame
pygame.init()

# Met en place la fenètre
pygame.display.set_caption("Platformer")

# Met en place les diemnsions de la fenètre, le nombre de frames par seconde et les crédits
WIDTH, HEIGHT = 1000, 800
FPS = 60
CREDITS = 3
# Met en place la vitesse du personnage et la taille d'un bloc
PLAYER_VEL = 5
BLOCK_SIZE = 96
# Crée la police d'écriture et les couleurs
font = pygame.font.Font(None, 36)
colors = [(255, 0, 0), (0, 0, 0)]

gameOver = False

# Crée la fenètre de jeu
window = pygame.display.set_mode((WIDTH, HEIGHT))


# Fonction pour charger les sprites
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


# Fonction pour trouver l'images des blocks
def get_block(size: float) -> pygame.Surface:
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


def get_background(name: str) -> tuple:
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


# noinspection PyPep8Naming
def draw_background(WINDOW: pygame.Surface, background: list, bg_image: pygame.Surface) -> None:
    for tile in background:
        WINDOW.blit(bg_image, tile)


# noinspection PyPep8Naming
def draw_objects(WINDOW: pygame.Surface, objects: list, offset_x: int) -> None:
    for obj in objects:
        obj.draw(WINDOW, offset_x)


# noinspection PyPep8Naming
def draw(WINDOW: pygame.Surface, background: list, bg_image: pygame.Surface,
         player: object, enemy: object, fire: object, objects: list, offset_x: int) -> None:
    draw_background(WINDOW, background, bg_image)
    draw_objects(WINDOW, objects, offset_x)
    fire.draw(WINDOW, offset_x)
    player.draw(WINDOW, offset_x)
    enemy.draw(WINDOW, offset_x)


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


# noinspection PyPep8Naming
def main(WINDOW: pygame.Surface, credits):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    block_size = 96

    player = Player(0, HEIGHT - block_size, 50, 50)
    first_enemy = Enemy(block_size * 6, HEIGHT - block_size * 4, 50, 50)
    gameOver_button = Button("Retry ?", font, (WIDTH - 200) // 2, (HEIGHT - 100) // 2, 200, 100)
    insertCoins_button = Button("Insert coins", font, (WIDTH - 200) // 2, (HEIGHT - 100) // 2, 200, 100)
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
    scene_name = "First Level"
    while run:

        clock.tick(FPS)

        lives_text = font.render(f"Lives: {player.lives}", True, (0, 0, 0))
        WINDOW.blit(lives_text, (10, 10))

        credits_text = font.render(f"Credits: {credits}", True, (0, 0, 0))
        WINDOW.blit(credits_text, (10, 50))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_SPACE or event.key == pygame.K_UP) and player.jump_count < 2:
                    player.jump()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if (WIDTH - 200) // 2 <= event.pos[0] <= (WIDTH - 200) // 2 + 200 and \
                        (HEIGHT - 100) // 2 <= event.pos[1] <= (HEIGHT - 100) // 2 + 100:
                    if scene_name == "First Level":
                        del player
                        del first_enemy
                        player = Player(0, HEIGHT - block_size, 50, 50)
                        first_enemy = Enemy(block_size * 6, HEIGHT - block_size * 4, 50, 50)
                        objects = [*floor, *pyramid, *left_tower, fire, first_enemy]
                        first_enemy.x_vel = -2
                        credits -= 1
                    elif scene_name == "Game Over":
                        pass

        player.loop(FPS)
        first_enemy.loop(objects)
        fire.loop()
        handle_move(player, first_enemy, objects)
        draw(WINDOW, background, bg_image, player, first_enemy, fire, objects, offset_x)

        if scene_name == "First Level":

            if player.rect.y > HEIGHT:
                player.lives = 0

            if credits == 0 and player.lives == 0:
                scene_name = "Game Over"
            else:
                scene_name = "First Level"

            if scene_name == "Game Over":
                insertCoins_button.draw(WINDOW)
            elif player.lives == 0 and scene_name != "Game Over":
                gameOver_button.draw(WINDOW)
                player.rect.x = WIDTH // 2
                player.rect.y = HEIGHT

            if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                    (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
                offset_x += player.x_vel

        elif scene_name == "Game Over":
            insertCoins_button.draw(WINDOW)

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window, CREDITS)
