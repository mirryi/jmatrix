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

import typing

from jmatrix import rule

class JMatrixParserError(ValueError):
	pass

def _rule_converter(r: str, rules: rule.Rules):
	split_rules = r.split()
	if 4 < len(split_rules) < 2:
		raise JMatrixParserError("Incorrect number of rules to {}.".format(r))
	if len(split_rules) < 3:
		split_rules.append('*')
	if len(split_rules) < 4:
		split_rules.append('allow')
	source_hostname, dest_hostname, rq_type, action = split_rules
	action_mapping = rule.Action.__members__
	action = action.upper()
	if action in action_mapping:
		action_value = action_mapping[action]
	else:
		raise JMatrixParserError("Incorrect action values to {}.".format(r))
	rq_type = rq_type.upper()
	if rq_type == '*':
		rq_type = "ALL"
	type_mapping = rule.Type.__members__
	if rq_type in type_mapping:
		request_type = type_mapping[rq_type]
	else:
		raise JMatrixParserError("Incorrect request type value to {}.".format(r))
	rules.matrix_rules[source_hostname][dest_hostname][request_type] = action_value

def _matrix_off_converter(r: str, rules: rule.Rules):
	split_rules = r.split()
	if len(split_rules) != 2:
		raise JMatrixParserError("Incorrect number of rules to {}.".format(r))
	source_hostname, state = split_rules
	state_mapping = rule.State.__members__
	state = state.upper()
	if state in state_mapping:
		state_val = state_mapping[state]
	else:
		raise JMatrixParserError("Incorrect boolean values to {}.".format(r))
	rules.matrix_off_rules[source_hostname] = state_val


# A mapping from uMatrix rule directives to converter functions
RULE_TO_CONVERTER = {
	"rule": _rule_converter,
	"matrix-off": _matrix_off_converter,
}


def rules_to_map(rule_lines: typing.List[str], rules: rule.Rules):
	"""Convert uMatrix rules into jblock lists."""
	for r in rule_lines:
		r_list = r.split(":", 1)
		if len(r_list) > 1:
			directive = r_list[0]
			line = r_list[1]
		else:
			directive = "rule"
			line = r
		directive = directive.lower().strip()
		line = line.strip()
		if directive not in RULE_TO_CONVERTER:
			print("[jmatrix]: rule '{}' ignored!".format(directive))
		else:
			RULE_TO_CONVERTER[directive](line.strip(), rules)
