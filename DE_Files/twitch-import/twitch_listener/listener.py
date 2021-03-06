from socket import socket
from time import time, sleep
from twitch_listener import utils
import select
import codecs
import logging

class connect_twitch(socket):

    '''
    A class to represent a connection to a twitch application

    Attributes
    ----------
    nickname : str
        nickname of the twitch application account you've create
    oauth : str 
        oauth credentials for your application
    client_id : str
        your application's name

    '''
    
    def __init__(self, nickname, oauth, client_id):

        self.nickname = nickname
        
        self.client_id = client_id
        if oauth.startswith('oauth:'):
            self.oauth = oauth
        else:
            self.oauth = 'oauth:' + oauth


        # list of bots used by twitch for messaging in the chat
        # we are not interested in their messages
        self.botlist = ['moobot' 'nightbot', 'ohbot',
                        'deepbot', 'ankhbot', 'vivbot',
                        'wizebot', 'coebot', 'phantombot',
                        'xanbot', 'hnlbot', 'streamlabs',
                        'stay_hydrated_bot', 'botismo', 'streamelements',
                        'slanderbot', 'fossabot']
            
        # IRC parameters
        self._server = "irc.chat.twitch.tv"
        self._port = 6667
        self._passString = f"PASS " + self.oauth + f"\n"
        self._nameString = f"NICK " + self.nickname + f"\n"
        

    def _join_channels(self, dirname, channels):

        '''
        Function to initialize a socket per channel and the logging parameters

        Parameters :
            dirname : str
                log directory in relative path
            channels : list
                list of channels to listen
        Returns :
                print when a socket is open
        '''

        self._sockets = {}
        self.joined = []
        self._loggers = {}
        
        # Establish socket connections
        for channel in channels:
            self._sockets[channel] = socket()
            self._sockets[channel].connect((self._server, self._port))
            self._sockets[channel].send(self._passString.encode('utf-8'))
            self._sockets[channel].send(self._nameString.encode('utf-8'))
            
            joinString = f"JOIN #" + channel.lower() + f"\n"
            self._sockets[channel].send(joinString.encode('utf-8'))
            self._loggers[channel] = utils.setup_loggers(channel, dirname+ '/' +channel + '.log')
            
            self.joined.append(channel)

            print("Open channel {0}".format(channel))
        
    def listen(self, dirname, channels, duration):

        """
        Method for scraping chat data from Twitch channels.
        At the end the socket are closed and logging module is shutdown

        Parameters:
            dirname : string
                - directory for log files
            channels : list
                - Channel(s) to connect to.
            duration : int           
                 - Length of time to listen for in seconds
        """

        self._join_channels(dirname, channels)
        startTime = time()
           
        # Collect data while duration not exceeded and channels are live
        while (time() - startTime) < duration: 
            now = time() # Track loop time for adaptive rate limiting
            ready_socks,_,_ = select.select(self._sockets.values(), [], [], 1)

            for channel in self.joined:
                sock = self._sockets[channel]

                if sock in ready_socks:

                    response = sock.recv(16384).decode('utf-8')
                    if "PING :tmi.twitch.tv\r\n" in response:
                        sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))                
                    else:
                        self._loggers[channel].info(response)                       
                    elapsed = time() - now
                    if elapsed < 60/800:
                        sleep( (60/800) - elapsed) # Rate limit
                else: # if not in ready_socks
                    pass
        
        # Close sockets once not collecting data
        for channel in self.joined:
            self._sockets[channel].close()
            print("Close channel {0}".format(channel))
        
        # close the logging module to release the log files
        logging.shutdown()

        

        
    

                    
        