import sys
from time import sleep
import pygame
from bullet import Bullet
from alien import Alien

pygame.init()

laser_sound = pygame.mixer.Sound("sounds/laser.wav")

explosion_sound = pygame.mixer.Sound("sounds/explosion.wav")

death_sound = pygame.mixer.Sound("sounds/player_dead.wav")

game_over = pygame.mixer.Sound("sounds/game_over.wav")

def check_keydown_events(event, tt_settings, screen, ship, bullets):
    """Respond to keypresses."""
    if event.key == pygame.K_RIGHT:
        ship.moving_right = True
    elif event.key == pygame.K_LEFT:
        ship.moving_left = True
    elif event.key == pygame.K_SPACE:
        fire_bullet(tt_settings, screen, ship, bullets)
    elif event.key == pygame.K_ESCAPE:
        sys.exit()

def fire_bullet(tt_settings, screen, ship, bullets):
    """Fire a bullet if limit is not reached."""
    # Create a new bullet and add it to the bullets group.
    if len(bullets) < tt_settings.bullets_allowed:
        new_bullet = Bullet(tt_settings, screen, ship)
        bullets.add(new_bullet)
        pygame.mixer.Sound.play(laser_sound)

def check_keyup_events(event, ship):
    """Respond to key releses."""
    if event.key == pygame.K_RIGHT:
        ship.moving_right = False
    if event.key == pygame.K_LEFT:
        ship.moving_left = False

def check_events(tt_settings, screen, stats, sb, play_button, ship, aliens,
        bullets):
    """Respond to keypresses and mouse events."""
    # Watch for keyboard and mouse events.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            check_keydown_events(event, tt_settings, screen, ship, bullets)
        elif event.type == pygame.KEYUP:
            check_keyup_events(event, ship)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            check_play_button(tt_settings, screen, stats, sb, play_button,
                ship, aliens, bullets, mouse_x, mouse_y)

def check_play_button(tt_settings, screen, stats, sb, play_button, ship,
        aliens, bullets, mouse_x, mouse_y):
    """Start a new game when the player clicks Play."""
    button_clicked = play_button.rect.collidepoint(mouse_x, mouse_y)
    if button_clicked and not stats.game_active:
        # Reset the game settings.
        tt_settings.initialize_dynamic_settings()

        # Hide the mouse cursor.
        pygame.mouse.set_visible(False)

        # Reset the game statistics
        stats.reset_stats()
        stats.game_active = True

        # Reset the scoreboard images.
        sb.prep_score()
        sb.prep_high_score()
        sb.prep_level()
        sb.prep_ships()

        # Empty the list of aliens and bullets.
        aliens.empty()
        bullets.empty()

        # Create a new fleet and center the ship.
        create_fleet(tt_settings, screen, ship, aliens)
        ship.center_ship()

def update_screen(tt_settings, screen, stats, sb, ship, aliens, bullets,
        play_button):
    """Update images on the screen and flip to the new screen."""
    # Redraw the screen during each pass through the loop.
    screen.fill(tt_settings.bg_color)
    # Redraw all bullets behind ship and aliens.
    for bullet in bullets.sprites():
        bullet.draw_bullet()

    ship.blitme()
    aliens.draw(screen)

    # Draw the score information.
    sb.show_score()

    # Draw the play button if the game is inactive.
    if not stats.game_active:
        play_button.draw_button()

    # Make the most recently drawn screen visible.
    pygame.display.flip()

def update_bullets(tt_settings, screen, stats, sb, ship, aliens, bullets):
    """Update position of ullets and get rid of old bullets."""
    # Update bullet positions. 
    bullets.update()

    # Get rid of bullets that have disappeared.
    for bullet in bullets.copy():
        if bullet.rect.bottom <= 0:
            bullets.remove(bullet)

    check_bullet_alien_collisions(tt_settings, screen, stats, sb, ship,
        aliens, bullets)

def check_bullet_alien_collisions(tt_settings, screen, stats, sb, ship,
        aliens, bullets):
    """Respond to bullet-alien collision."""
    # Remove any bullets and aliens that have collided
    collisions = pygame.sprite.groupcollide(bullets, aliens, True, True)

    if collisions:
        for aliens in collisions.values():
            stats.score += tt_settings.alien_points * len(aliens)
            sb.prep_score()
            pygame.mixer.Sound.play(explosion_sound)
        check_high_score(stats, sb)

    if len(aliens) == 0:
        # If the entire fleet is destroyed, start a new level
        bullets.empty()
        tt_settings.increase_speed()

        # Increase level.
        stats.level += 1
        sb.prep_level()

        create_fleet(tt_settings, screen, ship, aliens)

