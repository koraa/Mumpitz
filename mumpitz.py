#
# Data:  1/16/2012
# Author: Karolin Varner
# 
# © Copyright 2012 by Karolin Varner
#
#############################################################################
#
# This file is part of Mumpitz.
#
# Mumpitz is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mumpitz is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mumpitz. If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
#
# This file contains the Mumpitz library.
#

import urllib
import json

########################
# Data Fetching        #
########################

def fetchdata_url(url):
   return jason.loads(urllib.urlopen(url).read())

#########################
# Text formatting       #
#########################
#
# sym_* are for output. No rules, but be nice to your eyes.
#

# Tabbed view
sym_user          = "@"   # User Prefix
sym_channel       = "-> " # Channel prefix
sym_indend        = "   " # *tab* :3

# Path view for channels
sym_pathseperator = "/"   # Channel     | Path seperator

# Used between two text elements.
# If the gap is short use *_short, otherwise use *_long
sym_bridge_short = " "
sym_bridge_long  = "."

# Minimal length for long lengths
len_bridge_longlen = 8

# User flags. Pronted behind the users
sym_deaf          = "[8-X]"
sym_mute          = "[:-X]"
sym_suppress      = "[:~?]"
sym_self_deaf     = "(Ssss)"
sym_self_mute     = "(Mute)"
sym_recording     = "{REC}"
sym_priority      = "{:-D}"

# Not avaiable error
err_info_missing = "Not avaiable!"

#########################
# Clazzes               #
#########################

class MumEnt:
   """ Mumble entity - the things Channels and Users have in common. """
   def get_path_str(self):
      """ The path of this user formatted as string. """
      return join_str(( e.name_for_path() for e in self.get_path() ), sym_pathseperator)


   def extractdata(self, dict data):
      """ Read as much values as possible from data and write the fields. """
      if hasattr(self, "attrmap"):
         for elem in self.attrmap.iteritems():
            self.__setattr__(elem[0], dict_get(data, elem[1]))

      if hasattr(self, "flagmap"):
         for elem in self.flagmap.iteritems():
            self.__setattr__(elem[0], dict_flag(data, elem[1]))


