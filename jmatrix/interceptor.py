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
import typing
import re

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

IP_ADDR_NAIVE = re.compile(r'^\d+\.\d+\.\d+\.\d+$|^\[[\da-zA-Z:]+\]$')
# TODO should we cache this?
def _get_first_party_domain(host: str) -> str:
	"""Get the part of a url to compare 'first party' domains."""
	# TODO we should probably use the public suffix list here, instead of assuming TLD is 1 block
	if not IP_ADDR_NAIVE.search(host):
		return ".".join(host.rsplit('.', 2)[-2:])
	return host

def _evaluate_cell_z(
		src_hostname: typing.List[str], request_hostname: str,
		request_type: rule.Type, rules: rule.Rules) -> typing.Optional[rule.Action]:
	for hostname in src_hostname:
		r1 = rules.matrix_rules.get(hostname, None)
		if r1 is None:
			continue
		r2 = r1.get(request_hostname, None)
		if r2 is None:
			continue
		r3 = r2.get(request_type, None)
		if r3 is not None:
			return r3
	return None

def should_block(
		context_hostname: str, context_scheme: str,
		request_hostname: str, request_scheme: str,
		request_type: rule.Type, rules: rule.Rules) -> bool:
	"""Check if we should block a certain url."""
	widened_context = _hostname_widen_list(context_hostname)
	widened_request = _hostname_widen_list(request_hostname)
	# First check if we have a matrix-off rule
	context_scheme += "-scheme"
	if (any(map(
			lambda host: rules.matrix_off_rules.get(host, False),
			itertools.chain(widened_context, [context_scheme])))):
		# We should be off for this context
		return False

	# uMatrix dosen't have any simple rules to it's precedence. Because of this, we just follow the algorithm defined in:
	#
	# https://github.com/gorhill/uMatrix/blob/054935d025c32f62b8dc35a27fbf7fa07d9f9589/src/js/matrix.js#L416

	# Exact hostname, exact type
	r = _evaluate_cell_z(widened_context, request_hostname, request_type, rules)
	if r == rule.Action.ALLOW: return False
	elif r == rule.Action.BLOCK: return True

	# Exact hostname, any type
	r_override = _evaluate_cell_z(widened_context, request_hostname, rule.Type.ALL, rules)
	if r == rule.Action.BLOCK: return True

	dest = request_hostname
	first_party_domain = _get_first_party_domain(request_hostname)
	if (_get_first_party_domain(context_hostname) != first_party_domain):
		first_party_domain = ""

	# Ancestor cells up to 1st-party request domain
	if first_party_domain:
		for domain in widened_request:
			dest = domain
			if domain == first_party_domain:
				break
			r = _evaluate_cell_z(widened_context, domain, request_type, rules)
			if r == rule.Action.ALLOW: return False
			elif r == rule.Action.BLOCK: return True

			# Don't override a more specific allow rule (??)
			if r_override != rule.Action.ALLOW:
				r_override = _evaluate_cell_z(widened_context, domain, rule.Type.ALL, rules)
				if r_override == rule.Action.BLOCK: return True

		# First party special case cell
		r = _evaluate_cell_z(widened_context, '1st-party', request_type, rules)
		if r == rule.Action.ALLOW: return False
		elif r == rule.Action.BLOCK: return True

		# Don't override a more specific allow rule (??)
		if r_override != rule.Action.ALLOW:
			r_override = _evaluate_cell_z(widened_context, '1st-party', rule.Type.ALL, rules)
			if r_override == rule.Action.BLOCK: return True
		search_domains = _hostname_widen_list(dest)
	else:
		search_domains = widened_request

	# Go up to root
	for domain in search_domains:
		if domain == '*':
			break
		r = _evaluate_cell_z(widened_context, domain, request_type, rules)
		if r == rule.Action.ALLOW: return False
		elif r == rule.Action.BLOCK: return True

		# Don't override a more specific allow rule (??)
		if r_override != rule.Action.ALLOW:
			r_override = _evaluate_cell_z(widened_context, domain, rule.Type.ALL, rules)
			if r_override == rule.Action.BLOCK: return True

	# Hostname specific type cells
	r = _evaluate_cell_z(widened_context, '*', request_type, rules)
	if r == rule.Action.BLOCK: return True
	if r_override == rule.Action.ALLOW: return False
	if r == rule.Action.ALLOW: return False

	# Hostname type api call
	r = _evaluate_cell_z(widened_context, '*', rule.Type.ALL, rules)
	if r == rule.Action.BLOCK: return True
	if r == rule.Action.ALLOW: return False

	# No rules, block
	return True
