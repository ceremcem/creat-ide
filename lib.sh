#!/bin/bash


# TODO: 
# Use a command like xdotool windowundecorate <window_id> or wmctrl -i -r <window_id> -b remove,decorated







# Script to launch an application and control its window using xdotool,
# finding the window ID based on the application's Process ID (PID).

# --- Configuration ---
# Default delay after launching the application before trying to find its window
LAUNCH_DELAY=2 # seconds
# How long to wait (cumulatively) for the window to appear after launch
MAX_WAIT_TIME=10 # seconds
# Interval between checks when waiting for the window
WAIT_INTERVAL=0.2 # seconds

# --- Functions ---

# Function to find the window ID associated with a given PID
# Tries to find a window whose process ID matches the provided PID.
find_window_id_by_pid() {
    local target_pid="$1"
    local window_id=""
    local elapsed_time=0

    echo "Searching for window ID associated with PID: $target_pid"

    # Loop to wait for the window to appear
    while [ -z "$window_id" ] && [ "$elapsed_time" -lt "$MAX_WAIT_TIME" ]; do
        # Use xdotool to search for windows and filter by PID
        # xdotool search --pid <PID> returns window IDs belonging to that process
        window_id=$(xdotool search --onlyvisible --pid "$target_pid" 2>/dev/null | head -n 1)

        if [ -z "$window_id" ]; then
            # If no window found yet, wait a bit and try again
            sleep "$WAIT_INTERVAL"
            elapsed_time=$(echo "$elapsed_time + $WAIT_INTERVAL" | bc)
            # Optional: uncomment the line below to see search attempts
            # echo "Waiting for window... ($elapsed_time s elapsed)"
        fi
    done

    echo "$window_id"
}

# Function to minimize a window
minimize_window() {
    local window_id="$1"
    if [ -z "$window_id" ]; then
        echo "Error: No window ID provided for minimize."
        return 1
    }
    echo "Minimizing window ID: $window_id"
    xdotool windowminimize "$window_id"
    return 0
}

# Function to maximize a window
maximize_window() {
    local window_id="$1"
    if [ -z "$window_id" ]; then
        echo "Error: No window ID provided for maximize."
        return 1
    }
    echo "Maximizing window ID: $window_id"
    xdotool windowmaximize "$window_id"
    return 0
}

# Function to restore/unmaximize a window
restore_window() {
    local window_id="$1"
    if [ -z "$window_id" ]; then
        echo "Error: No window ID provided for restore."
        return 1
    }
    echo "Restoring window ID: $window_id"
    xdotool windowunmaximize "$window_id"
    return 0
}


# Function to move a window
# Args: window_id, x, y
move_window() {
    local window_id="$1"
    local x="$2"
    local y="$3"
    if [ -z "$window_id" ] || [ -z "$x" ] || [ -z "$y" ]; then
        echo "Error: Missing arguments for move (window_id, x, y)."
        return 1
    }
    echo "Moving window ID: $window_id to $x,$y"
    xdotool windowmove "$window_id" "$x" "$y"
    return 0
}

# Function to resize a window
# Args: window_id, width, height
# Note: Use --sync for potentially more reliable resizing, but might block
resize_window() {
    local window_id="$1"
    local width="$2"
    local height="$3"
    if [ -z "$window_id" ] || [ -z "$width" ] || [ -z "$height" ]; then
        echo "Error: Missing arguments for resize (window_id, width, height)."
        return 1
    }
    echo "Resizing window ID: $window_id to ${width}x${height}"
    # Use --sync to wait for the window manager to acknowledge the resize
    xdotool windowsize --sync "$window_id" "$width" "$height"
    return 0
}

# --- Main Script Logic ---

# Check if an application command was provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <application_command> [action] [args]"
    echo "Actions:"
    echo "  minimize                   - Minimize the window"
    echo "  maximize                   - Maximize the window"
    echo "  restore                    - Restore/Unmaximize the window"
    echo "  move <x> <y>               - Move the window to screen coordinates (x, y)"
    echo "  resize <width> <height>    - Resize the window to width x height"
    echo "  (no action)                - Just launch and find window ID"
    exit 1
fi

# Get the application command
APP_COMMAND="$1"
shift # Remove the command from the arguments list

# Launch the application in the background
echo "Launching application: $APP_COMMAND"
# Use exec to replace the current script process with the application process
# This is one way to get the PID reliably, though capturing $! right after is also common.
# Let's stick to capturing $! for simplicity and backgrounding.
$APP_COMMAND &
APP_PID=$! # Store the process ID of the launched application

# Wait for the application's window to appear using its PID
echo "Waiting up to $MAX_WAIT_TIME seconds for the window associated with PID $APP_PID to appear..."
WINDOW_ID=$(find_window_id_by_pid "$APP_PID")

if [ -z "$WINDOW_ID" ]; then
    echo "Error: Could not find a window ID associated with PID $APP_PID within the timeout."
    echo "The application was launched, but its window could not be identified."
    echo "You may need to increase MAX_WAIT_TIME or the application might not create a standard window."
    exit 1 # Exit with error if window not found
fi

# If a window ID was found
echo "Found window ID: $WINDOW_ID for application launched with PID $APP_PID"


# --- Perform Action if specified ---
if [ "$#" -gt 0 ]; then
    ACTION="$1"
    shift # Remove the action from arguments

    case "$ACTION" in
        minimize)
            minimize_window "$WINDOW_ID"
            ;;
        maximize)
            maximize_window "$WINDOW_ID"
            ;;
        restore)
            restore_window "$WINDOW_ID"
            ;;
        move)
            if [ "$#" -lt 2 ]; then
                echo "Error: move action requires x and y coordinates."
                echo "Usage: $0 <application_command> move <x> <y>"
                exit 1
            fi
            MOVE_X="$1"
            MOVE_Y="$2"
            move_window "$WINDOW_ID" "$MOVE_X" "$MOVE_Y"
            ;;
        resize)
            if [ "$#" -lt 2 ]; then
                echo "Error: resize action requires width and height."
                echo "Usage: $0 <application_command> resize <width> <height>"
                exit 1
            fi
            RESIZE_WIDTH="$1"
            RESIZE_HEIGHT="$2"
            resize_window "$WINDOW_ID" "$RESIZE_WIDTH" "$RESIZE_HEIGHT"
            ;;
        *)
            echo "Error: Unknown action '$ACTION'"
            echo "Usage: $0 <application_command> [action] [args]"
            exit 1
            ;;
    esac
else
    # If no action was specified, just report the window ID and exit
    echo "No action specified. Application launched and window ID found."
fi

# Note: The script exits after performing the action or reporting the ID.
# The launched application continues to run in the background.

exit 0
