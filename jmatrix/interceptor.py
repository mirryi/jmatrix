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


"""Functions to determine if a request should be blocked or not."""

import itertools


from jmatrix import rule

def _first_true(iterable, default=False, pred=None):
    """Returns the first true value in the iterable.

    If no true value is found, returns *default*

    If *pred* is not None, returns the first item
    for which pred(item) is true.

    """
    # first_true([a,b,c], x) --> a or b or c or x
    # first_true([a,b], x, f) --> a if f(a) else b if f(b) else x
    return next(filter(pred, iterable), default)


def _hostname_widen_list(hostname: str):
	"""An list generator which widens a hostname.

	eg: a.b.com -> b.com -> com
	"""
	l = []
	while hostname:
		l.append(hostname)
		hostname = hostname.partition(".")[-1]
	l.append('*')
	return l


def should_block(
		context_hostname: str, context_scheme: str, request_hostname: str,
		request_type: rule.Type, rules: rule.Rules) -> bool:
	widened_context = _hostname_widen_list(context_hostname)
	widened_request = _hostname_widen_list(request_hostname)
	# First check if we have a matrix-off rule
	context_scheme += "-scheme"
	if (any(map(
			lambda host: rules.matrix_off_rules.get(host, False),
			itertools.chain(widened_context, [context_scheme])))):
		# We should be off for this context
		return False

	# Begin checking actual matrix rules. Precedence looks like:
	# contextHostname -> destHostname -> type
	#
	# HOWEVER: Blacklists take precedence, ie: * * frame block won't allow for any whitelisting on any non-cell rule.

	# Block if no action
	action = True
	for w_c in widened_context:
		context_rules = rules.matrix_rules.get(w_c)
		if not context_rules:
			continue
		# TODO FIXME handle first-party
		for h_c in widened_request:
			hostname_rules = context_rules.get(h_c)
			if not hostname_rules:
				continue
			# types don't have any cascading, just check our type and *
			for t_c in [request_type, rule.Type.ALL]:
				final_rule = hostname_rules.get(t_c)
				if not final_rule:
					continue
				# If we get block/accept, we're done. If we get inherit, we have to continue.
				if final_rule == rule.Action.BLOCK:
					return True
				elif final_rule == rule.Action.ALLOW:
					action = False
					# We want to allow this request, but if there's a more general rule on a higher precedence,
					#
					# However, '* * type' seems to override all non-exact rules (?!?) instead of following normal
					# precedence.
					break

	# No rules, block
	return action
