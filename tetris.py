import pygame
import random

# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)

# Define the grid size
GRID_WIDTH = 10
GRID_HEIGHT = 20
CELL_SIZE = 30

# Define the screen size
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE

# Define the tetromino shapes
TETROMINOS = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[1, 0, 0], [1, 1, 1]],  # L
    [[0, 0, 1], [1, 1, 1]],  # J
    [[0, 1, 0], [1, 1, 1]],  # T
]

class Tetromino:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = random.choice([
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
        ])

    def rotate(self):
        rotated_shape = []
        for x in range(len(self.shape[0])):
            new_row = []
            for y in range(len(self.shape) - 1, -1, -1):
                new_row.append(self.shape[y][x])
            rotated_shape.append(new_row)
        self.shape = rotated_shape

    def draw(self, screen):
        for i, row in enumerate(self.shape):
            for j, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        screen,
                        self.color,
                        (
                            (self.x + j) * CELL_SIZE,
                            (self.y + i) * CELL_SIZE,
                            CELL_SIZE,
                            CELL_SIZE,
                        ),
                    )

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tetris")
clock = pygame.time.Clock()

# Game variables
grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
current_tetromino = None
game_over = False
score = 0

def new_tetromino():
    shape = random.choice(TETROMINOS)
    return Tetromino(GRID_WIDTH // 2 - len(shape[0]) // 2, 0, shape)

current_tetromino = new_tetromino()

def check_collision(grid, tetromino, offset_x, offset_y):
    for i, row in enumerate(tetromino.shape):
        for j, cell in enumerate(row):
            if cell:
                x = tetromino.x + j + offset_x
                y = tetromino.y + i + offset_y
                if x < 0 or x >= GRID_WIDTH or y >= GRID_HEIGHT:
                    return True
                if y >= 0 and grid[y][x]:
                    return True
    return False

def place_tetromino(grid, tetromino):
    for i, row in enumerate(tetromino.shape):
        for j, cell in enumerate(row):
            if cell:
                grid[tetromino.y + i][tetromino.x + j] = 1

def clear_lines(grid):
    lines_cleared = 0
    for i in range(GRID_HEIGHT):
        if all(grid[i]):
            del grid[i]
            grid.insert(0, [0] * GRID_WIDTH)
            lines_cleared += 1
    return lines_cleared

# Game loop
running = True
fall_time = 0
fall_speed = 500  # Milliseconds
score = 0

while running:
    delta_time = clock.get_rawtime()
    fall_time += delta_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                if not check_collision(grid, current_tetromino, -1, 0):
                    current_tetromino.x -= 1
            if event.key == pygame.K_RIGHT:
                if not check_collision(grid, current_tetromino, 1, 0):
                    current_tetromino.x += 1
            if event.key == pygame.K_DOWN:
                if not check_collision(grid, current_tetromino, 0, 1):
                    current_tetromino.y += 1
            if event.key == pygame.K_UP:
                rotated_tetromino = Tetromino(current_tetromino.x, current_tetromino.y, [row[:] for row in current_tetromino.shape]) # Create a copy of the shape
                rotated_tetromino.rotate()
                if not check_collision(grid, rotated_tetromino, 0, 0):
                    current_tetromino.rotate()

    if fall_time > fall_speed:
        fall_time = 0
        if not check_collision(grid, current_tetromino, 0, 1):
            current_tetromino.y += 1
        else:
            place_tetromino(grid, current_tetromino)
            lines_cleared = clear_lines(grid)
            score += lines_cleared * 100
            current_tetromino = new_tetromino()
            if check_collision(grid, current_tetromino, 0, 0):
                game_over = True
                running = False

    # Clear the screen
    screen.fill(BLACK)

    if game_over:
        font = pygame.font.Font(None, 50)
        text = font.render("Game Over", True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(text, text_rect)

        score_text = font.render(f"Score: {score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(score_text, score_rect)

        restart_text = font.render("Press SPACE to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(restart_text, restart_rect)

        pygame.display.flip()

        waiting_for_restart = True
        while waiting_for_restart:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    waiting_for_restart = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Reset game variables
                        grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
                        current_tetromino = new_tetromino()
                        game_over = False
                        score = 0
                        waiting_for_restart = False
        continue
    else:
        # Draw the grid
        for i in range(GRID_HEIGHT):
            for j in range(GRID_WIDTH):
                if grid[i][j]:
                    pygame.draw.rect(
                        screen,
                        GRAY,
                        (j * CELL_SIZE, i * CELL_SIZE, CELL_SIZE, CELL_SIZE),
                        0,
                    )
                else:
                    pygame.draw.rect(
                        screen,
                        WHITE,
                        (j * CELL_SIZE, i * CELL_SIZE, CELL_SIZE, CELL_SIZE),
                        1,
                    )

        # Draw the current tetromino
        if current_tetromino:
            current_tetromino.draw(screen)

        # Display the score
        font = pygame.font.Font(None, 36)
        text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(text, (10, 10))

    # Update the display
    pygame.display.flip()

    # Limit frame rate
    clock.tick(60)

# Quit Pygame
pygame.quit()
