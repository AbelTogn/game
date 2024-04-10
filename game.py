# Importation des bibliothèques nécessaires
from os import listdir
from os.path import isfile, join
from typing import Optional
from Class import *  # Importation des classes personnalisées

import pygame
import cv2

# Initialisation de Pygame
pygame.init()

# Configuration de la fenêtre de jeu
pygame.display.set_caption("Platformer")
WIDTH, HEIGHT = 1000, 800
FPS = 60
CREDITS = 3
PLAYER_VEL = 5
BLOCK_SIZE = 96
font = pygame.font.Font(None, 36)
colors = [(255, 0, 0), (0, 0, 0)]

gameOver = False
window = pygame.display.set_mode((WIDTH, HEIGHT))


# Fonction pour charger les feuilles de sprites
def load_sprite_sheets(directory_1, directory_2, width, height, direction=False) -> dict:
    # Recherche des fichiers d'images dans le répertoire spécifié
    path = join("assets", directory_1, directory_2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        # Chargement de la feuille de sprite
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []

        # Découpage de la feuille de sprite en sprites individuels
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        # Stockage des sprites dans un dictionnaire, gestion de la direction si spécifié
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = [pygame.transform.flip(sprite, True, False) for sprite
                                                                in sprites]
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


# Fonction pour obtenir l'image des blocs
def get_block(size: float) -> pygame.Surface:
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


# Fonction pour obtenir l'arrière-plan
def get_background(name: str) -> tuple:
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


# Fonction pour dessiner l'arrière-plan
def draw_background(WINDOW: pygame.Surface, background: list, bg_image: pygame.Surface) -> None:
    for tile in background:
        WINDOW.blit(bg_image, tile)


# Fonction pour dessiner les objets
def draw_objects(WINDOW: pygame.Surface, objects: list, offset_x: int) -> None:
    for obj in objects:
        obj.draw(WINDOW, offset_x)


# Fonction pour dessiner
def draw(WINDOW: pygame.Surface, background: list, bg_image: pygame.Surface,
         player: object, enemy: object, fire: object, objects: list, offset_x: int) -> None:
    draw_background(WINDOW, background, bg_image)
    draw_objects(WINDOW, objects, offset_x)
    fire.draw(WINDOW, offset_x)
    player.draw(WINDOW, offset_x)
    enemy.draw(WINDOW, offset_x)


# Gestion des collisions verticales
def handle_vertical_collision(character: object, objects: list, dy: int) -> list:
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(character, obj):
            if dy > 0:
                character.rect.bottom = obj.rect.top
                character.landed()
            elif dy < 0:
                character.rect.top = obj.rect.bottom + 1
                if isinstance(character, Player):
                    character.hit_head()
                elif isinstance(character, Enemy):
                    character.rect.bottom = obj.rect.bottom
                    character.y_vel = 0
            collided_objects.append(obj)

    return collided_objects


# Gestion des collisions
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


# Gestion du mouvement
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
        if isinstance(obj, Fire):
            player.make_hit(obj)
        elif obj == first_enemy:
            player.make_hit(first_enemy)

    enemy_on_ground = False
    for obj in objects:
        if isinstance(obj, Block) and obj.rect.colliderect(first_enemy.rect.move(0, 1)):
            enemy_on_ground = True
            break

    if enemy_on_ground:
        first_enemy.y_vel = 0
    else:
        first_enemy.y_vel += min(1, (first_enemy.fall_count / FPS) * first_enemy.GRAVITY)

    first_enemy.move(first_enemy.x_vel, 0)
    first_enemy.move(0, first_enemy.y_vel)
    first_enemy.update_sprite()
    first_enemy.update_sprite()


# Fonction principale
def main(WINDOW: pygame.Surface, credits):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    block_size = 96

    player = Player(0, HEIGHT - block_size, 50, 50)
    first_enemy = Enemy(block_size * 5, HEIGHT - block_size * 4, 50, 50)
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

    first_enemy.x_vel = -2

    run = True
    scene_name = "First Level"
    global play
    play = True
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
                        credits += 1
                        scene_name = "First Level"
                        player.lives = 3

        player.loop(FPS)
        first_enemy.loop(objects)
        fire.loop()
        handle_move(player, first_enemy, objects)
        draw(WINDOW, background, bg_image, player, first_enemy, fire, objects, offset_x)

        if scene_name == "First Level":

            if player.rect.y > HEIGHT:
                player.lives = 0

            if credits <= 0 and player.lives == 0 and play:
                scene_name = "Game Over"
            elif not credits <= 0 and play:
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
            play = False
            player.lives = 0
            insertCoins_button.draw(WINDOW)
        print(play)

    pygame.quit()
    quit()

if __name__ == "__main__":
    main(window, CREDITS)
