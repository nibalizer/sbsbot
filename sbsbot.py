#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

#twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, ssl, defer
from twisted.python import log
from sys import stdout

#system imports
import time, sys

# ganeti imports
import urllib2
import json

# fun imports
import re
import datetime

import random


import subprocess
import sbsconfig

class MessageLogger:
    """
    An independent logger class (because separation of application
    and protocol logic is a good thing).
    """
    def __init__(self, file):
        self.file = file

    def log(self, message):
        """Write a message to the file."""
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.file.write('%s %s\n' % (timestamp, message))
        self.file.flush()

    def close(self):
        self.file.close()

class Echo(protocol.Protocol):
    def dataReceived(self, data):
        stdout.write(data)

class RelayClient(protocol.Protocol):
    def dataReceived(self, data):
        stdout.write(data)

class LogBot(irc.IRCClient):
    """A logging IRC bot."""

    nickname = sbsconfig.nickname
    versionName = "versionName"
    versionNum = "versionNum"
    versionEnv = "versionEnv"
    sourceURL = "http://github.com/nibalizer/sciencebot"
    lineRate = 2
    channels = []
    channelkey = sbsconfig.channelkey

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.logger = MessageLogger(open(self.factory.filename, "a"))
        self.logger.log("[connected at %s]" %
                        time.asctime(time.localtime(time.time())))
        self.factory.ircservers.append(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.log("[disconnected at %s]" %
                        time.asctime(time.localtime(time.time())))
        self.logger.close()
        self.factory.ircservers.remove(self)

    # callbacks for events

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        #self.msg("NickServ", "identify %s" % scienceconfig.userpassword )
        self.join(self.factory.channel, self.channelkey)
        self.join('#games&movies', self.channelkey)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        self.logger.log("[I have joined %s]" % channel)
        self.channels.append(channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]




        # Check to see if they're sending me a private message
        if channel == self.nickname:
            reply = "I'm not sure what we have to say to each other directly."
            self.msg(user, reply)
            # Check to see if bot has been told to join multiple channels 

        elif msg.startswith("!sbs"):
          realmsg = msg.split(' ')[1:]

          p = subprocess.Popen(['twitter', 'set' ] + realmsg )
          p.communicate()


    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        self.logger.log("* %s %s" % (user, msg))

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.logger.log("%s is now known as %s" % (old_nick, new_nick))

    # for fun, oveEchorride the method that determines how a nickname is changed on
    # collisions. The default method appends an underscore.

    def alterCollidedNick(self, nickname):
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
        return nickname + '^'


class EchoClientFactory(protocol.ClientFactory):
    def startedConnecting(self, connector):
        print 'Started to connect.'

    def buildProtocol(self, addr):
        print 'Connected.'
        return Echo()

    def clientConnectionLost(self, connector, reason):
        print 'Lost Connection. Reason:', reason

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason


class RelayClientFactory(protocol.ClientFactory):
    def startedConnecting(self, connector):
        print 'Started to connect.'

    def buildProtocol(self, addr):
        print 'Connected.'
        return RelayClient()

    def clientConnectionLost(self, connector, reason):
        print 'Lost Connection. Reason:', reason

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason


class LogBotFactory(protocol.ClientFactory):
    """A factory LogBots.
    A new protocol instance will be created each time we connect to the server.
    """

    def __init__(self, channel, filename ):
        self.channel = channel
        self.channelkey = sbsconfig.channelkey
        self.filename = filename
        self.ircservers = []

    def buildProtocol(self, addr):
        p = LogBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, recconect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed:", reason
        reactor.stop()

if __name__ == '__main__':
    #initialize logging
    log.startLogging(sys.stdout)

    f = LogBotFactory(sbsconfig.channel, sbsconfig.logfile )

    reactor.connectSSL("irc.cat.pdx.edu", 6697, f, ssl.ClientContextFactory())

    # run bot
    reactor.run()



