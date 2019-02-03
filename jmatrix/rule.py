# Copyright (C) 2019  Jay Kamat <jaygkamat@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import enum
import typing
import collections
import functools

class Action(enum.Enum):
	"""A uMatrix action.

Defined formally in the uMatrix rule documentation.

https://github.com/gorhill/uMatrix/wiki/Rules-syntax

	"""
	BLOCK = 1
	ALLOW = 2
	INHERIT = 3

class Type(enum.Enum):
	"""A uMatrix request type.

Defined formally in the uMatrix rule documentation.

https://github.com/gorhill/uMatrix/wiki/Rules-syntax
	"""
	ALL = 1  # The fallback 'star' (*) rule
	COOKIE = 2
	CSS = 3
	IMAGE = 4
	MEDIA = 5
	SCRIPT = 6
	XHR = 7
	FRAME = 8
	OTHER = 9

class State(enum.Enum):
	"""A uMatrix state (for matrix-off).

Defined formally in the uMatrix rule documentation.

https://github.com/gorhill/uMatrix/wiki/Rules-syntax

	"""
	# TRUE means matrix is OFF, not on!
	TRUE = 1
	FALSE = 2

RULE_MATRIX_TYPE = typing.Dict[str, typing.Dict[str, typing.Dict[Type, Action]]]
RULE_MATRIX_OFF_TYPE = typing.Dict[str, State]

class Rules():
	def __init__(self):
		self.matrix_off_rules = {}  # type: RULE_MATRIX_OFF_TYPE
		# buckle up, we're going on a ride.
		self.matrix_rules = (
			collections.defaultdict(
				functools.partial(
					collections.defaultdict,
					functools.partial(
						collections.defaultdict,
						functools.partial(
							# Inherit by default
							Action, 3)))))  # type: RULE_MATRIX_TYPE
