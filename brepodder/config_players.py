"""
Player configuration for brePodder.

Defines supported external audio players and their commands.
"""
import shutil
from typing import Optional

from logger import get_logger

logger = get_logger(__name__)


# Player configurations
# {file} placeholder is replaced with the actual file path or URL
PLAYERS: dict[str, dict[str, Optional[str]]] = {
    'builtin': {
        'name': 'Built-in Player (GStreamer)',
        'check_command': None,  # Always available
        'play_command': None,   # Uses AudioPlayer widget
        'enqueue_command': None,
        'description': 'Built-in Qt/GStreamer player. May not support HTTPS streaming.'
    },
    'mpv': {
        'name': 'MPV',
        'check_command': 'mpv',
        'play_command': 'mpv --no-video "{file}"',
        'enqueue_command': 'mpv --no-video --playlist-start=0 --playlist-append="{file}"',
        'description': 'Lightweight, powerful media player. Excellent codec support.'
    },
    'mplayer': {
        'name': 'MPlayer',
        'check_command': 'mplayer',
        'play_command': 'mplayer "{file}"',
        'enqueue_command': 'mplayer -playlist "{file}"',
        'description': 'Classic Unix media player.'
    },
    'mocp': {
        'name': 'MOC (Music on Console)',
        'check_command': 'mocp',
        'play_command': 'mocp --clear --play "{file}"',
        'enqueue_command': 'mocp --append "{file}"',
        'description': 'Console audio player with server/client architecture.'
    },
    'vlc': {
        'name': 'VLC',
        'check_command': 'cvlc',
        'play_command': 'cvlc --play-and-exit "{file}"',
        'enqueue_command': 'cvlc --playlist-enqueue "{file}"',
        'description': 'VLC media player (command line mode).'
    },
    'ffplay': {
        'name': 'FFplay',
        'check_command': 'ffplay',
        'play_command': 'ffplay -nodisp -autoexit "{file}"',
        'enqueue_command': None,
        'description': 'Simple player from FFmpeg. No playlist support.'
    },
}


def is_player_installed(player_key: str) -> bool:
    """
    Check if a player is installed on the system.
    
    Args:
        player_key: Key from PLAYERS dict (e.g., 'mpv', 'vlc')
        
    Returns:
        True if player is installed, False otherwise
    """
    if player_key not in PLAYERS:
        return False
    
    check_command = PLAYERS[player_key]['check_command']
    
    # Built-in player is always available
    if check_command is None:
        return True
    
    # Check if the command exists in PATH
    return shutil.which(check_command) is not None


def get_available_players() -> list[str]:
    """
    Get a list of player keys that are installed on the system.
    
    Returns:
        List of player keys (e.g., ['builtin', 'mpv', 'vlc'])
    """
    available = []
    for player_key in PLAYERS:
        if is_player_installed(player_key):
            available.append(player_key)
            logger.debug("Player '%s' is available", player_key)
        else:
            logger.debug("Player '%s' is not installed", player_key)
    return available


def get_player_display_name(player_key: str) -> str:
    """Get the display name for a player."""
    if player_key in PLAYERS:
        return PLAYERS[player_key]['name']
    return player_key


def get_play_command(player_key: str, file_path: str) -> Optional[str]:
    """
    Get the command to play a file with the specified player.
    
    Args:
        player_key: Key from PLAYERS dict
        file_path: Path to file or URL to play
        
    Returns:
        Command string ready to execute, or None for built-in player
    """
    if player_key not in PLAYERS:
        return None
    
    command_template = PLAYERS[player_key]['play_command']
    if command_template is None:
        return None
    
    return command_template.replace('{file}', file_path)


def get_enqueue_command(player_key: str, file_path: str) -> Optional[str]:
    """
    Get the command to add a file to the player's playlist.
    
    Args:
        player_key: Key from PLAYERS dict
        file_path: Path to file or URL to enqueue
        
    Returns:
        Command string ready to execute, or None if not supported
    """
    if player_key not in PLAYERS:
        return None
    
    command_template = PLAYERS[player_key]['enqueue_command']
    if command_template is None:
        return None
    
    return command_template.replace('{file}', file_path)
