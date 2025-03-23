import pygame
import time

# Initialize Pygame
pygame.init()

# Set window dimensions
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Racing Game")

# Colors
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
yellow = (255, 255, 0)
gray = (100, 100, 100)
dark_gray = (50, 50, 50)
grass_green = (100, 200, 100)

# Car dimensions
car_width = 50
car_height = 30
car_x = width // 2 - car_width // 2
car_y = height - 2 * car_height
car_speed = 0
car_angle = 0
car_acceleration = 0.2
car_deceleration = 0.1
car_rotation_speed = 3
max_speed = 5

# Track dimensions
track_width = width * 3
track_height = height
track_x = 0

# Lap counter
laps = 0
finish_line_x = track_width - 50
font = pygame.font.Font(None, 36)

# Timer
start_time = time.time()
end_time = 0
race_finished = False

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                car_angle += car_rotation_speed
            if event.key == pygame.K_RIGHT:
                car_angle -= car_rotation_speed
            if event.key == pygame.K_UP:
                car_speed += car_acceleration
            if event.key == pygame.K_DOWN:
                car_speed -= car_acceleration
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_UP and car_speed > 0:
                car_speed -= car_deceleration
            if event.key == pygame.K_DOWN and car_speed < 0:
                car_speed += car_deceleration

    # Decelerate if no key is pressed
    if car_speed > 0:
        car_speed -= car_deceleration
        if car_speed < 0:
            car_speed = 0
    elif car_speed < 0:
        car_speed += car_deceleration
        if car_speed > 0:
            car_speed = 0

    # Limit speed
    if car_speed > max_speed:
        car_speed = max_speed
    elif car_speed < -max_speed:
        car_speed = -max_speed

    # Move track
    track_x -= car_speed
    if track_x < -(track_width - width):
        track_x = -(track_width - width)
    if track_x > 0:
        track_x = 0

    # Check for lap completion
    if car_x > finish_line_x - track_x and not race_finished:
        laps += 1
        if laps == 3:
            race_finished = True
            end_time = time.time()
            total_time = end_time - start_time
    if track_x < -(track_width - width):
        track_x = -(track_width - width)
    if track_x > 0:
        track_x = 0

    # Draw everything
    screen.fill(grass_green)

    # Draw track
    pygame.draw.rect(screen, gray, (track_x, 0, track_width, track_height))

    # Draw road markings
    for i in range(20):
        pygame.draw.rect(screen, yellow, (track_x + i * 400, height // 2 - 5, 200, 10))
        pygame.draw.rect(screen, white, (track_x + i * 400 + 100, height // 2 - 5, 50, 10))

    # Draw finish line
    pygame.draw.rect(screen, red, (finish_line_x + track_x, 0, 5, height))
    pygame.draw.rect(screen, white, (finish_line_x + track_x + 5, 0, 5, height))

    # Draw car
    pygame.draw.rect(screen, red, (car_x, car_y, car_width, car_height))

    # Display laps
    laps_text = font.render(f"Laps: {laps}", True, white)
    screen.blit(laps_text, (10, 10))

    # Display timer
    if not race_finished:
        current_time = time.time() - start_time
        timer_text = font.render(f"Time: {current_time:.2f}", True, white)
        screen.blit(timer_text, (10, 50))
    else:
        timer_text = font.render(f"Finished in: {total_time:.2f} seconds", True, white)
        screen.blit(timer_text, (width // 2 - 150, height // 2))

    pygame.display.update()

# Quit Pygame
pygame.quit()