class Channel(MumEnt):
   """
   The channels are saved in a Tree structure:
   Each node/branch is a Channel, Users are the leaves.
   Each node holds the information about it's parent, and it's
   subbranches and leaves. Therefore it is possible to move along
   this connections.
   """
   
   ##########################################
   # Attrs

   name      = None
   id        = None # ID No
   desc      = None # Description
   parent    = None # ! Not Readable from data !
   users     = None # ! Not Readable from data !
   channels  = None # Subchannels ! Not Readable from data !
   URL       = None # One-Click connect :3
   temporary = None

   # Maps the data attrs on this class's attrs: ('class attr', 'data key')
   attrmap = {
      "name" : "name"
      "id"   : "id"
      "URL"  : "x_connecturl"
      "desc" : "description"
   }
   
   # Maps the data flags on this class's attrs: ('class attr', 'data key')
   flagmap = {
      "temporary" : "temporary"
   }

   #########################################
   # Init

   def __init__(self, name=None, id=None, desc=None, parent=None, users=None, channels=None, URL=None, temporary=None):
      """ Initialize a Channel Object """
      self.name      = name
      self.id        = id
      self.desc      = desc
      self.parent    = parent
      self.users     = users
      self.channels  = channels
      self.URL       = URL
      self.temporary = temporary

   def __init__(self, dict data, Channel parent=None, users=None, channels=None):
      """ 
      Initialize as much values as possible using extractdata(self, data) 
      (=> This is quasi an alias).
      Parent, Users and subchannels can also be set here,
      because they are tree data.
      """
      self.parent = parent
      self.users = users
      self.channels = channels
      self.extractdata(data)

   def __init__(self, Channel clone, parent="", users="", channels=""):
      """ 
      Clone initializer.
      The data of the clone will be identical to trhe original.
      To clone a branch, use clone_branch.
      Like the data dict initializer,
      allows setting of tree data: parent, users, channels.
      The passed data will be set 
      if it is of type Channel (respectively User and list of Channels) 
      or None. (default="" => type(channel) == str)
      """
      self.name      = name
      self.id        = clone.id
      self.desc      = clone.desc
      self.users     = clone.users
      self.channels  = clone.channels
      self.URL       = clone.URL
      self.temporary = clone.temporary

      if (parent == None or type(parent) != str):
         self.parent = parent
      else:
         self.parent = clone.parent

      if (users == None or type(users) != str):
         self.users = users
      else:
         self.users = clone.users

      if (channels == None or type(channels) != str):
         self.channels = channels
      else:
         self.channels = clone.channels

   ########################################################
   # Tree Utils

   def get_path(self):
      """
      Returns the path of this user as tuple. 
      Each element of the path will be a Channel/User Object
      """
      if parent == None:
         return (self,)
      else:
         return self.parent.get_path() + (self,)

   def is_root(self):
      """Check if this is the root of the tree. (actually: self.parent == None)"""
      return self.partent == None

   def find_root(self):
      """ Find the root of this tree. """
      if self.is_root():
         return self
      else:
         self.parent.find_root()

   def tree_level(self, i=0):
      """Count what branching level this is. Root would be 0, child of root would be 1"""
      if self.is_root():
         return i
      else:
         return self.parent.tree_level(i+1)

   def parent_of(self, o):
      """Check if this is a parent of o."""
      # CHeck this channels childs
      for sub in self.channels + self.users:
         if sub == o:
            return true
      # Check subchannels
      for chan in self.channels: # Check subchannels
         if chan.parent_of(o):
            return true
      # Not found
      return false 

   def map_branch(self, fun, parent=""):
      """
      Returns a clone of this branch, where each node will be f(node).
      
      """
      clone = Channel(self, parent)
      clone.users = [ fun(User(u, clone)) for u in self.users ]
      clone.channels = [ c.map_branch(fun, clone) for c in channels ]
      return fun(c)

   def clone_branch(self, parent=""):
      """
      Returns a clone of this branch as indipendent tree.
      => This branch will be the new root.
      """
      map_branch(lambda x: x)

   def filter_tree_noclone(self, fun):
      """Self modifying filter_tree. Only used by filter_tree. Dont use :3"""
      self.users = filter(fun, users)
      self.channels = [ c.filter_tree_noclone() for c in filter(fun, channels)]
      return self

   def filter_tree(self, fun):      
      """
      Creates a clone of this branch, where only branches 
      are included that match the function.
      That an element matches requieres that the element
      and ALL ITS PARENTS match the function (no parent, no kid).
      This node is NOT fltered.
      """
      return self.clone_branch().filter_tree_noclone()

   def flatten(self):
      """
      Returns a flat representation of this branch, where every leave and branch 
      is one element of an array. Unlike the output of filter_tree, this output
      totally relates to the original tree.
      The output includes this branch, it will be element zero.
      """
      return [self] + users + [ chan.flatten() for chan in channels ]

      
   def reduce_branch(*args):
      """
      Reduce each channel in the tree in the following, recursive order:
         - (optional) Reduce this node with the input
         - Reduce self/result with users
         - Reduce with subchannel
      Call like: tree.reduce(fun) or tree(fun, v0)
      """
      # Check args
      if len(args) < 1 or len(args) > 2:
         raise TypeError("reduce_branch expects one or two arguments.")

      # Process args
      fun = args[0]
      if len(args) > 1:
         startv = fun(args[1], self)
      else:
         startv = self

      # Reduce with all users
      ret = reduce(fun, self.users, startv)
      #  Reduce with all channels
      for chan in self.channels: 
         ret = chan.reduce_branch_withstart(fun, ret)

      return ret
   
   def list_users(self):
      """ Returns a list of all users in this branch and it's subbranches. """
      return filter(lambda b : type(b) == User, self.flatten())

   def list_channels(self):
      """
      Returns a list of all channels in this branch and it's subbranches.
      This includes this Channel itself.
      """
      return filter(lambda b : type(b) == Channel, self.flatten())

   def has_users(self):
      """ Check if there are any users in this channel or one of the subchannels. """
      return len(self.list_users()) > 0

   ##################################################
   # String formatting

   def name_for_path(self):
      """ Returns the name formatted for a path. """
      return info_str(self.name);


