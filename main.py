import pygame
import threading
import math
import time

pygame.init()
clock = pygame.time.Clock()
display_width = 1202
display_height = 540
scoreboard_x = display_width // 2
scoreboard_y = 5
fps = 30
background_img_offset = [-67, -95]
bullseye_center = [967 + background_img_offset[0], 362 + background_img_offset[1]]
default_shot_point = [316 + background_img_offset[0], 362 + background_img_offset[1]]

game_display = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption('Curling Shootout')

background_img = pygame.image.load('curling lane.png')
font = pygame.font.SysFont('freesansbold.ttf', 24)
"""Color definitions"""
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 50, 0)
blue = (0, 50, 255)
"""physics constants"""
stone_radius = 15
stone_mass = 10# kg
gravity = 9.81
force_friction = 1# N
stone_acceleration = force_friction / stone_mass
dt = 1
"""scores var to pass to main"""
red_score_c = 0
blue_score_c = 0

"""Class to define the stones that are moved in the game
    They have a position, velocity, mass, and acceleration"""


class Stone:
    def __init__(self, x_position, y_position, x_velocity, y_velocity, color):
        self.radius = stone_radius
        self.velocity = pygame.math.Vector2(float(x_velocity), float(y_velocity))
        self.acceleration = self.set_acceleration_direction()
        self.position = pygame.math.Vector2(x_position, y_position)
        self.color = color

    def draw_stone(self):
        pygame.draw.circle(game_display, black, (self.position.x, self.position.y), self.radius + 1)
        pygame.draw.circle(game_display, self.color, (self.position.x, self.position.y), self.radius)

    def set_acceleration_direction(self):
        velo_unit = self.velocity.normalize()
        acceleration = (-stone_acceleration * velo_unit)
        return acceleration


def draw_scoreboard(red_score, blue_score):
    font2 = pygame.font.Font('freesansbold.ttf', 32)
    red_name_str = 'RED TEAM'
    blue_name_str = 'BLUE TEAM'
    score_str = str(red_score) + ' - ' + str(blue_score)
    score_text = font2.render(score_str, True, black)
    red_name_text = font2.render(red_name_str, True, red)
    blue_name_text = font2.render(blue_name_str, True, blue)
    score_rect = score_text.get_rect()
    red_name_rect = red_name_text.get_rect()
    blue_name_rect = blue_name_text.get_rect()
    score_rect.center = (scoreboard_x, scoreboard_y + 25)
    red_name_rect.center = (scoreboard_x - 145, scoreboard_y + 25)
    blue_name_rect.center = (scoreboard_x + 155, scoreboard_y + 25)
    game_display.blit(score_text, score_rect)
    game_display.blit(blue_name_text, blue_name_rect)
    game_display.blit(red_name_text, red_name_rect)


def gameplay():
    """ Display instructions at bottom of screen"""
    text = "LEFT/RIGHT= change speed - UP/DOWN= change launch point - A/D= change launch angle - SPACE= shoot"
    text_img = font.render(text, True, black)
    game_display.blit(text_img, (200, 500))


"""Draw the display and the circles again"""


def update_display(stone_list):
    game_display.blit(background_img, background_img_offset)
    pygame.draw.circle(game_display, black, (bullseye_center[0], bullseye_center[1]), 2)
    gameplay()
    for stone in stone_list:
        stone.draw_stone()
    pygame.display.flip()


"""
Gets the closest stone to the bullseye from each team and returns winner
"""


def evaluate_board(red_stones, blue_stones):
    best_red = 3000.0
    best_blue = 3000.0
    for stone in red_stones:
        position_magnitude = math.sqrt((bullseye_center[0] - stone.position.x)**2
                                       + (bullseye_center[1] - stone.position.y) ** 2)
        if position_magnitude < best_red:
            best_red = position_magnitude
    for stone in blue_stones:
        position_magnitude = math.sqrt((bullseye_center[0] - stone.position.x)**2 +
                                       (bullseye_center[1] - stone.position.y) ** 2)
        if position_magnitude < best_blue:
            best_blue = position_magnitude
    if best_red < best_blue:
        return 1
    elif best_blue < best_red:
        return 2
    else:
        return 0


"""
All the user interface control to move velocity vector and the position of stone 
"""


