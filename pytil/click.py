# Copyright (C) 2016 VIB/BEG/UGent - Tim Diels <timdiels.m@gmail.com>
#
# This file is part of pytil.
#
# pytil is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pytil is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with pytil.  If not, see <http://www.gnu.org/licenses/>.

'''
`click:click` extensions.
'''

import click
from functools import partial

option = partial(click.option, show_default=True, required=True)
'''
:py:func:`click:click.option` with other defaults.
'''

password_option = partial(option, prompt=True, hide_input=True, show_default=False)
'''
Password option.
'''
