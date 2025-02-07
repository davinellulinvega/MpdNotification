#!/usr/bin/python3
from pathlib import Path
from mpd import MPDClient
from notifypy import Notify


# Declare required constants
DFT_ICON = Path("/usr/share/icons/AdwaitaLegacy/48x48/legacy/media-tape.png")


class MpdClt(MPDClient):
    """
    Define a simple Mpd client that displays notifications whenever something relevant happens.
    """

    def __init__(self, host='localhost', port=6600, music_dir=Path("~/Music/").expanduser().resolve()):
        """
        Initialize the required attributes.
        """

        # Initialize the parent class
        super(MpdClt, self).__init__()

        # Notification stuff
        self._notification = Notify(default_notification_title="MPD Notification",
                                    default_notification_icon=DFT_ICON,
                                    default_notification_urgency='low',
                                    default_notification_application_name='MPD Notification')

        # Connect to the mpd daemon
        self._host = host
        self._port = port

        # Other stuff
        self._db_updating = False
        self._music_dir = music_dir

    def main(self):
        """
        The main loop that processes all relevant events and display a notification."
        """

        # Connect the client
        self.connect(self._host, self._port)

        # Get the old status and outputs
        old_status = self.status()
        old_outputs = self.outputs()

        try:
            while True:  # Yes we run forever
                # Wait for an event to pop
                subsystems = self.idle('player', 'update', 'output')

                for subsys in subsystems:
                    # Check the affected sub-system
                    if subsys == 'update':
                        if self._db_updating:
                            self._notification.message = 'Mpd database <b>updated !!!</b>'
                            self._db_updating = False
                        else:
                            self._notification.message = 'Mpd database <b>updating ...</b>'
                            self._db_updating = True
                    elif subsys == 'player':
                        # Get the current status
                        curr_status = clt.status()

                        # Find out what changed
                        player_state = curr_status.get('state', '')
                        if player_state == 'pause':
                            self._notification.message = '<i>Paused playback ...</i>'
                        elif player_state == 'stop':
                            self._notification.message = '<i>Stopped playback ...</i>'
                        elif player_state == 'play' or old_status['songid'] != curr_status['songid']:
                            curr_song = self.currentsong()
                            if old_status['songid'] != curr_status['songid']:
                                file_name = curr_song.get('file', None)
                                if file_name is not None:
                                    dir_name = self._music_dir.joinpath(file_name).parent
                                    #dir_name = os.path.join(self._music_dir, os.path.dirname(file_name))
                                    for ext in ['jpg', 'png', 'jpeg']:
                                        try:
                                            files = list(dir_name.glob(f"*.{ext}"))
                                        except:
                                            break
                                        if len(files) > 0:
                                            self._notification.icon = files[0]
                                            break

                            self._notification.message = f"<i>Playing:</i> <b>{curr_song.get('title', '')}</b>\n<i>by:</i> {curr_song.get('artist', '')}\n<i>album:</i> {curr_song.get('album', '')}"

                        # Update the old status
                        old_status = curr_status
                    elif subsys == 'output':
                        # Get current outputs status
                        curr_outputs = self.outputs()
                        for old_out, curr_out in zip(old_outputs, curr_outputs):
                            if old_out['outputenabled'] != curr_out['outputenabled']:
                                if curr_out['outputenabled'] == '1':
                                    self._notification.message = f"Enabled {curr_out['outputname']}"
                                else:
                                    self._notification.message = f"Disabled {curr_out['outputname']}"

                        # Update the old_outputs
                        old_outputs = curr_outputs

                    # Display the notification
                    self._notification.send()
                    self._notification.icon = DFT_ICON
        except:
            # Close all the things
            self.disconnect()
            self.close()

if __name__ == '__main__':
    # Get an MPD client
    clt = MpdClt()

    # Start the main loop
    clt.main()