def aim_stone(stone, stone_list, scores):

    line_end_point = pygame.math.Vector2(stone.position.x + 120, stone.position.y)
    keep_aiming = True
    while keep_aiming:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    stone.position.y -= 5
                if event.key == pygame.K_DOWN:
                    stone.position.y += 5
                if event.key == pygame.K_LEFT:
                    guide_line = pygame.math.Vector2(line_end_point.x - stone.position.x,
                                                     line_end_point.y - stone.position.y)
                    """Decrease magnitude of guide line"""
                    add_vect = guide_line.normalize()
                    new_guide_line = guide_line - add_vect * 2

                    line_end_point[0] = stone.position.x + new_guide_line.x
                    line_end_point[1] = stone.position.y + new_guide_line.y
                if event.key == pygame.K_RIGHT:
                    guide_line = pygame.math.Vector2(line_end_point.x - stone.position.x,
                                                     line_end_point.y - stone.position.y)
                    add_vect = guide_line.normalize()
                    """Increase magnitude of guide line"""
                    new_guide_line = guide_line + add_vect * 2

                    line_end_point.x = stone.position.x + new_guide_line.x
                    line_end_point.y = stone.position.y + new_guide_line.y
                if event.key == pygame.K_a:
                    guide_line = pygame.math.Vector2(line_end_point.x - stone.position.x,
                                                     line_end_point.y - stone.position.y)
                    """Get angle of guide line and rotate clockwise by 2 degrees"""
                    current_angle = round(math.atan(guide_line.y / guide_line.x))
                    current_angle -= 2
                    line_end_point = stone.position + guide_line.rotate(current_angle)
                if event.key == pygame.K_d:
                    guide_line = pygame.math.Vector2(line_end_point.x - stone.position.x,
                                                     line_end_point.y - stone.position.y)
                    """Get angle of guide line and rotate counterclockwise by 2 degrees"""
                    current_angle = round(math.atan(guide_line.y / guide_line.x))
                    current_angle += 2
                    line_end_point = stone.position + guide_line.rotate(current_angle)
                if event.key == pygame.K_SPACE:
                    keep_aiming = False

                update_display(stone_list)
                pygame.draw.line(game_display, black, (stone.position.x, stone.position.y),
                                 (line_end_point.x, line_end_point.y), 3)
                draw_scoreboard(scores[0], scores[1])
                pygame.display.flip()
# returns the guideline vector divided by 10 to give velocity of stone
    return (line_end_point - stone.position)/10


"""
Clears a collision by moving stone 2 to not be overlapping stone 1
This method fixes infinite recursion error
"""


def clear_collision(stone1, stone2):
    d = pygame.math.Vector2(stone2.position.x - stone1.position.x,
                            stone2.position.y - stone1.position.y)
    distance = math.sqrt(d.x**2 + d.y**2)
    # angle of line connecting center of stones
    angle = math.atan2(stone2.position.y - stone1.position.y, stone2.position.x - stone1.position.x)
    # update position of stone2 to get rid of overlap

    stone2.position.x += math.cos(angle) * (distance/3)
    stone2.position.y += math.sin(angle) * (distance/3)


"""
Method to detect a collision between the stone moving and all the other stones
Returns whether a collision occurred and the stone involved in the collision
"""


def detect_collision(stone, stone_list):
    for current_stone in stone_list:
        if current_stone.position != stone.position:
            d = pygame.math.Vector2(current_stone.position.x - stone.position.x,
                                    current_stone.position.y - stone.position.y)
            distance = math.sqrt(d.x**2 + d.y**2)
            if distance < 2 * stone_radius:
                return True, d, current_stone
    d = pygame.math.Vector2(0, 0)
    return False, d, stone


"""
Method to execute physics of a shot moving
"""


def execute_shot(shot_velocity, stone_shot, stone_list, scores):
    # set the velocity of the stone to the velocity returned by aim()
    stone_shot.velocity = shot_velocity
    # sets acceleration for stone
    stone_shot.set_acceleration_direction()
    # check whether the stone is moving or not in any direction
    while math.fabs(stone_shot.velocity.x) > .5 or math.fabs(stone_shot.velocity.y) > .5:
        # first check whether there is a collision
        collision, colliding_direction, stone_collided = detect_collision(stone_shot, stone_list)
        if collision:
            # if there is a collision save pre collision velocity of stone1
            stone_1_init_velo = stone_shot.velocity
            # get angle of collision between stones
            collision_angle = math.atan2(stone_collided.position.y - stone_shot.position.y,
                                         stone_collided.position.x - stone_shot.position.x)
            # clear the collision
            clear_collision(stone_shot, stone_collided)
            # set velocity of stone that got hit. This is the velocity of the stone1 *cos/sin(angle between 2 stones)
            stone_collided.velocity.x = stone_shot.velocity.magnitude()*math.cos(collision_angle)
            stone_collided.velocity.y = stone_shot.velocity.magnitude()*math.sin(collision_angle)
            # new velocity of stone 1 is the vector subtraction of the initial velocity and the stone collided velocity
            stone_shot.velocity = stone_1_init_velo - stone_collided.velocity
            # allow both stones to move simultaneously by creating a new process thread
            thread = threading.Thread(target=execute_shot, args=(stone_collided.velocity,
                                                                 stone_collided, stone_list, scores))
            thread.start()
            # check whether the stone is hitting the walls of the ice lane
        if stone_shot.position.y > 560 + background_img_offset[1]:
            stone_shot.velocity.y *= -1
        elif stone_shot.position.y < 175 + background_img_offset[1]:
            stone_shot.velocity.y *= -1
        if stone_shot.position.x > 1170 + background_img_offset[0]:
            stone_shot.velocity.x *= -1
        # execute kinematics on the stone
        # get the accel for this iteration
        stone_shot.acceleration = stone_shot.set_acceleration_direction()
        # position = velo*dt
        # velocity = acc*dt
        stone_shot.position += stone_shot.velocity * dt
        stone_shot.velocity += stone_shot.acceleration * dt
        stone_shot.acceleration = stone_shot.set_acceleration_direction()
        update_display(stone_list)
        draw_scoreboard(scores[0], scores[1])
        pygame.display.flip()
        clock.tick(fps)
    # set stones velocity to 0 once done moving
    stone_shot.velocity.x = 0
    stone_shot.velocity.y = 0


