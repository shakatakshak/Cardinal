# Copyright (c) 2013 John Maguire <john@leftforliving.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to 
# deal in the Software without restriction, including without limitation the 
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or 
# sell copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS 
# IN THE SOFTWARE.

import re

from twisted.words.protocols import irc
from twisted.internet import protocol

from plugins.ping import PingPlugin

modules = {
    'ping': PingPlugin,
}

class CardinalBot(irc.IRCClient):
    # Get the current nickname from the factory
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    # This is a regex to split the user nick, ident, and hostname
    user_regex = re.compile(r'(.*?)!(.*?)@(.*?)')

    # This dictionary will contain a list of loaded modules
    loaded_modules = {}

    def __init__(self):
        # Create a list of modules
        for name, module in modules.items():
            self.loaded_modules[name] = module.setup()

    # This is triggered when we have signed onto the network
    def signedOn(self):
        print "Signed on as %s." % (self.nickname,)
        for channel in self.factory.channels:
            self.join(channel)

    # This is triggered when we have joined a channel
    def joined(self, channel):
        print "Joined %s." % (channel,)

    # This is triggered when we have received a message
    def privmsg(self, user, channel, msg):
        # Break the user up into usable groups
        user = re.match(self.user_regex, user)

        # Change the channel to something we can reply to
        if channel == self.nickname:
            channel = user.group(1)

        # Loop through each loaded module
        for name, module in self.loaded_modules.items():
            # Loop through each registered command of the module
            for command in module['commands']:
                # If the message matches the commands regex...
                if re.match(command.regex, msg):
                    # Call the matched command.
                    command(self, user, channel, msg)

        print "(%s)>>> %s" % (channel, msg)

    # This is a wrapper command to send messages
    def sendMsg(self, user, message, length=None):
        print "(%s)<<< %s" % (user, message)
        self.msg(user, message, length)

# This interfaces CardinalBot with the Twisted library
class CardinalBotFactory(protocol.ClientFactory):
    protocol = CardinalBot

    def __init__(self, channels, nickname='Cardinal'):
        self.channels = channels
        self.nickname = nickname

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)