def get_number_aliens_x(tt_settings, alien_width):
    """Determine the number of aliens that fit in a row."""
    avaiable_space_x = tt_settings.screen_width - 2 * alien_width
    number_aliens_x = int(avaiable_space_x / (2 * alien_width))
    return number_aliens_x

def get_number_rows(tt_settings, ship_height, alien_height):
    """Determine the number of rows of aliens that fit on the screen."""
    available_space_y = (tt_settings.screen_height -
                            (3 * alien_height) - ship_height)
    number_rows = int(available_space_y / (2 * alien_height))
    return number_rows

def create_alien(tt_settings, screen, aliens, alien_number, row_number):
    """Create an alien and place it in the row."""
    alien = Alien(tt_settings, screen)
    alien_width = alien.rect.width
    alien.x = alien_width + 2 * alien_width * alien_number
    alien.rect.x = alien.x
    alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
    aliens.add(alien)

def create_fleet(tt_settings, screen, ship, aliens):
    """Create a full fleet of aliens."""
    # Create an alien and find the number of aliens in a row.
    # Spacing between each alien is equal to one alien width.
    alien = Alien(tt_settings, screen)
    number_aliens_x = get_number_aliens_x(tt_settings, alien.rect.width)
    number_rows = get_number_rows(tt_settings, ship.rect.height,
        alien.rect.height)
    
    # Create the fleet of aliens.
    for row_number in range(number_rows):
        for alien_number in range(number_aliens_x):
            create_alien(tt_settings, screen, aliens, alien_number,
                row_number)
        
def check_fleet_edges(tt_settings, aliens):
    """Respond appropriately if any aliens have reached an edge."""
    for alien in aliens.sprites():
        if alien.check_edges():
            change_fleet_direction(tt_settings, aliens)
            break

def change_fleet_direction(tt_settings, aliens):
    """Drop the entire fleet and change the fleet's direction."""
    for alien in aliens.sprites():
        alien.rect.y += tt_settings.fleet_drop_speed
    tt_settings.fleet_direction *= -1

def ship_hit(tt_settings, screen, stats, sb, ship, aliens, bullets):
    """Respond to ship being hit by alien."""
    if stats.ships_left > 0:
        # Decrement ships_left
        stats.ships_left -= 1
        pygame.mixer.Sound.play(death_sound)

        # Update scoreboard.
        sb.prep_ships()

        # Empty the list of aliens and bullets.
        aliens.empty()
        bullets.empty()

        # Create a new fleet and center the ship. 
        create_fleet(tt_settings, screen, ship, aliens)
        ship.center_ship()

        # Pause.
        sleep(0.5)

    else:
        stats.game_active = False
        pygame.mixer.Sound.play(game_over)
        pygame.mouse.set_visible(True)

def check_aliens_bottom(tt_settings, screen, stats, sb, ship, aliens,
        bullets):
    """Check if any aliens have reached the bottom of the screen."""
    screen_rect = screen.get_rect()
    for alien in aliens.sprites():
        if alien.rect.bottom >= screen_rect.bottom:
            # Treat this the same as if the ship got hit.
            ship_hit(tt_settings, screen, stats, sb, ship, aliens, bullets)
            break

def update_aliens(tt_settings, screen, stats, sb, ship, aliens, bullets):
    """
    Check if the fleet is at an edge,
    and then update the positions of all aliens in the fleet.
    """
    check_fleet_edges(tt_settings, aliens)
    aliens.update()

    # Look for alien-ship collisions.
    if pygame.sprite.spritecollideany(ship, aliens):
        ship_hit(tt_settings, screen, stats, sb, ship, aliens, bullets)

    # Look for aliens hitting the bottom of the screen.
    check_aliens_bottom(tt_settings, screen, stats, sb, ship, aliens, bullets)

def check_high_score(stats, sb):
    """Check to see if there's a new high score."""
    if stats.score > stats.high_score:
        stats.high_score = stats.score
        sb.prep_high_score()