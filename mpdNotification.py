#!/usr/bin/python3
import os
from glob import glob
import logging
from mpd import MPDClient
import notify2
from gi.repository import GdkPixbuf

class MpdClt(MPDClient):
    """
    Define a simple Mpd client that displays notifications whenever something relevant happens.
    """

    def __init__(self, host='localhost', port=6600, music_dir=os.path.join('/', 'home', 'davinellulinvega','Music')):
        """
        Initialize the required attributes.
        """

        # Initialize the parent class
        super(MpdClt, self).__init__()

        # Notification stuff
        self._notification = notify2.Notification("MPD Notification", "0")
        notify2.init("MPD Notification")

        # Connect to the mpd daemon
        self._host = host
        self._port = port

        # Other stuff
        self._db_updating = False
        self._music_dir = music_dir
        logging.basicConfig(filename='/tmp/mpdNotification.log')
        self._log = logging.getLogger()

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
                            self._notification.update('MPD Notification', message='Mpd database <b>updated !!!</b>')
                            self._db_updating = False
                        else:
                            self._notification.update('MPD Notification', message='Mpd database <b>updating ...</b>')
                            self._db_updating = True
                    elif subsys == 'player':
                        # Get the current status
                        curr_status = clt.status()

                        # Find out what changed
                        player_state = curr_status.get('state', '')
                        if player_state == 'pause':
                            self._notification.update('MPD Notification', message='<i>Paused playback ...</i>')
                        elif player_state == 'stop':
                            self._notification.update('MPD Notification', message='<i>Stopped playback ...</i>')
                        elif player_state == 'play' or old_status['songid'] != curr_status['songid']:
                            curr_song = self.currentsong()
                            if old_status['songid'] != curr_status['songid']:
                                file_name = curr_song.get('file', None)
                                if file_name is not None:
                                    dir_name = os.path.join(self._music_dir, os.path.dirname(file_name))
                                    icon = None
                                    for ext in ['jpg', 'png', 'jpeg']:
                                        try:
                                            files = glob("{}/*.{}".format(dir_name, ext))
                                        except:
                                            self._log.exception('An error occurred while looking for Album cover:', exc_info=True)
                                            break
                                        if len(files) > 0:
                                            self._notification.set_icon_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(files[0], 100, 100))
                                            break

                            self._notification.update("MPD Notification", message="<i>Playing:</i> <b>{}"
                                                      "</b>\n<i>by:</i> {}\n<i>from:</i> {}".format(curr_song.get('title', ''),
                                                                                                  curr_song.get('artist', ''),
                                                                                                  curr_song.get('album', '')))

                        # Update the old status
                        old_status = curr_status
                    elif subsys == 'output':
                        # Get current outputs status
                        curr_outputs = self.outputs()
                        for old_out, curr_out in zip(old_outputs, curr_outputs):
                            if old_out['outputenabled'] != curr_out['outputenabled']:
                                if curr_out['outputenabled'] == '1':
                                    self._notification.update('MPD Notification', message='Enabled {}'.format(curr_out['outputname']))
                                else:
                                    self._notification.update('MPD Notification', message='Disabled {}'.format(curr_out['outputname']))

                        # Update the old_outputs
                        old_outputs = curr_outputs

                    # Display the notification
                    self._notification.show()
        except:
            self._log.exception('An error occurred within the main loop:', exc_info=True)
            # Close all the things
            self._notification.close()
            self.disconnect()
            self.close()
            logging.shutdown()

if __name__ == '__main__':
    # Get an MPD client
    clt = MpdClt()

    # Start the main loop
    clt.main()