class User(MumEnt):
   """ Represents a single connected user."""
   name       = None # Name of the user
   id         = None # Id No
   channel    = None # Channel object the user is in ! Not Readable from data !
   address    = None # The human-redable address of the user
   comment    = None # Self-set comment of the user
   avatar     = None # Avatar
   deaf       = None # Flag
   muted      = None # Flag
   suppressed = None # Flag
   selfmuted  = None # Flag
   selfdeaf   = None # Flag
   recording  = None # Flag
   priority   = None # Flag

   # Maps the data attrs on this class's attrs: ('class attr', 'data key')
   attrmap = {
      "name"      : "name"
      "id"        : "userid"
      "address"   : "x_addrstring"
      "comment"   : "comment"
      "avatar"    : "x_texture"
   }
   
   # Maps the data flags on this class's attrs: ('class attr', 'data key')
   flagmap = {
      "deaf"      : "deaf"
      "muted"     : "mute"
      "suppressed": "suppress"
      "selfmuted" : "selfMute"
      "selfdeaf"  : "selfDeaf"
      "recording" : "recording"
      "priority"  : "prioritySpeaker"
   }

   def __init__(self, name=None, id=None, channel=None, address=None, comment=None, avatar=None, deaf=None, muted=None, suppressed=None, selfmuted=None, selfdeaf=None, recording=None, priority=None):
      """ Initialize as much values as given, the rest is None """
      self.name       = name
      self.id         = id
      self.channel    = channel
      self.address    = address
      self.comment    = comment
      self.avatar     = avatar
      self.deaf       = deaf
      self.muted      = muted
      self.suppressed = suppressed
      self.selfmuted  = selfmuted
      self.selfdeaf   = selfdeaf
      self.recording  = recording
      self.priority   = priority

   def __init__(self, dict data, Channel chan=None):
      """
      Initialize as much values as possible using extractdata(self, data)
      (=> This is quasi an alias).
      channel can also be set this way, beacause it is tree data.
      """
      self.channel = chan
      self.extractdata(data)

   def __init__(self, User clone, Channel chan=""):
      """
      Clone initializer.
      Like the data dict initializer,
      allows setting of tree data: channel.
      The passed channel data will be set 
      if it is of type Channel or None. (default="" => type(channel) == str)
      """
      self.name       = clone.name
      self.id         = clone.id
      self.address    = clone.address
      self.comment    = clone.comment
      self.avatar     = clone.avatar
      self.deaf       = clone.deaf
      self.muted      = clone.muted
      self.suppressed = clone.suppressed
      self.selfmuted  = clone.selfmuted
      self.selfdeaf   = clone.selfdeaf
      self.recording  = clone.recording
      self.priority   = clone.priority

      if (chan == None or type(chan) == Channel):
         self.channel = chan
      else:
         self.channel = clone.channel

   def get_path(self):
      """ Returns the path of this user as tuple. Each element of the path will be a Channel/User Object """
      assert channel != None
      return channel.get_path() + (self,)

   def name_for_path(self):
      """ Returns the name formatted for a path. """
      return "@" + info_str(name);

########################
# Information          #
########################

def info_avaiable(dict info):
   """ Computes if the given information is avaiable (actually: x -> x == None) """
   return info == None

def info_str(sict info, str err=err_info_missing):
   """
   Convert an infromation to a string.
   actually: x,err -> x == None: err
                      otherwise: str(x)
   """
   if info_avaiable(info):
      return str(info)
   else
      return err

########################
# Lists                #
########################

def join(l):
   """ Concat all elements of l """
   return reduce(lambda a,b : a + b, l)

def join_str(l, sep=" "):
   """ Joins all the elements of l as a string """
   return reduce(lambda a, b: str(a) + sep + str(b)), l)

########################
# Dict                 #
########################

def dict_get(dict data, field):
   """Read a field from a data. Returns the value if possible and None if not."""
   if (flag in data):
      return data[flag]
   else:
      return None

def dict_flag(dict data, flag):
   """
   Read a flag from data. 
   The flag is true if it is set as true, #
   otherwise (not set, or set but false) it will be false.
   """
   if (flag in data):
      return bool(data[flag])
   return False

#
# Extract a list of flags from a *data*.
# Each flag is extracted using dict_flag
# Args:
#    -data: The dict from which the flags should be extracted
#    -map:  The map of flags: (NameInOutput, NameInInput)
def dict_convertflags(dict data, dict map):
   return tuple(
         filter(lambda e : lß0en(e) > 0,
            ( ["", f[0]][dict_flag(data, f[1])] for f in data.iteritems() ) ))

##########################
# Information Extraction #
##########################


def gatherinfo_chan(chandata, parent=None):
   """
   Transform the informatin in data in Channel and User objects.
   Returns the Root Channel Object.
   """
   chan = Channel(chandata, parent)
   chan.users = [ User(udat, chan) for udat in chandata['users'] ]
   chan.channels = [ gatherinfo_chan(cdat, chan) for cdat in chandata['channels'] ]
   return chan

############################
# Information Display      #
############################
