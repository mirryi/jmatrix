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

def _rule_converter(d: str, r: str, rules: rule.Rules) -> None:
	split_rules = r.split()
	if not (2 <= len(split_rules) <= 4):
		raise JMatrixParserError("Incorrect number of rules to: {}.".format(r))
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
	# https://github.com/gorhill/uMatrix/issues/759
	elif rq_type == 'PLUGIN':
		rq_type = 'MEDIA'
	type_mapping = rule.Type.__members__
	if rq_type in type_mapping:
		request_type = type_mapping[rq_type]
	else:
		raise JMatrixParserError("Incorrect request type value to {}.".format(r))
	rules.matrix_rules[source_hostname][dest_hostname][request_type] = action_value

def _matrix_off_converter(d: str, r: str, rules: rule.Rules) -> None:
	split_rules = r.split()
	if len(split_rules) != 2:
		raise JMatrixParserError("Incorrect number of rules to {}.".format(r))
	source_hostname, state = split_rules
	state_mapping = rule.Flag.__members__
	state = state.upper()
	if state in state_mapping:
		state_val = state_mapping[state]
	else:
		raise JMatrixParserError("Incorrect boolean values to {}.".format(r))
	rules.matrix_flags[source_hostname].add(state_val)

def _matrix_flag_converter(d: str, r: str, rules: rule.Rules) -> None:
	split_rules = r.split()
	if len(split_rules) != 2:
		raise JMatrixParserError("Incorrect number of rules to {}.".format(r))
	source_hostname, state = split_rules
	state_mapping = rule.Flag.__members__
	directive = d.upper().replace("-", "_")
	if directive in state_mapping:
		flag_val = state_mapping[directive]
	else:
		raise JMatrixParserError("Incorrect boolean values to {}.".format(r))
	rules.matrix_flags[source_hostname].add(flag_val)


# A mapping from uMatrix rule directives to converter functions
RULE_TO_CONVERTER = {
	"rule": _rule_converter,
	"matrix-off": _matrix_off_converter,
	"https-strict": _matrix_flag_converter,
}


def rules_to_map(rule_lines: typing.Iterable[str], rules: rule.Rules) -> None:
	"""Convert uMatrix rules into jmatrix lists."""
	for r in rule_lines:
		# Remove comments
		r = r.split('#', 1)[0].strip()
		if not r:
			continue
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
			RULE_TO_CONVERTER[directive](directive, line.strip(), rules)
