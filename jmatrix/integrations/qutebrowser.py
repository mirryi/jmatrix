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


## TODO FIXME make config-source not be super painful

import sys
import os

import jmatrix.rule, jmatrix.ublock_parser, jmatrix.interceptor

from PyQt5.QtCore import QUrl

from qutebrowser.api import interceptor, cmdutils, message

from qutebrowser.config.configfiles import ConfigAPI  # noqa: F401
from qutebrowser.config.config import ConfigContainer # noqa: F401

config = config  # type: ConfigAPI # noqa: F821 pylint: disable=E0602,C0103
c = c  # type: ConfigContainer # noqa: F821 pylint: disable=E0602,C0103



JMATRIX_RULES = jmatrix.rule.Rules()

JMATRIX_CONFIG = config.configdir / "jmatrix-rules"

if not JMATRIX_CONFIG.exists():
	# Create the file with the default config
	with open(JMATRIX_CONFIG, "w") as f:
		f.write(jmatrix.rule.DEFAULT_RULES)

@cmdutils.register()
def jmatrix_read_config():
	"""Overwrite internal config with the one in the jmatrix config file."""
	global JMATRIX_RULES
	JMATRIX_RULES = jmatrix.rule.Rules()
	with open(JMATRIX_CONFIG, "r") as f:
		jmatrix.ublock_parser.rules_to_map(f, JMATRIX_RULES)

# Read back config
jmatrix_read_config()

# Unsupported matrix rules:
# - cookie
QUTEBROWSER_JMATRIX_MAPPING = {
	interceptor.ResourceType.STYLESHEET: jmatrix.rule.Type.CSS,
	interceptor.ResourceType.IMAGE: jmatrix.rule.Type.IMAGE,
	interceptor.ResourceType.MEDIA: jmatrix.rule.Type.MEDIA,
	interceptor.ResourceType.SCRIPT: jmatrix.rule.Type.SCRIPT,
	interceptor.ResourceType.XHR: jmatrix.rule.Type.XHR,
	interceptor.ResourceType.SUB_FRAME: jmatrix.rule.Type.FRAME,
}

def _jmatrix_intercept_request(info: interceptor.Request) -> None:
	request_type = info.resource_type
	if request_type == interceptor.ResourceType.MAIN_FRAME:
		return
	context_host = info.first_party_url.host()
	context_scheme = info.first_party_url.scheme()
	request_scheme = info.request_url.scheme()
	if request_scheme == "blob":
		# Sometimes we get 'blob' urls which don't have their host decoded properly
		request_host = QUrl(info.request_url.toString(QUrl.RemoveScheme)).host()
	else:
		request_host = info.request_url.host()

	jmatrix_type = QUTEBROWSER_JMATRIX_MAPPING.get(request_type, jmatrix.rule.Type.OTHER)
	if jmatrix.interceptor.should_block(
			context_host, context_scheme,
			request_host, jmatrix_type, JMATRIX_RULES):
		info.block()


interceptor.register(_jmatrix_intercept_request)
