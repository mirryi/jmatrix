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

import sys, os, time

import jmatrix.rule, jmatrix.ublock_parser, jmatrix.interceptor

from qutebrowser.api import interceptor, cmdutils, message, apitypes
from qutebrowser.completion.models import completionmodel, listcategory
from qutebrowser.utils import objreg

from qutebrowser.config.configfiles import ConfigAPI  # noqa: F401
from qutebrowser.config.config import ConfigContainer # noqa: F401

config = config  # type: ConfigAPI # noqa: F821 pylint: disable=E0602,C0103
c = c  # type: ConfigContainer # noqa: F821 pylint: disable=E0602,C0103



# Used to actually decide if we should block a rule or not
JMATRIX_RULES = jmatrix.rule.Rules()

# Used to track requests that we have seen for purposes of completion
SEEN_REQUESTS = jmatrix.rule.Rules()

JMATRIX_CONFIG = config.configdir / "jmatrix-rules"

if not JMATRIX_CONFIG.exists():
	# Create the file with the default config
	with open(JMATRIX_CONFIG, "w") as f:
		f.write(jmatrix.rule.JMATRIX_HEADER + jmatrix.rule.DEFAULT_RULES)

@cmdutils.register()
def jmatrix_read_config():
	"""Overwrite internal config with the one in the jmatrix config file."""
	global JMATRIX_RULES
	global SEEN_REQUESTS
	JMATRIX_RULES = jmatrix.rule.Rules()
	SEEN_REQUESTS = jmatrix.rule.Rules()
	with open(JMATRIX_CONFIG, "r") as f:
		jmatrix.ublock_parser.rules_to_map(f, JMATRIX_RULES)

@cmdutils.register()
def jmatrix_write_config():
	"""Write out current rules."""
	# This will strip out the "ignored" values in the default config.
	text = jmatrix.ublock_parser.map_to_rules(JMATRIX_RULES)
	with open(JMATRIX_CONFIG, "w") as f:
		f.write(jmatrix.rule.JMATRIX_HEADER + text)

# Read back config
jmatrix_read_config()

# Unsupported matrix rules:
# - cookie
QUTEBROWSER_JMATRIX_MAPPING = {
	interceptor.ResourceType.stylesheet: jmatrix.rule.Type.CSS,
	interceptor.ResourceType.image: jmatrix.rule.Type.IMAGE,
	interceptor.ResourceType.media: jmatrix.rule.Type.MEDIA,
	interceptor.ResourceType.script: jmatrix.rule.Type.SCRIPT,
	interceptor.ResourceType.xhr: jmatrix.rule.Type.XHR,
	interceptor.ResourceType.sub_frame: jmatrix.rule.Type.FRAME,
}

def _jmatrix_intercept_request(info: interceptor.Request) -> None:
	request_type = info.resource_type
	# Never blacklist main navigation (should this be changed?)
	if (request_type == interceptor.ResourceType.main_frame or
		# If we are already blocked, don't waste our time here.
		info.is_blocked):
		return
	context_host = info.first_party_url.host()
	context_scheme = info.first_party_url.scheme()
	request_scheme = info.request_url.scheme()
	if request_scheme == "blob":
		# These 'blob' urls don't seem to be actual requests, but internal chrome stuff
		# Let them pass, since they aren't real requests and break things if we block them.
		return
	request_host = info.request_url.host()

	jmatrix_type = QUTEBROWSER_JMATRIX_MAPPING.get(request_type, jmatrix.rule.Type.OTHER)
	block = jmatrix.interceptor.should_block(
			context_host, context_scheme,
			request_host, request_scheme,
			jmatrix_type, JMATRIX_RULES)
	if block:
		info.block()

	SEEN_REQUESTS.matrix_rules[context_host][request_host][jmatrix_type] = \
		jmatrix.rule.Action.BLOCK if block else jmatrix.rule.Action.ALLOW

interceptor.register(_jmatrix_intercept_request)

def _get_rules_completion(*args, info):
	tab = objreg.get('tab', scope='tab', window=info.win_id, tab='current')
	model = completionmodel.CompletionModel(column_widths=(100,))
	entries = [
		("{:10}{:10}{}".format(action.name, res_type.name.lower(), dest),) for
		dest, types in SEEN_REQUESTS.matrix_rules[tab.url().host()].items() for
		res_type, action in types.items()
	]
	cat = listcategory.ListCategory("Requests", entries)
	model.add_category(cat)
	return model

@cmdutils.register()
@cmdutils.argument("rule", completion=_get_rules_completion)
@cmdutils.argument("tab", value=cmdutils.Value.cur_tab)
def jmatrix_toggle_rule(tab: apitypes.Tab, rule: str):
	"""View request types made on this host and block/allow them.

	Requests are collated based on the host of the URL, so you may see requests from other pages on the same host.

	"""
	try:
		action, res_type, dest = rule.split()
	except ValueError:
		raise cmdutils.CommandError(
			"Expected input of the form \"block/allow request_type "
			"destination_host\""
		)
	if action.upper() == "BLOCK":
		action = jmatrix.rule.Action.ALLOW
	else:
		action = jmatrix.rule.Action.BLOCK
	if res_type == '*':
		res_type = "ALL"
	try:
		res_type = jmatrix.rule.Type[res_type.upper()]
	except KeyError:
		message.error("Type '{}' not recognized".format(res_type))
	origin = tab.url().host()
	JMATRIX_RULES.matrix_rules[origin][dest][res_type] = action
	# Change our seen requests to match so it'll show up in the completion
	# without having to reload the page.
	SEEN_REQUESTS.matrix_rules[origin][dest][res_type] = action
