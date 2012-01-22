#
# Data:  1/16/2012
# Author: Karolin Varner
# 
# (C) Copyright 2012 by Karolin Varner
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
   return json.loads(unicode(urllib.urlopen(url).read()))

#########################
# Text formatting       #
#########################
#
# sym_* are for output. No rules, but be nice to your eyes.
#

# Tabbed view
sym_user          = u"@"   # User Prefix
sym_channel       = u"-> " # Channel prefix
sym_indend        = u"   " # *tab* :3

# Path view for channels
sym_pathseperator = u"/"   # Channel     | Path seperator

# Used between two text elements.
# If the gap is short use *_short, otherwise use *_long
sym_bridge_short = u" "
sym_bridge_long  = u"."

# Minimal length for long lengths
len_bridge_longlen = 8

# User flags. Pronted behind the users
sym_deaf          = u"[8-X]"
sym_mute          = u"[:-X]"
sym_suppress      = u"[:~?]"
sym_self_deaf     = u"(Ssss)"
sym_self_mute     = u"(Mute)"
sym_recording     = u"{REC}"
sym_priority      = u"{:-D}"

# Not avaiable error
err_info_missing = u"Not avaiable!"

#########################
# Clazzes               #
#########################

class MumEnt:
   """ Mumble entity - the things Channels and Users have in common. """
   def path(self):
      """ The path of this user formatted as string. """
      return join_str(( e.path_elem() for e in self.get_path() ), sym_pathseperator)

   def info(self):
      """ Dump all the information known about this. """
      o = u""
      if hasattr(self, "attrmap"):
         for key in self.attrmap.keys():
            value = info_str(getattr(self, key)).strip()
            o += value + u"\n"
            o += join_str((sym_channel + line for line in value.split(u"\n")))

      if hasattr(self, "flagmap"):
         flags = ( (key, getattr(self, key)) for key in self.flagmap.keys() )
         o += u"Flags:\n"
         o += sym_channel + join_str(map(lambda x : x[0], filter(lambda x : x[1], flags)))

      return o


   def extractdata(self, data):
      """ Read as much values as possible from data and write the fields. """
      if hasattr(self, "attrmap"):
         for elem in self.attrmap.iteritems():
            setattr(self, elem[0], dict_get(data, elem[1]))

      if hasattr(self, "flagmap"):
         for elem in self.flagmap.iteritems():
            setattr(self, elem[0], dict_flag(data, elem[1]))

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
      u"name" : u"name",
      u"id"   : u"id",
      u"URL"  : u"x_connecturl",
      u"desc" : u"description"
   }
   
   # Maps the data flags on this class's attrs: ('class attr', 'data key')
   flagmap = {
      u"temporary" : u"temporary"
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

   @classmethod
   def from_data(clazz,chandata, parent=None, users=None, channels=None):
      """ 
      Initialize as much values as possible using extractdata(self, data) 
      (=> This is quasi an alias).
      Parent, Users and subchannels can also be set here,
      because they are tree data.
      """
      self = clazz()
      self.parent = parent
      self.users = users
      self.channels = channels
      self.extractdata(chandata)
      return self

   @classmethod
   def from_clone(clazz, clone, parent=u"", users=u"", channels=u""):
      """ 
      Clone initializer.
      The data of the clone will be identical to trhe original.
      To clone a branch, use clone_branch.
      Like the data dict initializer,
      allows setting of tree data: parent, users, channels.
      The passed data will be set 
      if it is of type Channel (respectively User and list of Channels) 
      or None. (default="" => type(channel) == unicode)
      """
      self = clazz()
      self.name      = clone.name
      self.id        = clone.id
      self.desc      = clone.desc
      self.users     = clone.users
      self.channels  = clone.channels
      self.URL       = clone.URL
      self.temporary = clone.temporary

      if (parent == None or type(parent) != unicode):
         self.parent = parent
      else:
         self.parent = clone.parent

      if (users == None or type(users) != unicode):
         self.users = users
      else:
         self.users = clone.users

      if (channels == None or type(channels) != unicode):
         self.channels = channels
      else:
         self.channels = clone.channels

      return self

   ########################################################
   # Tree Utils

   def get_path(self):
      """
      Returns the path of this user as tuple. 
      Each element of the path will be a Channel/User Object
      """
      if self.parent == None:
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
      clone = Channel.from_clone(self, parent)
      clone.users = [ fun(User.from_clone(u, clone)) for u in self.users ]
      clone.channels = [ c.map_branch(fun, clone) for c in self.channels ]
      return fun(clone)

   def clone_branch(self, parent=""):
      """
      Returns a clone of this branch as indipendent tree.
      => This branch will be the new root.
      """
      return self.map_branch(lambda x: x)

   def filter_tree_noclone(self, fun):
      """Self modifying filter_tree. Only used by filter_tree. Dont use :3"""
      self.users = filter(fun, self.users)
      self.channels = [ c.filter_tree_noclone(fun) for c in filter(fun, self.channels)]
      return self

   def filter_tree(self, fun):      
      """
      Creates a clone of this branch, where only branches 
      are included that match the function.
      That an element matches requieres that the element
      and ALL ITS PARENTS match the function (no parent, no kid).
      This node is NOT fltered.
      """
      return self.clone_branch().filter_tree_noclone(fun)

   def flatten(self):
      """
      Returns a flat representation of this branch, where every leave and branch 
      is one element of an array. Unlike the output of filter_tree, this output
      totally relates to the original tree.
      The output includes this branch, it will be element zero.
      """
      return [self] + self.users + sum([ chan.flatten() for chan in self.channels ], [])
      
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
         raise TypeError(u"reduce_branch expects one or two arguments.")

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
      return filter(lambda b : isinstance(b, User), self.flatten())

   def list_channels(self):
      """
      Returns a list of all channels in this branch and it's subbranches.
      This includes this Channel itself.
      """
      return filter(lambda b : isinstance(b, Channel), self.flatten())

   def has_users(self):
      """ Check if there are any users in this channel or one of the subchannels. """
      return len(self.list_users()) > 0

   ##################################################
   # String formatting

   def get_name(self):
      """ Get the name """
      return info_str(self.name)
   
   def path_elem(self):
      """ Returns the name formatted for a path. """
      return self.get_name()

   def representation(self):
      """ Return a short one-line representation of this channel. """
      return sym_channel + self.get_name()

   def full_representation(self):
      return self.path() #+ u": " + info_str(self.URL)

   def overview(self, indend=0):
      """Generate overview for this channel/branch"""
      # This channels name & Url
      o  = [sym_indend*indend + sym_channel + self.get_name()]
      # + ":" + sym_indend*2 + info_str(self.URL, "")] # Could add url
      o += [sym_indend*(indend+2) + u.overview() for u in self.users ]
      o += [c.overview(indend+1) for c in self.channels]
      return join_str(o, u"\n").replace(u'\n\n', u'\n')

   def __str__(self):
      return self.full_representation()

class User(MumEnt):
   """ Represents a single connected user."""
   name       = None # Name of the user
   id         = None # Id No
   channel    = None # Channel object the user is in ! Not Readable from data !
   address    = None # The human-redable address of the user
   comment    = None # Self-set comment of the user
   avatar     = None # Avatar
   deaf       = None # Flag
   mute      = None # Flag
   suppressed = None # Flag
   selfmute  = None # Flag
   selfdeaf   = None # Flag
   recording  = None # Flag
   priority   = None # Flag

   # Maps the data attrs on this class's attrs: ('class attr', 'data key')
   attrmap = {
      u"name"      : u"name",
      u"id"        : u"userid",
      u"address"   : u"x_addrstring",
      u"comment"   : u"comment",
      u"avatar"    : u"x_texture"
   }
   
   # Maps the data flags on this class's attrs: ('class attr', 'data key')
   flagmap = {
      u"deaf"      : u"deaf",
      u"mute"      : u"mute",
      u"suppressed": u"suppress",
      u"selfmute"  : u"selfMute",
      u"selfdeaf"  : u"selfDeaf",
      u"recording" : u"recording",
      u"priority"  : u"prioritySpeaker"
   }

   def __init__(self, name=None, id=None, channel=None, address=None, comment=None, avatar=None, deaf=None, mute=None, suppressed=None, selfmute=None, selfdeaf=None, recording=None, priority=None):
      """ Initialize as much values as given, the rest is None """
      self.name       = name
      self.id         = id
      self.channel    = channel
      self.address    = address
      self.comment    = comment
      self.avatar     = avatar
      self.deaf       = deaf
      self.mute      = mute
      self.suppressed = suppressed
      self.selfmute  = selfmute
      self.selfdeaf   = selfdeaf
      self.recording  = recording
      self.priority   = priority

   @classmethod
   def from_data(clazz, data, chan=None):
      """
      Initialize as much values as possible using extractdata(self, data)
      (=> This is quasi an alias).
      channel can also be set this way, beacause it is tree data.
      """
      self = clazz()
      self.channel = chan
      self.extractdata(data)
      return self

   @classmethod
   def from_clone(clazz, clone, chan=u""):
      """
      Clone initializer.
      Like the data dict initializer,
      allows setting of tree data: channel.
      The passed channel data will be set 
      if it is of type Channel or None. (default="" => type(channel) == str)
      """
      self = clazz()
      self.name       = clone.name
      self.id         = clone.id
      self.address    = clone.address
      self.comment    = clone.comment
      self.avatar     = clone.avatar
      self.deaf       = clone.deaf
      self.mute      = clone.mute
      self.suppressed = clone.suppressed
      self.selfmute   = clone.selfmute
      self.selfdeaf   = clone.selfdeaf
      self.recording  = clone.recording
      self.priority   = clone.priority

      if (chan == None or isinstance(chan, Channel)):
         self.channel = chan
      else:
         self.channel = clone.channel

      return self

   def get_path(self):
      """
      Returns the path of this user as tuple. 
      Each element of the path will be a Channel/User Object.
      """
      assert channel != None
      return channel.get_path() + (self,)

   def name_for_path(self):
      """ Returns the name formatted for a path. """
      return "@" + info_str(name);

   ##################################################
   # String formatting

   def flags_tostr(self):
      o = ""
      
      # Self mute | deaf
      if self.selfdeaf:
         o += sym_self_deaf
      elif self.selfmute:
         o += sym_self_mute

      # Supressed
      if self.suppressed:
         o += sym_suppress

      # Mute | Deaf
      if self.deaf:
         o += sym_deaf
      elif self.mute:
         o += sym_mute

      # --
      if self.recording:
         o += sym_recording
      
      if self.priority:
         o += sym_priority

      return o

   def get_name(self):
      """ Get the name """
      return info_str(self.name)
   
   def path_elem(self):
      """ Returns the name formatted for a path. """
      return sym_user + self.get_name()

   def representation(self):
      """ Return a short one-line representation of this channel. """
      return sym_user + self.get_name()

   def full_representation(self):
      return self.path()

   def overview(self, indend=0):
      """Generate overview for this channel/branch"""
      return self.representation() + "  " + self.flags_tostr()

   def __str__(self):
      return self.overview()

########################
# Information          #
########################

def info_avaiable(info):
   """ Computes if the given information is avaiable (actually: x -> x == None) """
   return info != None

def info_str(info, err=err_info_missing):
   """
   Convert an infromation to a string.
   actually: x,err -> x == None: err
                      otherwise: str(x)
   """
   if info_avaiable(info):
      return unicode(info)
   else:
      return err

########################
# Lists                #
########################

def join(l):
   """ Concat all elements of l """
   return reduce(lambda a,b : a + b, l)

def join_str(l, sep=" "):
   """ Joins all the elements of l as a string """
   return reduce(lambda a, b: unicode(a) + sep + unicode(b), l, "")

########################
# Dict                 #
########################

def dict_get(data, field):
   """Read a field from a data. Returns the value if possible and None if not."""
   if (field in data):
      return data[field]
   else:
      return None

def dict_flag(data, flag):
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
def dict_convertflags(data, map):
   return tuple(
         filter(lambda e : len(e) > 0,
            ( ["", f[0]][dict_flag(data, f[1])] for f in data.iteritems() ) ))

##########################
# Information Extraction #
##########################


def gatherinfo_chan(chandata, parent=None):
   """
   Transform the informatin in data in Channel and User objects.
   Returns the Root Channel Object.
   """
   chan = Channel.from_data(chandata, parent)
   chan.users = [ User.from_data(udat, chan) for udat in chandata[u'users'] ]
   chan.channels = [ gatherinfo_chan(cdat, chan) for cdat in chandata[u'channels'] ]
   return chan

def create_tree(url):
   return gatherinfo_chan(fetchdata_url(url)[u'root'])