def main():
    red_stones = []
    blue_stones = []
    stone_list = []
    red_turn = True
    current_round = 0
    red_score = 0
    blue_score = 0
    scores = [red_score, blue_score]
    # create the 6 stones used in the game, 3 per each team
    for i in range(3):
        stone_r = Stone(160.0 + background_img_offset[0], 185 + background_img_offset[1] + i * 35.0, 1, 1, red)
        stone_b = Stone(160.0 + background_img_offset[0], 548 + background_img_offset[1] - i * 35.0, 1, 1, blue)
        red_stones.append(stone_r)
        blue_stones.append(stone_b)
        stone_list.append(stone_r)
        stone_list.append(stone_b)

    update_display(stone_list)
    keep_running = True
    while keep_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                keep_running = False
            if red_turn:
                if current_round == 0:
                    # shoot first red stone
                    red_stones[0].position = pygame.math.Vector2(default_shot_point[0], default_shot_point[1])
                    shot_velocity = aim_stone(red_stones[0], stone_list, scores)
                    thread = threading.Thread(execute_shot(shot_velocity, red_stones[0], stone_list, scores))
                    thread.start()
                elif current_round == 1:
                    # shoot second red stone
                    red_stones[1].position = pygame.math.Vector2(default_shot_point[0], default_shot_point[1])
                    shot_velocity = aim_stone(red_stones[1], stone_list, scores)
                    thread = threading.Thread(execute_shot(shot_velocity, red_stones[1], stone_list, scores))
                    thread.start()
                else:
                    # shoot third red stone
                    red_stones[2].position = pygame.math.Vector2(default_shot_point[0], default_shot_point[1])
                    shot_velocity = aim_stone(red_stones[2], stone_list, scores)
                    thread = threading.Thread(execute_shot(shot_velocity, red_stones[2], stone_list, scores))
                    thread.start()
                red_turn = not red_turn
            else:
                if current_round == 0:
                    # shoot first blue stone
                    blue_stones[0].position = pygame.math.Vector2(default_shot_point[0], default_shot_point[1])
                    shot_velocity = aim_stone(blue_stones[0], stone_list, scores)
                    thread = threading.Thread(execute_shot(shot_velocity, blue_stones[0], stone_list, scores))
                    thread.start()
                elif current_round == 1:
                    # shoot second blue stone
                    blue_stones[1].position = pygame.math.Vector2(default_shot_point[0], default_shot_point[1])
                    shot_velocity = aim_stone(blue_stones[1], stone_list, scores)
                    thread = threading.Thread(execute_shot(shot_velocity, blue_stones[1], stone_list, scores))
                    thread.start()
                else:
                    # shoot third blue stone
                    blue_stones[2].position = pygame.math.Vector2(default_shot_point[0], default_shot_point[1])
                    shot_velocity = aim_stone(blue_stones[2], stone_list, scores)
                    thread = threading.Thread(execute_shot(shot_velocity, blue_stones[2], stone_list, scores))
                    thread.start()
                red_turn = not red_turn
                current_round += 1
            if current_round > 2:
                # reset board and update scoreboard base on winner of set
                frame_winner = evaluate_board(red_stones, blue_stones)
                time.sleep(5)
                if frame_winner == 1:
                    print("red won")
                    scores[0] += 1
                elif frame_winner == 2:
                    print("blue won")
                    scores[1] += 1
                else:
                    print("its a tie")
                current_round = 0

                for i in range(3):
                    red_stones[i].position.x = 160.0 + background_img_offset[0]
                    red_stones[i].position.y = 185 + background_img_offset[1] + i * 35.0
                    blue_stones[i].position.x = 160.0 + background_img_offset[0]
                    blue_stones[i].position.y = 548 + background_img_offset[1] - i * 35.0
        update_display(stone_list)
        draw_scoreboard(scores[0], scores[1])

        pygame.display.flip()
        clock.tick(fps)


main()
