# Copyright (C) 2016 VIB/BEG/UGent - Tim Diels <timdiels.m@gmail.com>
# 
# This file is part of Chicken Turtle Util.
# 
# Chicken Turtle Util is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Chicken Turtle Util is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Chicken Turtle Util.  If not, see <http://www.gnu.org/licenses/>.

'''
Various utilities
'''

PATH_MAX_LENGTH = 256  # currently set to win32 limit: http://stackoverflow.com/a/1880453/1031434

class Object(object):
    '''
    Like `object`, but does not raise when args are given to `__init__`.
    
    Notes
    -----
    This was the default behaviour of `object` in Python 2.x. 
    '''
    def __init__(self, *args, **kwargs):
        super().__init__()
